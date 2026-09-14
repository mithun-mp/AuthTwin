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
    session = Session(id=str(uuid.uuid4()), target_id=target.id, identity_id=identity.id, name="Test Topology Session")

    db_session.add_all([target, identity, session])
    db_session.commit()

    yield db_session
    db_session.close()


def test_one_to_one_topology(db):
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    t1 = Transaction(id="tx-1", session_id=session.id, timestamp=now, method="POST", url="http://localhost/projects", path="/projects", res_status=201, res_body='{"id": 101}')
    t2 = Transaction(id="tx-2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/projects/101", path="/projects/101", res_status=200)

    db.add_all([t1, t2])
    dep = Dependency(id="dep-1", producer_transaction_id="tx-1", consumer_transaction_id="tx-2", producer_field_path="response.body.id", consumer_field_location="PATH", consumer_field_name="id", extracted_value="101", dependency_type="RESPONSE_TO_PATH", confidence=1.0)
    db.add(dep)
    db.commit()

    nodes, edges = build_canonical_graph("wf-1", [t1, t2], [dep])
    assert len(nodes) == 2
    assert len(edges) == 1
    assert edges[0].edge_type == "DEPENDENCY_TRANSITION"
    assert edges[0].step_distance == 1


def test_one_to_n_branching(db):
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    t0 = Transaction(id="tx-0", session_id=session.id, timestamp=now, method="POST", url="http://localhost/projects", path="/projects", res_status=201)
    t1 = Transaction(id="tx-1", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/projects/101", path="/projects/101", res_status=200)
    t2 = Transaction(id="tx-2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=4), method="GET", url="http://localhost/documents/101", path="/documents/101", res_status=200)
    t3 = Transaction(id="tx-3", session_id=session.id, timestamp=now + datetime.timedelta(seconds=6), method="GET", url="http://localhost/users/101", path="/users/101", res_status=200)

    db.add_all([t0, t1, t2, t3])

    dep1 = Dependency(id="d1", producer_transaction_id="tx-0", consumer_transaction_id="tx-1", producer_field_path="res.id", consumer_field_location="PATH", consumer_field_name="id", extracted_value="101", dependency_type="RESPONSE_TO_PATH", confidence=1.0)
    dep2 = Dependency(id="d2", producer_transaction_id="tx-0", consumer_transaction_id="tx-2", producer_field_path="res.id", consumer_field_location="PATH", consumer_field_name="id", extracted_value="101", dependency_type="RESPONSE_TO_PATH", confidence=1.0)
    dep3 = Dependency(id="d3", producer_transaction_id="tx-0", consumer_transaction_id="tx-3", producer_field_path="res.id", consumer_field_location="PATH", consumer_field_name="id", extracted_value="101", dependency_type="RESPONSE_TO_PATH", confidence=1.0)
    db.add_all([dep1, dep2, dep3])
    db.commit()

    nodes, edges = build_canonical_graph("wf-branch", [t0, t1, t2, t3], [dep1, dep2, dep3])
    root_node = next(n for n in nodes if n.method == "POST")
    assert root_node.out_degree == 3

    branch_edges = [e for e in edges if e.source == root_node.id]
    assert len(branch_edges) == 3
    for e in branch_edges:
        assert "BRANCH" in e.types or e.edge_type == "DEPENDENCY_TRANSITION"


def test_n_to_one_merging(db):
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    t1 = Transaction(id="tx-p1", session_id=session.id, timestamp=now, method="GET", url="http://localhost/projects/101", path="/projects/101", res_status=200)
    t2 = Transaction(id="tx-p2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/documents/101", path="/documents/101", res_status=200)
    t3 = Transaction(id="tx-p3", session_id=session.id, timestamp=now + datetime.timedelta(seconds=4), method="GET", url="http://localhost/users/101", path="/users/101", res_status=200)
    t4 = Transaction(id="tx-m", session_id=session.id, timestamp=now + datetime.timedelta(seconds=6), method="GET", url="http://localhost/dashboard", path="/dashboard", res_status=200)

    db.add_all([t1, t2, t3, t4])
    db.commit()

    nodes, edges = build_canonical_graph("wf-merge", [t1, t2, t3, t4], [])
    target_node = next(n for n in nodes if n.actual_path == "/dashboard")
    assert target_node.in_degree >= 1


def test_non_consecutive_dependency(db):
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    txs = [
        Transaction(id="tx-0", session_id=session.id, timestamp=now, method="POST", url="http://localhost/projects", path="/projects", res_status=201, res_body='{"id": 101}'),
        Transaction(id="tx-1", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/users", path="/users", res_status=200),
        Transaction(id="tx-2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=4), method="GET", url="http://localhost/settings", path="/settings", res_status=200),
        Transaction(id="tx-3", session_id=session.id, timestamp=now + datetime.timedelta(seconds=6), method="GET", url="http://localhost/projects/101", path="/projects/101", res_status=200)
    ]
    db.add_all(txs)

    non_consec_dep = Dependency(
        id="dep-non-consec",
        producer_transaction_id="tx-0",
        consumer_transaction_id="tx-3",
        producer_field_path="response.body.id",
        consumer_field_location="PATH",
        consumer_field_name="id",
        extracted_value="101",
        dependency_type="RESPONSE_TO_PATH",
        confidence=1.0
    )
    db.add(non_consec_dep)
    db.commit()

    nodes, edges = build_canonical_graph("wf-non-consec", txs, [non_consec_dep])
    dep_edge = next(e for e in edges if e.dependency_id == "dep-non-consec")
    assert dep_edge.step_distance == 3
    assert dep_edge.edge_type == "DEPENDENCY_TRANSITION"


def test_repeated_operation_aggregation(db):
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    txs = [
        Transaction(id="t-1", session_id=session.id, timestamp=now, method="GET", url="http://localhost/projects/101", path="/projects/101", res_status=200),
        Transaction(id="t-2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/projects/102", path="/projects/102", res_status=200),
        Transaction(id="t-3", session_id=session.id, timestamp=now + datetime.timedelta(seconds=4), method="GET", url="http://localhost/projects/103", path="/projects/103", res_status=200)
    ]
    db.add_all(txs)
    db.commit()

    # 1. Canonical Graph collapses repeated route templates (/projects/{id}) into 1 logical node
    c_nodes, c_edges = build_canonical_graph("wf-rep", txs, [])
    assert len(c_nodes) == 1
    assert len(c_nodes[0].occurrences) == 3

    # 2. Linear Workflow keeps 3 distinct steps
    linear_wf = build_linear_workflow("wf-rep", session, txs, [])
    assert len(linear_wf.steps) == 3
    assert [s.step_index for s in linear_wf.steps] == [0, 1, 2]


def test_graph_determinism_and_validation(db):
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    txs = [
        Transaction(id="tx-a", session_id=session.id, timestamp=now, method="POST", url="http://localhost/items", path="/items", res_status=201),
        Transaction(id="tx-b", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/items/55", path="/items/55", res_status=200)
    ]
    db.add_all(txs)
    db.commit()

    nodes1, edges1 = build_canonical_graph("wf-det", txs, [])
    nodes2, edges2 = build_canonical_graph("wf-det", txs, [])

    # Exact same IDs across runs
    assert [n.id for n in nodes1] == [n.id for n in nodes2]
    assert [e.id for e in edges1] == [e.id for e in edges2]

    # Validate graph passes integrity checks
    validate_canonical_graph(nodes1, edges1)
