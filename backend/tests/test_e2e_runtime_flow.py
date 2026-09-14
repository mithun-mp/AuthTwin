import pytest
import uuid
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Target, Identity, Session as SessionModel, Transaction, Workflow, ShadowWorkflow
from app.api import interceptor as interceptor_api

# Setup isolated in-memory SQLite database for E2E flow testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

import app.models

@pytest.fixture(autouse=True)
def setup_db():
    Target.__table__.metadata.drop_all(bind=engine)
    Target.__table__.metadata.create_all(bind=engine)
    yield
    Target.__table__.metadata.drop_all(bind=engine)


class FakeTargetServerResponse:
    def __init__(self, content: bytes, content_type: str = "text/html", status_code: int = 200, headers: dict = None):
        self.content = content
        self.headers = headers or {"content-type": content_type, "server": "Reference Target API"}
        self.status_code = status_code
        self.text = content.decode("utf-8")


class FakeTargetAsyncClient:
    """Mock HTTPX client representing the external Target application server (http://127.0.0.1:8001)."""
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def get(self, url, **kwargs):
        if "8001" in url or "target.example" in url:
            return FakeTargetServerResponse(
                content=b"<html><head><title>Sample Target App</title></head><body><h1>Target Products</h1></body></html>",
                content_type="text/html"
            )
        raise Exception(f"Unreachable target url: {url}")

    async def request(self, method, url, **kwargs):
        if "/api/v1/products/17" in url:
            return FakeTargetServerResponse(
                content=b'{"id": 17, "name": "Security Audit Tool", "price": 99.0}',
                content_type="application/json"
            )
        elif "/api/v1/products" in url:
            return FakeTargetServerResponse(
                content=b'[{"id": 17, "name": "Security Audit Tool"}]',
                content_type="application/json"
            )
        elif "/api/v1/cart" in url:
            return FakeTargetServerResponse(
                content=b'{"cart_id": "c-901", "product_id": 17, "status": "active"}',
                content_type="application/json"
            )
        elif "/api/v1/orders" in url:
            return FakeTargetServerResponse(
                content=b'{"order_id": 501, "status": "created", "total": 99.0}',
                content_type="application/json"
            )
        elif "/login" in url or "/api/v1/login" in url:
            return FakeTargetServerResponse(
                content=b'{"token": "token-user-alice-123", "user": "Alice"}',
                content_type="application/json"
            )
        else:
            return FakeTargetServerResponse(
                content=b"<html><body><h1>Target Home</h1></body></html>",
                content_type="text/html"
            )


def test_complete_end_to_end_runtime_flow(monkeypatch):
    """
    Comprehensive E2E verification of the 32-step AuthTwin runtime flow:
    Target Probe -> Save Target -> Identity Creation -> Selection -> Proxy Capture ->
    DB Persistence -> Session Grouping -> Dependency Analysis -> WSG Generation -> Replay Shadow Clone.
    """
    monkeypatch.setattr(interceptor_api.httpx, "AsyncClient", FakeTargetAsyncClient)

    # Step 1: Fresh DB starts empty - Active target lookup returns 404
    res = client.get("/api/v1/targets/active")
    assert res.status_code == 404
    assert "No active project target configuration found" in res.json()["detail"]

    # Step 2: Probe Target Server (POST /targets/probe)
    probe_res = client.post("/api/v1/targets/probe", json={"target_url": "http://127.0.0.1:8001"})
    assert probe_res.status_code == 200
    assert probe_res.json()["is_active"] is True

    # Step 3: Self-Target Protection - Probing AuthTwin ports (5000, 5173) is rejected
    self_target_res = client.post("/api/v1/targets/probe", json={"target_url": "http://127.0.0.1:5000"})
    assert self_target_res.status_code == 400
    assert "Target Scope Violation" in self_target_res.json()["detail"]

    # Step 4: Explicit Operator Target Save (POST /targets/active)
    save_res = client.post("/api/v1/targets/active", json={"target_url": "http://127.0.0.1:8001"})
    assert save_res.status_code == 200
    target_data = save_res.json()
    assert target_data["base_url"] == "http://127.0.0.1:8001"
    target_id = target_data["id"]

    # Step 5: Active Target resolution from DB succeeds
    active_res = client.get("/api/v1/targets/active")
    assert active_res.status_code == 200
    assert active_res.json()["id"] == target_id

    # Step 6: Identity Creation (POST /identities)
    id_res = client.post("/api/v1/identities", json={
        "target_id": target_id,
        "name": "Security Analyst (Alice)",
        "role": "Primary",
        "auth_type": "Bearer"
    })
    assert id_res.status_code == 200
    identity_id = id_res.json()["id"]

    # Step 7: Identity Selection & Start Live Recording
    start_rec_res = client.post(f"/api/v1/interceptor/start-recording?identity_id={identity_id}")
    assert start_rec_res.status_code == 200
    assert start_rec_res.json()["status"] == "recording"

    # Step 8: Perform Target Plane HTTP Requests through Secret Proxy Middleware
    p1 = client.get("/api/v1/interceptor/proxy/")
    assert p1.status_code == 200
    assert "base href" in p1.text

    p2 = client.get("/api/v1/interceptor/proxy/api/v1/products")
    assert p2.status_code == 200

    p3 = client.get("/api/v1/interceptor/proxy/api/v1/products/17")
    assert p3.status_code == 200

    p4 = client.post("/api/v1/interceptor/proxy/api/v1/cart", json={"product_id": 17})
    assert p4.status_code == 200

    p5 = client.post("/api/v1/interceptor/proxy/api/v1/orders", json={"cart_id": "c-901"})
    assert p5.status_code == 200

    # Step 9: Control Plane API calls (e.g. GET /api/v1/targets) MUST NOT be captured into live buffer
    client.get("/api/v1/targets")

    # Step 10: Inspect Live Buffer
    buf_res = client.get("/api/v1/interceptor/live-buffer").json()
    assert buf_res["is_recording"] is True
    assert buf_res["count"] == 5

    # Step 11: Stop Recording & Process Session / Dependencies / WSG Generation
    stop_res = client.post("/api/v1/interceptor/stop-recording")
    assert stop_res.status_code == 200
    import_data = stop_res.json()
    session_id = import_data["session_id"]
    assert import_data["imported_count"] == 5

    # Step 12: Verify DB persistence of Session, Transactions, Dependencies, and Workflows
    db = TestingSessionLocal()
    saved_session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    assert saved_session is not None
    assert saved_session.identity_id == identity_id

    saved_txs = db.query(Transaction).filter(Transaction.session_id == session_id).all()
    assert len(saved_txs) == 5

    workflows = db.query(Workflow).filter(Workflow.session_id == session_id).all()
    assert len(workflows) > 0
    workflow_id = workflows[0].id

    # Step 13: Verify Workflow State Graph API
    wsg_res = client.get(f"/api/v1/workflows/{workflow_id}/graph")
    assert wsg_res.status_code == 200
    graph_data = wsg_res.json()
    assert len(graph_data["nodes"]) > 0

    # Step 14: Replay Readiness - Clone Workflow to Shadow Workflow for Alternate Identity
    id_bob = client.post("/api/v1/identities", json={
        "target_id": target_id,
        "name": "Alternate User (Bob)",
        "role": "Alternate"
    }).json()["id"]

    clone_res = client.post(f"/api/v1/workflows/{workflow_id}/clone", json={"shadow_identity_id": id_bob})
    assert clone_res.status_code == 200
    shadow_data = clone_res.json()
    assert shadow_data["shadow_identity_id"] == id_bob
    assert shadow_data["status"] == "MODEL_ONLY"

    # Step 15: Failure Test - Deleting target causes proxy to fail closed (HTTP 400)
    db.query(Target).delete()
    db.commit()

    fail_proxy_res = client.get("/api/v1/interceptor/proxy/api/v1/products")
    assert fail_proxy_res.status_code == 400
    assert "No active project target configuration found" in fail_proxy_res.json()["detail"]
