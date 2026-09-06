import pytest
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Target, Identity, Session, Transaction, Workflow
from app.workflows.wsg_generator import generate_workflow_state_graph

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
