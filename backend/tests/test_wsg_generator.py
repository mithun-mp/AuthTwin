import pytest
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.database import Base
from app.models.models import Target, Identity, Session, Transaction, Dependency, Workflow
from app.services.workflow_service import (
    generate_workflow_state_graph, get_workflow_graph_details,
    build_linear_workflow, build_canonical_graph
)

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    target = Target(id=str(uuid.uuid4()), name="Test Target", base_url="http://localhost")
    identity = Identity(id=str(uuid.uuid4()), target_id=target.id, name="Alice", role="Primary")
    session = Session(id=str(uuid.uuid4()), target_id=target.id, identity_id=identity.id, name="Test Session")
    
    db_session.add_all([target, identity, session])
    db_session.commit()
    
    yield db_session
    db_session.close()

def test_generate_workflow_state_graph(db):
    session = db.query(Session).first()

    t1 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=datetime.datetime.utcnow(),
        method="POST",
        url="http://localhost/projects",
        path="/projects",
        res_status=201
    )
    t2 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=datetime.datetime.utcnow() + datetime.timedelta(seconds=5),
        method="GET",
        url="http://localhost/projects/101",
        path="/projects/101",
        res_status=200
    )

    db.add_all([t1, t2])
    db.commit()

    wf = generate_workflow_state_graph(db, session.id)
    assert wf.node_count == 2
    assert wf.edge_count == 1
    assert len(wf.nodes) == 2
    assert len(wf.edges) == 1

def test_linear_and_canonical_dual_representation(db):
    session = db.query(Session).first()

    # User's exact scenario:
    # 0: POST /projects (201 -> id:101)
    # 1: GET /projects/101 (200)
    # 2: GET /projects/101 (200)
    # 3: GET /documents/101 (200)
    # 4: POST /documents (201)
    # 5: GET /documents (200)
    now = datetime.datetime.utcnow()
    txs = [
        Transaction(id="tx-0", session_id=session.id, timestamp=now, method="POST", url="http://localhost/projects", path="/projects", res_status=201, res_body='{"id": 101}'),
        Transaction(id="tx-1", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/projects/101", path="/projects/101", res_status=200, res_body='{"id": 101}'),
        Transaction(id="tx-2", session_id=session.id, timestamp=now + datetime.timedelta(seconds=4), method="GET", url="http://localhost/projects/101", path="/projects/101", res_status=200, res_body='{"id": 101}'),
        Transaction(id="tx-3", session_id=session.id, timestamp=now + datetime.timedelta(seconds=6), method="GET", url="http://localhost/documents/101", path="/documents/101", res_status=200, res_body='{"id": 501}'),
        Transaction(id="tx-4", session_id=session.id, timestamp=now + datetime.timedelta(seconds=8), method="POST", url="http://localhost/documents", path="/documents", res_status=201, res_body='{"id": 502}'),
        Transaction(id="tx-5", session_id=session.id, timestamp=now + datetime.timedelta(seconds=10), method="GET", url="http://localhost/documents", path="/documents", res_status=200, res_body='[{"id": 502}]')
    ]
    db.add_all(txs)

    dep1 = Dependency(id="dep-1", producer_transaction_id="tx-0", consumer_transaction_id="tx-1", producer_field_path="response.body.id", consumer_field_location="PATH", consumer_field_name="path_segment_1", extracted_value="101", dependency_type="RESPONSE_TO_PATH", confidence=1.0)
    dep2 = Dependency(id="dep-2", producer_transaction_id="tx-0", consumer_transaction_id="tx-2", producer_field_path="response.body.id", consumer_field_location="PATH", consumer_field_name="path_segment_1", extracted_value="101", dependency_type="RESPONSE_TO_PATH", confidence=1.0)
    db.add_all([dep1, dep2])
    db.commit()

    wf = generate_workflow_state_graph(db, session.id)
    graph_details = get_workflow_graph_details(db, wf.id)

    # 1. Verify Linear Workflow representation
    linear = graph_details.linear_workflow
    assert len(linear.steps) == 6
    assert [s.step_index for s in linear.steps] == [0, 1, 2, 3, 4, 5]
    assert linear.steps[1].transaction_id == "tx-1"
    assert linear.steps[2].transaction_id == "tx-2"
    # Occurrence IDs remain distinct
    assert linear.steps[1].occurrence_id != linear.steps[2].occurrence_id

    # 2. Verify Canonical Hybrid Graph representation
    c_nodes = graph_details.canonical_nodes
    c_edges = graph_details.canonical_edges
    assert len(c_nodes) > 0
    
    # Locate GET /projects/101 logical node and verify it tracks 2 occurrences
    proj_get_node = next((n for n in c_nodes if n.actual_path == "/projects/101"), None)
    assert proj_get_node is not None
    assert len(proj_get_node.occurrences) == 2

def test_graph_determinism(db):
    session = db.query(Session).first()
    now = datetime.datetime.utcnow()

    txs = [
        Transaction(id="tx-a", session_id=session.id, timestamp=now, method="POST", url="http://localhost/login", path="/login", res_status=200),
        Transaction(id="tx-b", session_id=session.id, timestamp=now + datetime.timedelta(seconds=2), method="GET", url="http://localhost/items", path="/items", res_status=200)
    ]
    db.add_all(txs)
    db.commit()

    wf1 = generate_workflow_state_graph(db, session.id)
    g1 = get_workflow_graph_details(db, wf1.id)

    wf2 = generate_workflow_state_graph(db, session.id)
    g2 = get_workflow_graph_details(db, wf2.id)

    # Topological structure must be 100% deterministic across runs
    assert [n.id for n in g1.canonical_nodes] == [n.id for n in g2.canonical_nodes]
    assert [e.id for e in g1.canonical_edges] == [e.id for e in g2.canonical_edges]
