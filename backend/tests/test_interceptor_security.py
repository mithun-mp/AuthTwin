import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import Base, get_db
from app.models import Target, Identity, Workflow, ShadowWorkflow
from app.api import interceptor as interceptor_api

# Setup in-memory SQLite database for testing
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

@pytest.fixture(autouse=True)
def setup_db():
    Target.__table__.metadata.create_all(bind=engine)
    yield
    Target.__table__.metadata.drop_all(bind=engine)


def test_ssrf_target_scope_protection():
    """Verify target scope validation blocks AuthTwin control-plane addresses and SSRF endpoints."""
    # Test 1: Block AuthTwin server port 5000
    res = client.post("/api/v1/interceptor/verify", json={"target_url": "http://127.0.0.1:5000"})
    assert res.status_code == 400
    assert "Target Scope Violation" in res.json()["detail"]


    # Test 2: Block AuthTwin frontend port 5173
    res = client.post("/api/v1/interceptor/verify", json={"target_url": "http://localhost:5173"})
    assert res.status_code == 400
    assert "Target Scope Violation" in res.json()["detail"]

    # Test 3: Block Cloud Metadata address
    res = client.post("/api/v1/interceptor/verify", json={"target_url": "http://169.254.169.254/latest/meta-data"})
    assert res.status_code == 403
    assert "SSRF Violation" in res.json()["detail"]


def test_controlled_target_is_accepted_without_auto_registration():
    db = TestingSessionLocal()
    db.add(Target(id="controlled", name="Controlled Target", base_url="http://target.example"))
    db.commit()

    res = client.post("/api/v1/interceptor/verify", json={"target_url": "http://target.example"})

    assert res.status_code == 200
    assert res.json()["is_active"] is False
    assert db.query(Target).count() == 1


def test_active_target_endpoint_fails_closed_without_configuration():
    res = client.get("/api/v1/targets/active")

    assert res.status_code == 404
    assert "No active project target configuration found" in res.json()["detail"]


def test_proxy_loop_header_protection():
    """Verify X-AuthTwin-Proxy header prevents infinite proxy recursion loops."""
    res = client.get("/api/v1/interceptor/proxy/login", headers={"X-AuthTwin-Proxy": "1"})
    assert res.status_code == 400
    assert "Proxy Loop Detected" in res.json()["detail"]


def test_no_configured_target_fail_closed():
    """Verify secret_proxy_middleware fails closed (HTTP 400) if database has no configured target."""
    res = client.get("/api/v1/interceptor/proxy/some-route")
    assert res.status_code == 400
    assert "No active project target configuration found" in res.json()["detail"]


def test_capture_rejects_target_that_is_not_active_configuration():
    db = TestingSessionLocal()
    db.add(Target(id="configured", name="Configured Target", base_url="http://target.example"))
    db.commit()

    res = client.post("/api/v1/interceptor/capture-session", json={
        "target_url": "http://other.example",
        "transactions": [{
            "method": "GET",
            "url": "http://other.example/api/v1/projects",
            "path": "/api/v1/projects",
            "res_status": 200,
        }],
    })

    assert res.status_code == 400
    assert "does not match the active project target" in res.json()["detail"]


def test_capture_rejects_transaction_from_control_plane_origin():
    db = TestingSessionLocal()
    t = Target(id="configured", name="Configured Target", base_url="http://target.example")
    id_obj = Identity(id="id-configured", target_id="configured", name="Analyst", role="Primary")
    db.add_all([t, id_obj])
    db.commit()

    res = client.post("/api/v1/interceptor/capture-session", json={
        "target_url": "http://target.example",
        "transactions": [{
            "method": "GET",
            "url": "http://localhost:5000/api/v1/targets",

            "path": "/api/v1/targets",
            "res_status": 200,
        }],
    })

    assert res.status_code == 400
    assert "does not match the validated project target" in res.json()["detail"]


class FakeUpstreamResponse:
    def __init__(self, content: bytes, content_type: str, status_code: int = 200):
        self.content = content
        self.headers = {"content-type": content_type}
        self.status_code = status_code
        self.text = content.decode("utf-8")


class FakeAsyncClient:
    response = FakeUpstreamResponse(b'{"ok":true}', "application/json")
    requested_url = None

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def request(self, method, url, **kwargs):
        self.requested_url = url
        type(self).requested_url = url
        return type(self).response


def test_target_api_path_is_forwarded_and_captured(monkeypatch):
    db = TestingSessionLocal()
    db.add(Target(id="target-api", name="Target API", base_url="http://target.example"))
    db.commit()
    monkeypatch.setattr(interceptor_api.httpx, "AsyncClient", FakeAsyncClient)

    res = client.get("/api/v1/interceptor/proxy/api/v1/projects")

    assert res.status_code == 200
    assert FakeAsyncClient.requested_url == "http://target.example/api/v1/projects"


def test_auth_credential_redaction_in_live_buffer():
    """Verify Authorization tokens, session cookies, and API keys are redacted in live buffer output."""
    # 1. Seed a valid target & identity
    db = TestingSessionLocal()
    t = Target(id="t1", name="Target 1", base_url="http://127.0.0.1:8001")
    alice = Identity(id="i1", target_id="t1", name="Alice", role="Primary")
    db.add_all([t, alice])
    db.commit()

    # 1. Start recording with explicit identity_id
    client.post("/api/v1/interceptor/start-recording", params={"identity_id": "i1"})

    # 2. Submit transaction with secret token via capture session
    secret_headers = {
        "Authorization": "Bearer SUPER_SECRET_TEST_TOKEN",
        "Cookie": "session=SUPER_SECRET_SESSION_COOKIE",
        "X-API-Key": "SUPER_SECRET_API_KEY"
    }

    payload = {
        "target_url": "http://127.0.0.1:8001",
        "identity_id": "i1",
        "identity_name": "Alice (Test)",
        "transactions": [
            {
                "method": "POST",
                "url": "http://127.0.0.1:8001/login",
                "path": "/login",
                "req_headers": secret_headers,
                "req_body": '{"username":"alice"}',
                "res_status": 200,
                "res_headers": {"Content-Type": "application/json"},
                "res_body": '{"token":"Bearer SUPER_SECRET_TEST_TOKEN"}'
            }
        ]
    }
    
    res = client.post("/api/v1/interceptor/capture-session", json=payload)
    assert res.status_code == 200


    # 3. Retrieve live buffer and verify raw secrets are NOT exposed
    buffer_res = client.get("/api/v1/interceptor/live-buffer").json()
    for tx in buffer_res.get("transactions", []):
        req_hdrs = tx.get("req_headers", {})
        assert "SUPER_SECRET_TEST_TOKEN" not in req_hdrs.get("Authorization", "")
        assert "[REDACTED]" in req_hdrs.get("Authorization", "")
        assert "SUPER_SECRET_SESSION_COOKIE" not in req_hdrs.get("Cookie", "")
        assert "SUPER_SECRET_API_KEY" not in req_hdrs.get("X-API-Key", "")


def test_shadow_clone_model_only_boundary():
    """Verify cloning a workflow into a shadow workflow creates ZERO HTTP replay calls and maintains MODEL_ONLY status."""
    db = TestingSessionLocal()
    target = Target(id="t1", name="Target 1", base_url="http://127.0.0.1:8001")
    alice = Identity(id="i1", target_id="t1", name="Alice", role="Primary")
    bob = Identity(id="i2", target_id="t1", name="Bob", role="Alternate")
    db.add_all([target, alice, bob])
    db.commit()

    # Import session
    har_payload = {
        "target_url": "http://127.0.0.1:8001",
        "identity_id": "i1",
        "identity_name": "Alice",
        "transactions": [

            {
                "method": "GET",
                "url": "http://127.0.0.1:8001/projects",
                "path": "/projects",
                "res_status": 200
            }
        ]
    }
    import_res = client.post("/api/v1/interceptor/capture-session", json=har_payload).json()
    session_id = import_res["session_id"]

    workflows = client.get("/api/v1/workflows").json()
    assert len(workflows) > 0
    wf_id = workflows[0]["id"]

    # Clone Workflow to Shadow
    clone_res = client.post(f"/api/v1/workflows/{wf_id}/clone", json={"shadow_identity_id": "i2"})
    assert clone_res.status_code == 200
    shadow_data = clone_res.json()

    assert shadow_data["status"] == "MODEL_ONLY"
    assert shadow_data["clone_policy"] == "CREDENTIAL_ISOLATED"
    assert shadow_data["shadow_identity_id"] == "i2"
