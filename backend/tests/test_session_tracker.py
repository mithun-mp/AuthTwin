import pytest
import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Target, Identity, Session, Transaction
from app.identity.session_tracker import process_and_group_session, get_token_fingerprint

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    target = Target(id=str(uuid.uuid4()), name="Test Target", base_url="http://localhost")
    db_session.add(target)
    db_session.commit()
    
    identity = Identity(id=str(uuid.uuid4()), target_id=target.id, name="Test User", role="Primary")
    db_session.add(identity)
    db_session.commit()
    
    yield db_session
    db_session.close()


def test_token_fingerprint():
    headers = {"Authorization": "Bearer token123"}
    fp = get_token_fingerprint(headers)
    assert fp is not None
    assert len(fp) == 16

def test_process_and_group_session(db):
    target = db.query(Target).first()
    raw_txs = [
        {
            "id": str(uuid.uuid4()),
            "timestamp": "2026-09-04T10:00:00Z",
            "method": "POST",
            "url": "http://localhost/projects",
            "path": "/projects",
            "query_params": {},
            "req_headers": {"Authorization": "Bearer [REDACTED]"},
            "raw_req_headers": {"Authorization": "Bearer secret_token"},
            "req_body": '{"name": "Alpha"}',
            "res_status": 201,
            "res_headers": {},
            "res_body": '{"id": 101}',
            "operation_id": "createProject"
        }
    ]

    session_obj, db_txs = process_and_group_session(db, target.id, raw_txs)
    assert session_obj.target_id == target.id
    assert len(db_txs) == 1
    assert db_txs[0].req_headers["Authorization"] == "Bearer [REDACTED]"
