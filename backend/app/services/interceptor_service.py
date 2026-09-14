import uuid
import httpx
import datetime
import re
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
from fastapi import HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session as DBSession

from app.core.config import settings
from app.core.database import get_active_target_model
from app.core.logging import redact_headers, logger
from app.models.models import Target, Identity, Transaction, Session as SessionModel, OpenAPISpec
from app.schemas.schemas import HARImportResult
from app.services.target_service import validate_target_scope
from app.services.session_service import process_and_group_session
from app.services.dependency_service import analyze_session_dependencies
from app.services.workflow_service import generate_workflow_state_graph
from app.services.openapi_service import match_transactions_to_operations

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host", "content-length"
}

# In-memory session tracking state
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

        if (path.startswith("//") or path.startswith(settings.PROXY_PREFIX) or
            path.startswith("http://") or path.startswith("https://") or
            path.startswith("data:") or path.startswith("blob:") or
            path.startswith("javascript:") or path.startswith("#")):
            return match.group(0)

        if path.startswith("/"):
            new_path = f"{settings.PROXY_PREFIX}{path}"
        else:
            new_path = f"{settings.PROXY_PREFIX}/{path}"
            
        return f'{attr}={quote}{new_path}{quote}'

    pattern = re.compile(r'\b(src|href|action|formaction)\s*=\s*(["\'])([^"\']+)["\']', re.IGNORECASE)
    return pattern.sub(replace_attr, html_str)


def get_active_target_url(db: DBSession) -> str:
    """SINGLE SOURCE OF TRUTH: Obtains active target base_url from persisted Target model."""
    target = get_active_target_model(db)
    if not target or not target.base_url or not target.base_url.strip():
        raise HTTPException(
            status_code=400,
            detail="No active project target configuration found. Please select or configure a target application first."
        )
    return validate_target_scope(target.base_url)


def validate_transaction_target(transaction_url: str, active_target_url: str) -> str:
    """Require captured transaction URLs to stay on the validated target origin."""
    if not transaction_url or not transaction_url.strip():
        raise HTTPException(status_code=400, detail="Captured transaction URL cannot be empty.")

    parsed_transaction = urlparse(transaction_url.strip())
    if not parsed_transaction.scheme or not parsed_transaction.netloc:
        raise HTTPException(status_code=400, detail="Captured transaction URL must be absolute.")

    transaction_origin = f"{parsed_transaction.scheme}://{parsed_transaction.netloc}".lower()
    target_origin = f"{urlparse(active_target_url).scheme}://{urlparse(active_target_url).netloc}".lower()
    if transaction_origin != target_origin:
        raise HTTPException(
            status_code=400,
            detail="Captured transaction URL does not match the validated project target.",
        )
    return transaction_url.strip()


def start_live_recording(db: DBSession, identity_id: Optional[str] = None) -> Dict[str, Any]:
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

    logger.info(f"[INTERCEPTOR] Started live proxy middleware recording for {clean_target} under Identity {identity.name}")
    return {
        "status": "recording",
        "is_recording": True,
        "is_paused": False,
        "target_url": clean_target,
        "identity_id": identity.id,
        "identity_name": identity.name,
        "message": f"AuthTwin Live Proxy Middleware active for {clean_target}"
    }


def pause_live_recording() -> Dict[str, Any]:
    session = active_recording_sessions["default"]
    session["is_recording"] = False
    session["is_paused"] = True
    return {
        "status": "paused",
        "is_recording": False,
        "is_paused": True,
        "count": len(session["transactions"]),
        "message": "Live proxy middleware recording paused."
    }


def resume_live_recording() -> Dict[str, Any]:
    session = active_recording_sessions["default"]
    session["is_recording"] = True
    session["is_paused"] = False
    return {
        "status": "recording",
        "is_recording": True,
        "is_paused": False,
        "count": len(session["transactions"]),
        "message": "Live proxy middleware recording resumed."
    }


def clear_live_buffer() -> Dict[str, Any]:
    session = active_recording_sessions["default"]
    session["is_recording"] = False
    session["is_paused"] = False
    session["transactions"] = []
    return {
        "status": "cleared",
        "is_recording": False,
        "is_paused": False,
        "count": 0,
        "message": "Interceptor live buffer cleared."
    }


def get_live_buffer_data(db: DBSession) -> Dict[str, Any]:
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


def capture_live_session(db: DBSession, payload: Any) -> HARImportResult:
    target_url = validate_target_scope(payload.target_url)
    active_url = get_active_target_url(db)
    if target_url != active_url:
        raise HTTPException(status_code=400, detail="Capture target does not match the active project target configuration.")
    target = db.query(Target).filter(Target.base_url == active_url).first()
    if not target:
        raise HTTPException(status_code=400, detail="No active project target configuration found.")

    identity = None
    if payload.identity_id:
        identity = db.query(Identity).filter(Identity.id == payload.identity_id).first()
    if not identity:
        identity = db.query(Identity).filter(Identity.target_id == target.id, Identity.role == "Primary").first()
    if not identity:
        identity = db.query(Identity).filter(Identity.target_id == target.id).first()

    if not identity:
        raise HTTPException(status_code=400, detail="No identity configured for target. Please create an identity first.")

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

    session_obj, db_transactions = process_and_group_session(
        db=db,
        target_id=target.id,
        transactions_raw=raw_txs,
        explicit_identity_id=identity.id
    )

    spec = db.query(OpenAPISpec).filter(OpenAPISpec.target_id == target.id).first()
    if spec:
        match_transactions_to_operations(db, spec)

    analyze_session_dependencies(db, session_obj.id)
    generate_workflow_state_graph(db, session_obj.id)

    return HARImportResult(
        target_id=target.id,
        session_id=session_obj.id,
        imported_count=len(db_transactions),
        skipped_count=0,
        warnings=[],
        transactions=db_transactions
    )
