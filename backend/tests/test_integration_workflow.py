import pytest
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Target, Identity, Session, Transaction, Workflow, ShadowWorkflow
from app.dependencies.analyzer import analyze_session_dependencies
from app.workflows.wsg_generator import generate_workflow_state_graph
from app.shadow.cloner import clone_shadow_workflow

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    target = Target(id=str(uuid.uuid4()), name="Reference API Target", base_url="http://127.0.0.1:8090")
    alice = Identity(id=str(uuid.uuid4()), target_id=target.id, name="Alice", role="Primary")
    bob = Identity(id=str(uuid.uuid4()), target_id=target.id, name="Bob", role="Alternate")
    session = Session(id=str(uuid.uuid4()), target_id=target.id, identity_id=alice.id, name="Alice Reference Workflow")
    
    db_session.add_all([target, alice, bob, session])
    db_session.commit()
    
    yield db_session
    db_session.close()

def test_complete_end_to_end_m1_workflow(db):
    alice = db.query(Identity).filter(Identity.name == "Alice").first()
    bob = db.query(Identity).filter(Identity.name == "Bob").first()
    session = db.query(Session).first()

    now = datetime.datetime.utcnow()

    # Step 1: POST /login
    t1 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=now,
        method="POST",
        url="http://127.0.0.1:8090/login",
        path="/login",
        req_headers={"Content-Type": "application/json"},
        req_body='{"username": "alice", "password": "password123"}',
        res_status=200,
        res_headers={"Content-Type": "application/json"},
        res_body='{"token": "bearer_alice_123"}'
    )

    # Step 2: POST /projects -> returns {"id": 101}
    t2 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=now + datetime.timedelta(seconds=2),
        method="POST",
        url="http://127.0.0.1:8090/projects",
        path="/projects",
        req_headers={"Authorization": "Bearer [REDACTED]"},
        req_body='{"name": "Project Alpha"}',
        res_status=201,
        res_headers={"Content-Type": "application/json"},
        res_body='{"id": 101, "name": "Project Alpha", "owner": "alice"}'
    )

    # Step 3: GET /projects/101
    t3 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=now + datetime.timedelta(seconds=4),
        method="GET",
        url="http://127.0.0.1:8090/projects/101",
        path="/projects/101",
        req_headers={"Authorization": "Bearer [REDACTED]"},
        req_body="",
        res_status=200,
        res_headers={"Content-Type": "application/json"},
        res_body='{"id": 101, "name": "Project Alpha", "owner": "alice"}'
    )

    # Step 4: POST /projects/101/documents -> returns {"id": 501}
    t4 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=now + datetime.timedelta(seconds=6),
        method="POST",
        url="http://127.0.0.1:8090/projects/101/documents",
        path="/projects/101/documents",
        req_headers={"Authorization": "Bearer [REDACTED]"},
        req_body='{"title": "Architecture Doc"}',
        res_status=201,
        res_headers={"Content-Type": "application/json"},
        res_body='{"id": 501, "title": "Architecture Doc", "project_id": 101}'
    )

    # Step 5: GET /documents/501
    t5 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=now + datetime.timedelta(seconds=8),
        method="GET",
        url="http://127.0.0.1:8090/documents/501",
        path="/documents/501",
        req_headers={"Authorization": "Bearer [REDACTED]"},
        req_body="",
        res_status=200,
        res_headers={"Content-Type": "application/json"},
        res_body='{"id": 501, "title": "Architecture Doc", "project_id": 101}'
    )

    db.add_all([t1, t2, t3, t4, t5])
    db.commit()

    # 1. Dependency Analysis
    deps = analyze_session_dependencies(db, session.id)
    assert len(deps) >= 2 # Should link 101 -> GET /projects/101 and 501 -> GET /documents/501

    # 2. Workflow State Graph Generation
    wf = generate_workflow_state_graph(db, session.id)
    assert wf.node_count == 5
    assert wf.edge_count >= 4

    # 3. Shadow Workflow Duplication (Bob)
    shadow_wf = clone_shadow_workflow(db, wf.id, bob.id)
    assert shadow_wf.source_workflow_id == wf.id
    assert shadow_wf.source_identity_id == alice.id
    assert shadow_wf.shadow_identity_id == bob.id
    assert shadow_wf.status == "MODEL_ONLY"
