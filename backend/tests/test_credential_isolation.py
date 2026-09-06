import pytest
import uuid
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.models import Target, Identity, Session, Transaction, Workflow, ShadowWorkflow
from app.workflows.wsg_generator import generate_workflow_state_graph
from app.shadow.cloner import clone_shadow_workflow

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db_session = SessionLocal()
    
    target = Target(id=str(uuid.uuid4()), name="Test Target", base_url="http://localhost")
    alice = Identity(id=str(uuid.uuid4()), target_id=target.id, name="Alice", role="Primary")
    bob = Identity(id=str(uuid.uuid4()), target_id=target.id, name="Bob", role="Alternate")
    session = Session(id=str(uuid.uuid4()), target_id=target.id, identity_id=alice.id, name="Alice Session")
    
    db_session.add_all([target, alice, bob, session])
    db_session.commit()
    
    yield db_session
    db_session.close()

def test_credential_isolation_invariant(db):
    alice = db.query(Identity).filter(Identity.name == "Alice").first()
    bob = db.query(Identity).filter(Identity.name == "Bob").first()
    session = db.query(Session).first()

    secret_token_alice = "Bearer SECRET_ALICE_JWT_TOKEN_ABC123987"
    
    t1 = Transaction(
        id=str(uuid.uuid4()),
        session_id=session.id,
        timestamp=datetime.datetime.utcnow(),
        method="POST",
        url="http://localhost/projects",
        path="/projects",
        req_headers={"Authorization": "Bearer [REDACTED]", "Cookie": "session=secret_alice_cookie"},
        res_status=201
    )
    db.add(t1)
    db.commit()

    wf = generate_workflow_state_graph(db, session.id)
    shadow_wf = clone_shadow_workflow(db, wf.id, bob.id)

    # Verify Shadow Workflow record does NOT store Alice's credentials anywhere
    assert shadow_wf.shadow_identity_id == bob.id
    assert shadow_wf.shadow_identity_id != alice.id

    # Verify database model for ShadowWorkflow contains no secret headers or token attributes
    assert not hasattr(shadow_wf, "authorization_token")
    assert not hasattr(shadow_wf, "cookie")
    assert shadow_wf.clone_policy == "CREDENTIAL_ISOLATED"
    assert shadow_wf.status == "MODEL_ONLY"

    # Assert secret string is nowhere in shadow workflow representation
    shadow_str = str(shadow_wf.__dict__)
    assert secret_token_alice not in shadow_str
    assert "secret_alice_cookie" not in shadow_str
