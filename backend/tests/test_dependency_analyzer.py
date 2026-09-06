import pytest
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Target, Identity, Session, Transaction, Dependency
from app.dependencies.analyzer import analyze_session_dependencies

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

def test_analyze_session_dependencies(db):
    session = db.query(Session).first()

    # T1: Producer (POST /projects -> returns {"id": 101})
    t1 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=datetime.datetime.utcnow(),
        method="POST",
        url="http://localhost/projects",
        path="/projects",
        query_params={},
        req_headers={},
        req_body='{"name": "Project Alpha"}',
        res_status=201,
        res_headers={},
        res_body='{"id": 101, "name": "Project Alpha"}'
    )

    # T2: Consumer (GET /projects/101 -> path consumes 101)
    t2 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=datetime.datetime.utcnow() + datetime.timedelta(seconds=5),
        method="GET",
        url="http://localhost/projects/101",
        path="/projects/101",
        query_params={},
        req_headers={},
        req_body="",
        res_status=200,
        res_headers={},
        res_body='{"id": 101, "name": "Project Alpha"}'
    )

    db.add_all([t1, t2])
    db.commit()

    deps = analyze_session_dependencies(db, session.id)
    assert len(deps) >= 1

    dep = deps[0]
    assert dep.producer_transaction_id == t1.id
    assert dep.consumer_transaction_id == t2.id
    assert dep.extracted_value == "101"
    assert dep.dependency_type == "RESPONSE_TO_PATH"

def test_false_positive_dependency_filtering(db):
    session = db.query(Session).first()

    # T1 returns total_count=101
    t1 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=datetime.datetime.utcnow(),
        method="GET",
        url="http://localhost/items",
        path="/items",
        query_params={},
        req_headers={},
        req_body="",
        res_status=200,
        res_headers={},
        res_body='{"items": [], "total_count": 101}'
    )

    # T2 uses query param ?page=101
    t2 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=datetime.datetime.utcnow() + datetime.timedelta(seconds=5),
        method="GET",
        url="http://localhost/other?page=101",
        path="/other",
        query_params={"page": "101"},
        req_headers={},
        req_body="",
        res_status=200,
        res_headers={},
        res_body='{"items": []}'
    )

    db.add_all([t1, t2])
    db.commit()

    deps = analyze_session_dependencies(db, session.id)
    # Assert low-confidence coincidental pagination dependency is filtered out (confidence < 0.5)
    assert len(deps) == 0
