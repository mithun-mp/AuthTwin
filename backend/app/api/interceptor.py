import uuid
import httpx
import datetime
import socket
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from fastapi import APIRouter, Depends, HTTPException, Request, Response, Body, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session as DBSession

from app.config import settings
from app.database import get_db, get_active_target_model
from app.models import Target, Transaction, Session as SessionModel, Identity, OpenAPISpec
from app.schemas import TransactionResponse, HARImportResult
from app.logging import redact_headers, logger
from app.identity.session_tracker import process_and_group_session
from app.dependencies.analyzer import analyze_session_dependencies
from app.workflows.wsg_generator import generate_workflow_state_graph

router = APIRouter(prefix="/interceptor", tags=["Live Interceptor"])

# Security & Proxy Constraints
MAX_BODY_BYTES = 10 * 1024 * 1024  # 10 MB limit
MAX_BUFFER_TXS = 1000               # Max live transactions per buffer session
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length"
}

PROXY_PREFIX = "/api/v1/interceptor/proxy"

# In-memory session tracking state (target_url is sourced directly from DB Target model)
active_recording_sessions: Dict[str, Dict[str, Any]] = {
    "default": {
        "is_recording": False,
        "is_paused": False,
        "identity_id": None,
        "identity_name": None,
        "transactions": []
    }
}


def rewrite_html_target_urls(html_str: str) -> str:
    """
    Rewrites relative URLs in HTML attributes (src, href, action, formaction)
    so that browser requests inside the iframe stay on the target plane via the proxy prefix.
    """
    if not html_str:
        return html_str

    def replace_attr(match):
        attr = match.group(1)   # src, href, action, formaction
        quote = match.group(2)  # " or '
        path = match.group(3)   # attribute value

        if (path.startswith("//") or path.startswith(PROXY_PREFIX) or
            path.startswith("http://") or path.startswith("https://") or
            path.startswith("data:") or path.startswith("blob:") or
            path.startswith("javascript:") or path.startswith("#")):
            return match.group(0)

        if path.startswith("/"):
            new_path = f"{PROXY_PREFIX}{path}"
        else:
            new_path = f"{PROXY_PREFIX}/{path}"
            
        return f'{attr}={quote}{new_path}{quote}'

    pattern = re.compile(r'\b(src|href|action|formaction)\s*=\s*(["\'])([^"\']+)["\']', re.IGNORECASE)
    return pattern.sub(replace_attr, html_str)


def validate_target_scope(target_url: str) -> str:
    """
    Validates target URL scheme, host, and prevents SSRF/self-target recursion
    to AuthTwin Control Plane endpoints (ports 8000, 5173, etc.), cloud metadata endpoints,
    or arbitrary internal loops.
    """
    if not target_url or not target_url.strip():
        raise HTTPException(
            status_code=400,
            detail="Target URL cannot be empty. Please configure your target application address."
        )

    clean_target = target_url.strip().rstrip("/")
    if not clean_target.startswith(("http://", "https://")):
        clean_target = f"http://{clean_target}"

    parsed = urlparse(clean_target)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid target URL scheme: {parsed.scheme}"
        )

    hostname = (parsed.hostname or "").lower()
    port = parsed.port or (80 if parsed.scheme == "http" else 443)

    # Normalize hostname & resolve IP
    resolved_ips = {hostname}
    try:
        ip = socket.gethostbyname(hostname)
        resolved_ips.add(ip)
    except Exception:
        pass

    # Check normalized endpoints against AuthTwin Control Plane listeners
    control_endpoints = settings.get_control_plane_endpoints()
    for h in resolved_ips:
        if (h, port) in control_endpoints:
            raise HTTPException(
                status_code=400,
                detail="Target Scope Violation: Candidate resolves to AuthTwin Control Plane."
            )

    # Check if path explicitly targets AuthTwin proxy route
    if parsed.path and parsed.path.startswith("/api/v1/interceptor/proxy"):
        raise HTTPException(
            status_code=400,
            detail="Target Scope Violation: Candidate resolves to AuthTwin Control Plane."
        )

    # Prevent Cloud Metadata SSRF
    if hostname in ("169.254.169.254", "metadata.google.internal"):
        raise HTTPException(status_code=403, detail="SSRF Violation: Access to cloud metadata endpoint forbidden.")

    return clean_target


def get_active_target_url(db: DBSession) -> str:
    """
    SINGLE SOURCE OF TRUTH: Obtains the active target base_url from the persisted
    Target model in the database. Fails closed if no target is configured.
    """
    target = get_active_target_model(db)
    if not target or not target.base_url or not target.base_url.strip():
        raise HTTPException(
            status_code=400,
            detail="No active project target configuration found. Please select or configure a target application first."
        )
    return validate_target_scope(target.base_url)


def validate_transaction_target(transaction_url: str, active_target_url: str) -> str:
    """Normalize and validate captured transaction URLs to ensure they resolve to target origin."""
    if not transaction_url or not transaction_url.strip():
        raise HTTPException(status_code=400, detail="Captured transaction URL cannot be empty.")

    clean_tx = transaction_url.strip()
    active_target = active_target_url.strip().rstrip("/")
    parsed_target = urlparse(active_target)
    target_netloc = parsed_target.netloc.lower()

    def normalize_host(netloc: str) -> str:
        return netloc.replace("localhost", "127.0.0.1")

    norm_target_netloc = normalize_host(target_netloc)

    # Check for proxy prefix
    has_proxy_prefix = PROXY_PREFIX in clean_tx
    if has_proxy_prefix:
        idx = clean_tx.find(PROXY_PREFIX)
        clean_tx = clean_tx[idx + len(PROXY_PREFIX):]
        if not clean_tx.startswith("/"):
            clean_tx = f"/{clean_tx}"

    parsed_tx = urlparse(clean_tx)

    # Convert relative path to absolute target URL
    if not parsed_tx.scheme or not parsed_tx.netloc:
        path = clean_tx if clean_tx.startswith("/") else f"/{clean_tx}"
        return f"{active_target}{path}"

    tx_netloc = normalize_host(parsed_tx.netloc.lower())

    if not has_proxy_prefix and tx_netloc != norm_target_netloc:
        raise HTTPException(
            status_code=400,
            detail="Captured transaction URL does not match the validated project target.",
        )

    return clean_tx


class TargetVerifyRequest(BaseModel):
    target_url: str

class TargetVerifyResponse(BaseModel):
    target_url: str
    is_active: bool
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    server_header: Optional[str] = None
    message: str

class LiveTransactionPayload(BaseModel):
    method: str
    url: str
    path: str
    query_params: Optional[Dict[str, Any]] = None
    req_headers: Optional[Dict[str, Any]] = None
    req_body: Optional[str] = None
    res_status: int
    res_headers: Optional[Dict[str, Any]] = None
    res_body: Optional[str] = None

class LiveCaptureSessionRequest(BaseModel):
    target_url: str
    identity_id: Optional[str] = None
    identity_name: Optional[str] = None
    transactions: List[LiveTransactionPayload]


@router.post("/verify", response_model=TargetVerifyResponse)
async def verify_target_server(req: TargetVerifyRequest, db: DBSession = Depends(get_db)):
    """
    Probes and verifies if a candidate target application address is active and valid.
    PROBE ONLY: Does NOT mutate or activate target in database until explicit operator save action.
    """
    target_url = validate_target_scope(req.target_url)

    start_time = datetime.datetime.utcnow()
    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            res = await client.get(target_url)
            elapsed_ms = (datetime.datetime.utcnow() - start_time).total_seconds() * 1000.0

            return TargetVerifyResponse(
                target_url=target_url,
                is_active=True,
                status_code=res.status_code,
                response_time_ms=round(elapsed_ms, 2),
                server_header=res.headers.get("server", "FastAPI / Uvicorn"),
                message=f"Target server ACTIVE on {target_url} (Status: {res.status_code}, Latency: {round(elapsed_ms, 1)}ms)"
            )
    except HTTPException:
        raise
    except Exception as err:
        return TargetVerifyResponse(
            target_url=target_url,
            is_active=False,
            status_code=None,
            response_time_ms=None,
            server_header=None,
            message=f"Target server UNREACHABLE on {target_url}. Error: {str(err)}"
        )


@router.post("/start-recording")
def start_live_recording(
    identity_id: Optional[str] = Query(None),
    db: DBSession = Depends(get_db)
):
    """
    Starts background live traffic middleware recording session.
    Sources the target URL from the active DB target configuration.
    Requires a valid identity_id configured for the target.
    """
    session = active_recording_sessions["default"]
    clean_target = get_active_target_url(db)
    target = get_active_target_model(db)

    identity = None
    if identity_id:
        identity = db.query(Identity).filter(Identity.id == identity_id).first()
    if not identity and target:
        identity = db.query(Identity).filter(Identity.target_id == target.id).first()

    if not identity:
        raise HTTPException(
            status_code=400,
            detail="No identity configured for target. Please create an identity first."
        )

    session["is_recording"] = True
    session["is_paused"] = False
    session["identity_id"] = identity.id
    session["identity_name"] = identity.name
    session["transactions"] = []

    logger.info(f"[INTERCEPTOR] Started live proxy middleware recording for {clean_target} under Identity {identity.name} ({identity.id})")
    return {
        "status": "recording",
        "is_recording": True,
        "is_paused": False,
        "target_url": clean_target,
        "identity_id": identity.id,
        "identity_name": identity.name,
        "message": f"AuthTwin Live Proxy Middleware active for {clean_target}"
    }


@router.post("/pause-recording")
def pause_live_recording():
    """
    Pauses live proxy middleware recording session without clearing the buffer.
    """
    session = active_recording_sessions["default"]
    session["is_recording"] = False
    session["is_paused"] = True
    logger.info(f"[INTERCEPTOR] Paused recording session ({len(session['transactions'])} transactions in buffer)")
    return {
        "status": "paused",
        "is_recording": False,
        "is_paused": True,
        "count": len(session["transactions"]),
        "message": "Live proxy middleware recording paused."
    }


@router.post("/resume-recording")
def resume_live_recording():
    """
    Resumes live proxy middleware recording session.
    """
    session = active_recording_sessions["default"]
    session["is_recording"] = True
    session["is_paused"] = False
    logger.info(f"[INTERCEPTOR] Resumed recording session ({len(session['transactions'])} transactions in buffer)")
    return {
        "status": "recording",
        "is_recording": True,
        "is_paused": False,
        "count": len(session["transactions"]),
        "message": "Live proxy middleware recording resumed."
    }


@router.api_route("/clear-buffer", methods=["POST", "DELETE"])
@router.api_route("/live-buffer", methods=["DELETE"])
def clear_live_buffer():
    """
    Wipes live memory buffer and resets recording state to Idle.
    """
    session = active_recording_sessions["default"]
    session["is_recording"] = False
    session["is_paused"] = False
    session["transactions"] = []
    logger.info("[INTERCEPTOR] Wiped live traffic memory buffer.")
    return {
        "status": "cleared",
        "is_recording": False,
        "is_paused": False,
        "count": 0,
        "message": "Interceptor live buffer cleared."
    }


@router.post("/restart-recording")
def restart_live_recording(
    identity_id: Optional[str] = Query(None),
    db: DBSession = Depends(get_db)
):
    """
    Clears live buffer and immediately restarts live traffic middleware recording session.
    """
    clear_live_buffer()
    return start_live_recording(identity_id=identity_id, db=db)


@router.get("/live-buffer")
def get_live_buffer(db: DBSession = Depends(get_db)):
    """
    Returns current live captured transactions buffer for real-time UI display.
    Target URL is sourced from the database Target model.
    """
    session = active_recording_sessions["default"]
    target_record = get_active_target_model(db)
    active_url = target_record.base_url if target_record else None

    sanitized_txs = []
    for tx in session["transactions"]:
        tx_copy = dict(tx)
        tx_copy["req_headers"] = redact_headers(tx.get("req_headers", {}))
        tx_copy["res_headers"] = redact_headers(tx.get("res_headers", {}))
        sanitized_txs.append(tx_copy)

    return {
        "is_recording": session.get("is_recording", False),
        "is_paused": session.get("is_paused", False),
        "target_url": active_url,
        "identity_id": session.get("identity_id"),
        "identity_name": session.get("identity_name"),
        "count": len(sanitized_txs),
        "transactions": sanitized_txs
    }


@router.post("/stop-recording", response_model=HARImportResult)
def stop_live_recording(db: DBSession = Depends(get_db)):
    """
    Stops live recording session, processes session grouping, OpenAPI matching,
    Dependency Analysis, and Workflow State Graph (WSG) generation.
    Handles empty buffer gracefully without 400 error.
    """
    session = active_recording_sessions["default"]
    target_model = get_active_target_model(db)

    session["is_recording"] = False
    session["is_paused"] = False

    if not session["transactions"]:
        return HARImportResult(
            target_id=target_model.id if target_model else "",
            session_id="",
            imported_count=0,
            skipped_count=0,
            warnings=["No live transactions were recorded during session."],
            transactions=[]
        )

    active_url = get_active_target_url(db)

    payload = LiveCaptureSessionRequest(
        target_url=active_url,
        identity_id=session.get("identity_id"),
        identity_name=session.get("identity_name"),
        transactions=[
            LiveTransactionPayload(**tx) for tx in session["transactions"]
        ]
    )

    result = capture_live_session(payload, db)
    session["transactions"] = []
    return result


@router.post("/capture-session", response_model=HARImportResult)
def capture_live_session(
    payload: LiveCaptureSessionRequest,
    db: DBSession = Depends(get_db)
):
    """
    Ingests live recorded HTTP transactions, associates session/identity,
    executes Dependency Analysis, and generates the Workflow State Graph (WSG).
    """
    target_url = validate_target_scope(payload.target_url)
    active_url = get_active_target_url(db)
    if target_url != active_url:
        raise HTTPException(status_code=400, detail="Capture target does not match the active project target configuration.")
    target = db.query(Target).filter(Target.base_url == active_url).first()
    if not target:
        raise HTTPException(status_code=400, detail="No active project target configuration found.")

    # Resolve Identity strictly from DB
    identity = None
    if payload.identity_id:
        identity = db.query(Identity).filter(Identity.id == payload.identity_id).first()
    if not identity:
        identity = db.query(Identity).filter(Identity.target_id == target.id, Identity.role == "Primary").first()
    if not identity:
        identity = db.query(Identity).filter(Identity.target_id == target.id).first()

    if not identity:
        raise HTTPException(status_code=400, detail="No identity configured for target. Please create an identity first.")

    # Format transactions for session tracker
    raw_txs = []
    now = datetime.datetime.utcnow()

    for idx, tx in enumerate(payload.transactions):
        raw_headers = tx.req_headers or {}
        redacted_req_hdrs = redact_headers(raw_headers)
        redacted_res_hdrs = redact_headers(tx.res_headers or {})

        raw_txs.append({
            "id": str(uuid.uuid4()),
            "timestamp": now + datetime.timedelta(seconds=idx * 2),
            "method": tx.method.upper(),
            "url": validate_transaction_target(tx.url, active_url),
            "path": tx.path,
            "query_params": tx.query_params or {},
            "req_headers": redacted_req_hdrs,
            "raw_req_headers": raw_headers,
            "req_body": tx.req_body or "",
            "res_status": tx.res_status,
            "res_headers": redacted_res_hdrs,
            "res_body": tx.res_body or "",
            "operation_id": None
        })

    if not raw_txs:
        raise HTTPException(status_code=400, detail="No transactions submitted for live capture")

    # 1. Group Session & Identity
    session_obj, db_transactions = process_and_group_session(
        db=db,
        target_id=target.id,
        transactions_raw=raw_txs,
        explicit_identity_id=identity.id
    )

    # 2. Auto-match OpenAPI operations if spec exists
    spec = db.query(OpenAPISpec).filter(OpenAPISpec.target_id == target.id).first()
    if spec:
        from app.openapi.loader import match_transactions_to_operations
        match_transactions_to_operations(db, spec)

    # 3. Dependency Analysis
    analyze_session_dependencies(db, session_obj.id)

    # 4. Workflow State Graph Generation
    generate_workflow_state_graph(db, session_obj.id)

    return HARImportResult(
        target_id=target.id,
        session_id=session_obj.id,
        imported_count=len(db_transactions),
        skipped_count=0,
        warnings=[],
        transactions=db_transactions
    )


@router.api_route("/proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def secret_proxy_middleware(request: Request, path: str = "", db: DBSession = Depends(get_db)):
    """
    Secret Reverse Proxy Middleware:
    - Obtains active target base URL from database Target model (single source of truth).
    - Enforces SSRF and normalized self-target protection.
    - Strips hop-by-hop headers.
    - Enforces MAX_BODY_BYTES size limit (10MB).
    - Prevents proxy loops (`X-AuthTwin-Proxy` check).
    - Auto-rewrites root-relative URLs in HTML attributes to proxy route.
    - Auto-injects client-side interceptor script with one-time guard and origin-based control-plane bypass.
    - Secretly captures target traffic into active recording session buffer with REDACTED credentials.
    """
    # Check for Proxy Loop recursion header
    if request.headers.get("X-AuthTwin-Proxy") == "1":
        logger.warning(f"[PROXY_LOOP_PREVENTED] Request to /{path} had X-AuthTwin-Proxy header set.")
        raise HTTPException(status_code=400, detail="Proxy Loop Detected: Interceptor cannot proxy requests to itself.")

    # SINGLE SOURCE OF TRUTH: Query active target from DB
    target_base = get_active_target_url(db)

    path_with_leading_slash = f"/{path}" if not path.startswith("/") else path
    target_full_url = f"{target_base}{path_with_leading_slash}"

    logger.info(f"[PROXY_IN] {request.method} /{path} | Target Base: {target_base}")
    logger.info(f"[PROXY_FWD] Forwarding {request.method} -> {target_full_url}")

    # Extract request payload & check size limit
    req_body_bytes = await request.body()
    if len(req_body_bytes) > MAX_BODY_BYTES:
        raise HTTPException(status_code=413, detail=f"Request body exceeds maximum allowed size of {MAX_BODY_BYTES // (1024*1024)}MB.")

    req_body_str = req_body_bytes.decode("utf-8", errors="ignore")

    # Filter out Hop-by-Hop headers
    forward_headers = {
        k: v for k, v in request.headers.items()
        if k.lower() not in HOP_BY_HOP_HEADERS
    }
    forward_headers["X-AuthTwin-Proxy"] = "1"

    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
        try:
            target_res = await client.request(
                method=request.method,
                url=target_full_url,
                params=dict(request.query_params),
                headers=forward_headers,
                content=req_body_bytes
            )
            logger.info(f"[PROXY_OUT] Target {target_full_url} responded with Status: {target_res.status_code}")
        except Exception as proxy_err:
            logger.error(f"[PROXY_ERR] Failed to reach target {target_full_url}: {str(proxy_err)}")
            return HTMLResponse(
                content=f"<h3>AuthTwin Proxy Error</h3><p>Could not connect to target application at <code>{target_full_url}</code>.</p><p>Error: {str(proxy_err)}</p>",
                status_code=502
            )

    res_content = target_res.content
    if len(res_content) > MAX_BODY_BYTES:
        return Response(content="Response body exceeds 10MB limit", status_code=413)

    res_headers = dict(target_res.headers)
    res_body_str = target_res.text

    content_type = target_res.headers.get("content-type", "").lower()

    # Self-Target HTML Signature Inspection: Reject target if response HTML is AuthTwin itself
    if "text/html" in content_type:
        if ("<title>AuthTwin" in res_body_str or
            "AuthTwin — Workflow-Aware" in res_body_str or
            "VITE_AUTHTWIN" in res_body_str or
            ('id="root"' in res_body_str and '/src/main.tsx' in res_body_str)):
            logger.warning(f"[SELF_TARGET_HTML_REJECTED] Target HTML on {target_full_url} matched AuthTwin Control Plane signature.")
            raise HTTPException(
                status_code=400,
                detail="Target Scope Violation: Candidate application resolves to AuthTwin Control Plane."
            )

        # Rewrite root-relative attributes (src="/...", href="/...", action="/...", formaction="/...") to stay on proxy route
        res_body_str = rewrite_html_target_urls(res_body_str)

        base_tag = '<base href="/api/v1/interceptor/proxy/">'
        if "<head>" in res_body_str:
            res_body_str = res_body_str.replace("<head>", f"<head>{base_tag}")
        elif "<HEAD>" in res_body_str:
            res_body_str = res_body_str.replace("<HEAD>", f"<HEAD>{base_tag}")
        else:
            res_body_str = f"{base_tag}{res_body_str}"

        injected_script = """
        <script>
        /* AuthTwin Secret Middleware Interceptor Auto-Patch (Guarded & Isolated) */
        (function() {
            if (window.__AUTHTWIN_INTERCEPTOR_INSTALLED__) return;
            window.__AUTHTWIN_INTERCEPTOR_INSTALLED__ = true;

            const PROXY_PREFIX = '/api/v1/interceptor/proxy';
            const CONTROL_ORIGINS = [window.location.origin];

            const AUTHTWIN_CONTROL_PATHS = [
                '/api/v1/targets', '/api/v1/identities', '/api/v1/sessions',
                '/api/v1/transactions', '/api/v1/dependencies', '/api/v1/workflows',
                '/api/v1/shadow-workflows', '/api/v1/openapi', '/api/v1/health',
                '/api/v1/interceptor/verify', '/api/v1/interceptor/live-buffer',
                '/api/v1/interceptor/start-recording', '/api/v1/interceptor/stop-recording'
            ];

            function isControlPlaneRequest(urlStr) {
                if (!urlStr || typeof urlStr !== 'string') return false;
                try {
                    const parsed = new URL(urlStr, window.location.origin);
                    const isControlOrigin = CONTROL_ORIGINS.includes(parsed.origin);
                    if (isControlOrigin && !parsed.pathname.startsWith(PROXY_PREFIX)) {
                        if (AUTHTWIN_CONTROL_PATHS.some(p => parsed.pathname.startsWith(p))) {
                            return true;
                        }
                    }
                } catch(e) {}
                return false;
            }

            function rewriteUrl(urlStr) {
                if (!urlStr || typeof urlStr !== 'string') return urlStr;
                if (urlStr.startsWith(PROXY_PREFIX)) return urlStr;
                if (urlStr.startsWith('data:') || urlStr.startsWith('blob:') || urlStr.startsWith('#') || urlStr.startsWith('javascript:')) return urlStr;
                
                if (isControlPlaneRequest(urlStr)) {
                    return urlStr;
                }

                if (urlStr.startsWith('/')) {
                    return PROXY_PREFIX + urlStr;
                }
                try {
                    const parsed = new URL(urlStr, window.location.origin);
                    if (parsed.pathname.startsWith(PROXY_PREFIX)) return urlStr;
                    return PROXY_PREFIX + parsed.pathname + parsed.search + parsed.hash;
                } catch(e) {
                    return PROXY_PREFIX + (urlStr.startsWith('/') ? urlStr : '/' + urlStr);
                }
            }

            // Patch Fetch
            const origFetch = window.fetch;
            window.fetch = async function(input, init) {
                let url = typeof input === 'string' ? input : (input instanceof Request ? input.url : String(input));
                if (isControlPlaneRequest(url)) {
                    return origFetch(input, init);
                }
                const proxiedUrl = rewriteUrl(url);
                if (typeof input === 'string') {
                    return origFetch(proxiedUrl, init);
                } else if (input instanceof Request) {
                    return origFetch(new Request(proxiedUrl, input), init);
                }
                return origFetch(input, init);
            };

            // Patch XMLHttpRequest
            const origOpen = XMLHttpRequest.prototype.open;
            XMLHttpRequest.prototype.open = function(method, url, ...args) {
                if (isControlPlaneRequest(url)) {
                    return origOpen.call(this, method, url, ...args);
                }
                const proxiedUrl = rewriteUrl(url);
                return origOpen.call(this, method, proxiedUrl, ...args);
            };

            // Patch History API (pushState & replaceState)
            const origPushState = history.pushState;
            history.pushState = function(state, title, url) {
                if (url && typeof url === 'string' && !url.startsWith(PROXY_PREFIX) && !isControlPlaneRequest(url)) {
                    url = rewriteUrl(url);
                }
                return origPushState.call(this, state, title, url);
            };

            const origReplaceState = history.replaceState;
            history.replaceState = function(state, title, url) {
                if (url && typeof url === 'string' && !url.startsWith(PROXY_PREFIX) && !isControlPlaneRequest(url)) {
                    url = rewriteUrl(url);
                }
                return origReplaceState.call(this, state, title, url);
            };

            // Intercept link clicks & form submissions
            document.addEventListener('click', function(e) {
                const link = e.target.closest('a');
                if (link && link.getAttribute('href')) {
                    const href = link.getAttribute('href');
                    if (!href.startsWith(PROXY_PREFIX) && !href.startsWith('http') && !href.startsWith('#') && !href.startsWith('javascript:')) {
                        const newHref = rewriteUrl(href);
                        link.setAttribute('href', newHref);
                    }
                }
            }, true);

            document.addEventListener('submit', function(e) {
                const form = e.target;
                if (form) {
                    const action = form.getAttribute('action') || '';
                    if (!action.startsWith(PROXY_PREFIX) && !action.startsWith('http')) {
                        const newAction = rewriteUrl(action);
                        form.setAttribute('action', newAction);
                    }
                }
            }, true);
        })();
        </script>
        """
        if "</body>" in res_body_str:
            res_body_str = res_body_str.replace("</body>", f"{injected_script}</body>")
        else:
            res_body_str += injected_script
        res_content = res_body_str.encode("utf-8")

    # Control plane & development asset path prefixes to bypass live recording capture
    CONTROL_PLANE_PATHS = (
        "/api/v1/targets", "/api/v1/identities", "/api/v1/sessions",
        "/api/v1/transactions", "/api/v1/dependencies", "/api/v1/workflows",
        "/api/v1/shadow-workflows", "/api/v1/openapi", "/api/v1/health",
        "/api/v1/interceptor/verify", "/api/v1/interceptor/live-buffer",
        "/api/v1/interceptor/start-recording", "/api/v1/interceptor/stop-recording",
        "/@vite", "/src/", "/node_modules/", "/favicon.ico"
    )


    # If live recording is ACTIVE, save target transaction into buffer (MAX_BUFFER_TXS check)
    session = active_recording_sessions["default"]
    if session.get("is_recording"):
        if not any(path_with_leading_slash.startswith(cp) for cp in CONTROL_PLANE_PATHS):
            if len(session["transactions"]) < MAX_BUFFER_TXS:
                raw_req_hdrs = dict(request.headers)
                tx_data = {
                    "method": request.method,
                    "url": target_full_url,
                    "path": path_with_leading_slash,
                    "query_params": dict(request.query_params),
                    "req_headers": redact_headers(raw_req_hdrs),     # STORE REDACTED FOR BUFFER/UI
                    "raw_req_headers": raw_req_hdrs,                 # RETAIN INTERNAL FOR FINGERPRINTING ONLY
                    "req_body": req_body_str,
                    "res_status": target_res.status_code,
                    "res_headers": redact_headers(res_headers),      # STORE REDACTED FOR BUFFER/UI
                    "res_body": res_body_str
                }
                session["transactions"].append(tx_data)
                logger.info(f"[INTERCEPTED] {request.method} {path_with_leading_slash} ({target_res.status_code}) -> Total Captured: {len(session['transactions'])}")
            else:
                logger.warning(f"[INTERCEPTOR] Live buffer limit of {MAX_BUFFER_TXS} reached. Skipping capture.")

    # Filter response headers & rewrite Location headers for redirects
    clean_res_headers = {}
    for k, v in res_headers.items():
        k_lower = k.lower()
        if k_lower in HOP_BY_HOP_HEADERS or k_lower == "content-encoding":
            continue
        if k_lower == "location":
            if v.startswith(target_base):
                rel_p = v[len(target_base):]
                v = f"{PROXY_PREFIX}{rel_p if rel_p.startswith('/') else '/' + rel_p}"
            elif v.startswith("/") and not v.startswith(PROXY_PREFIX):
                v = f"{PROXY_PREFIX}{v}"
        clean_res_headers[k] = v

    return Response(
        content=res_content,
        status_code=target_res.status_code,
        headers=clean_res_headers,
        media_type=content_type or "text/html"
    )
