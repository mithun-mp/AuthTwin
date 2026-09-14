import pytest
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import Target, Identity, Session, Transaction, Dependency, Workflow
from app.services.workflow_service import (
    generate_workflow_state_graph,
    get_workflow_graph_details,
    build_canonical_graph,
    build_linear_workflow,
    validate_canonical_graph
)

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()

    target = Target(id=str(uuid.uuid4()), name="Test Target", base_url="http://localhost")
    identity = Identity(id=str(uuid.uuid4()), target_id=target.id, name="Alice", role="Primary")
    session = Session(id=str(uuid.uuid4()), target_id=target.id, identity_id=identity.id, name="Test Canonical Graph Session")

    db_session.add_all([target, identity, session])
    db_session.commit()

    yield db_session
    db_session.close()


def test_canonical_graph_one_to_one(db):
    """Test 1->1 topology with exact edge bindings and evidence."""
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    t1 = Transaction(id="tx-101", session_id=session.id, timestamp=now, method="POST", url="http://localhost/api/v1/auth/login", path="/api/v1/auth/login", res_status=200, res_body='{"token": "xyz123"}')
    t2 = Transaction(id="tx-102", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/api/v1/user/profile", path="/api/v1/user/profile", res_status=200, req_headers='{"Authorization": "Bearer xyz123"}')

    db.add_all([t1, t2])
    dep = Dependency(
        id="dep-101",
        producer_transaction_id="tx-101",
        consumer_transaction_id="tx-102",
        producer_field_path="response.body.token",
        consumer_field_location="HEADER",
        consumer_field_name="Authorization",
        extracted_value="xyz123",
        dependency_type="RESPONSE_TO_HEADER",
        confidence=1.0
    )
    db.add(dep)
    db.commit()

    nodes, edges = build_canonical_graph("wf-1to1", [t1, t2], [dep])
    assert len(nodes) == 2
    assert len(edges) == 1

    edge = edges[0]
    assert edge.edge_type == "DEPENDENCY_TRANSITION"
    assert edge.cardinality == "1->1"
    assert len(edge.bindings) == 1
    assert edge.bindings[0].producer_path == "response.body.token"
    assert edge.bindings[0].consumer_parameter == "Authorization"
    assert edge.bindings[0].extracted_value == "xyz123"
    assert edge.evidence.reason == "Parameter dependency payload binding"


def test_canonical_graph_one_to_n_branching(db):
    """Test 1->N branching topology where one node produces values for multiple downstream operations."""
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    t0 = Transaction(id="tx-login", session_id=session.id, timestamp=now, method="POST", url="http://localhost/api/v1/auth/login", path="/api/v1/auth/login", res_status=200, res_body='{"token": "tok999"}')
    t1 = Transaction(id="tx-dash", session_id=session.id, timestamp=now + datetime.timedelta(seconds=1), method="GET", url="http://localhost/api/v1/dashboard", path="/api/v1/dashboard", res_status=200)
    t2 = Transaction(id="tx-reports", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/api/v1/reports", path="/api/v1/reports", res_status=200)
    t3 = Transaction(id="tx-settings", session_id=session.id, timestamp=now + datetime.timedelta(seconds=3), method="GET", url="http://localhost/api/v1/settings", path="/api/v1/settings", res_status=200)

    db.add_all([t0, t1, t2, t3])

    dep1 = Dependency(id="d1", producer_transaction_id="tx-login", consumer_transaction_id="tx-dash", producer_field_path="res.token", consumer_field_location="HEADER", consumer_field_name="Auth", extracted_value="tok999", dependency_type="RESPONSE_TO_HEADER", confidence=1.0)
    dep2 = Dependency(id="d2", producer_transaction_id="tx-login", consumer_transaction_id="tx-reports", producer_field_path="res.token", consumer_field_location="HEADER", consumer_field_name="Auth", extracted_value="tok999", dependency_type="RESPONSE_TO_HEADER", confidence=1.0)
    dep3 = Dependency(id="d3", producer_transaction_id="tx-login", consumer_transaction_id="tx-settings", producer_field_path="res.token", consumer_field_location="HEADER", consumer_field_name="Auth", extracted_value="tok999", dependency_type="RESPONSE_TO_HEADER", confidence=1.0)

    db.add_all([dep1, dep2, dep3])
    db.commit()

    nodes, edges = build_canonical_graph("wf-1toN", [t0, t1, t2, t3], [dep1, dep2, dep3])
    login_node = next(n for n in nodes if n.actual_path == "/api/v1/auth/login")
    assert login_node.out_degree == 3

    branch_edges = [e for e in edges if e.source == login_node.id]
    assert len(branch_edges) == 3


def test_canonical_graph_n_to_one_merging(db):
    """Test N->1 merging topology where multiple nodes converge into a single state."""
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    t1 = Transaction(id="tx-p1", session_id=session.id, timestamp=now, method="GET", url="http://localhost/api/v1/products/1", path="/api/v1/products/1", res_status=200)
    t2 = Transaction(id="tx-p2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/api/v1/categories/5", path="/api/v1/categories/5", res_status=200)
    t3 = Transaction(id="tx-checkout", session_id=session.id, timestamp=now + datetime.timedelta(seconds=4), method="POST", url="http://localhost/api/v1/checkout", path="/api/v1/checkout", res_status=200)

    db.add_all([t1, t2, t3])
    db.commit()

    nodes, edges = build_canonical_graph("wf-Nto1", [t1, t2, t3], [])
    checkout_node = next(n for n in nodes if n.actual_path == "/api/v1/checkout")
    assert checkout_node.in_degree >= 1


def test_canonical_graph_non_consecutive_dependencies(db):
    """Test non-consecutive dependency transition (step_distance > 1)."""
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    txs = [
        Transaction(id="tx-0", session_id=session.id, timestamp=now, method="POST", url="http://localhost/api/v1/cart", path="/api/v1/cart", res_status=201, res_body='{"cart_id": "c-44"}'),
        Transaction(id="tx-1", session_id=session.id, timestamp=now + datetime.timedelta(seconds=1), method="GET", url="http://localhost/api/v1/user", path="/api/v1/user", res_status=200),
        Transaction(id="tx-2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/api/v1/help", path="/api/v1/help", res_status=200),
        Transaction(id="tx-3", session_id=session.id, timestamp=now + datetime.timedelta(seconds=3), method="POST", url="http://localhost/api/v1/checkout/c-44", path="/api/v1/checkout/c-44", res_status=200)
    ]
    db.add_all(txs)

    non_consec_dep = Dependency(
        id="dep-cart-checkout",
        producer_transaction_id="tx-0",
        consumer_transaction_id="tx-3",
        producer_field_path="response.body.cart_id",
        consumer_field_location="PATH",
        consumer_field_name="cart_id",
        extracted_value="c-44",
        dependency_type="RESPONSE_TO_PATH",
        confidence=1.0
    )
    db.add(non_consec_dep)
    db.commit()

    nodes, edges = build_canonical_graph("wf-nonconsec", txs, [non_consec_dep])
    dep_edge = next(e for e in edges if e.dependency_id == "dep-cart-checkout")
    assert dep_edge.step_distance == 3
    assert dep_edge.edge_type == "DEPENDENCY_TRANSITION"


def test_canonical_graph_repeated_occurrences(db):
    """Test repeated invocations of the same template produce 1 canonical node with all occurrence details preserved."""
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    txs = [
        Transaction(id="t-item-1", session_id=session.id, timestamp=now, method="GET", url="http://localhost/items/1", path="/items/1", res_status=200),
        Transaction(id="t-item-2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/items/2", path="/items/2", res_status=200),
        Transaction(id="t-item-3", session_id=session.id, timestamp=now + datetime.timedelta(seconds=4), method="GET", url="http://localhost/items/3", path="/items/3", res_status=200)
    ]
    db.add_all(txs)
    db.commit()

    c_nodes, c_edges = build_canonical_graph("wf-rep", txs, [])
    assert len(c_nodes) == 1
    item_node = c_nodes[0]
    assert len(item_node.occurrences) == 3
    assert [o.occurrence_index for o in item_node.occurrences] == [0, 1, 2]
    assert [o.transaction_id for o in item_node.occurrences] == ["t-item-1", "t-item-2", "t-item-3"]

    # Linear workflow preserves 3 distinct steps
    linear_wf = build_linear_workflow("wf-rep", session, txs, [])
    assert len(linear_wf.steps) == 3


def test_canonical_graph_determinism(db):
    """Test SHA-256 ID generation produces identical deterministic IDs across multiple runs."""
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    txs = [
        Transaction(id="tx-alpha", session_id=session.id, timestamp=now, method="POST", url="http://localhost/orders", path="/orders", res_status=201),
        Transaction(id="tx-beta", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/orders/88", path="/orders/88", res_status=200)
    ]
    db.add_all(txs)
    db.commit()

    nodes1, edges1 = build_canonical_graph("wf-det", txs, [])
    nodes2, edges2 = build_canonical_graph("wf-det", txs, [])

    assert [n.id for n in nodes1] == [n.id for n in nodes2]
    assert [e.id for e in edges1] == [e.id for e in edges2]

    # Run validation function
    validate_canonical_graph(nodes1, edges1)
