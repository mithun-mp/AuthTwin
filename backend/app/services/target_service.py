import uuid
import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException
import httpx

from app.core.config import settings
from app.core.database import get_active_target_model
from app.core.logging import logger
from app.models.models import Target

def validate_target_scope(target_url: str) -> str:
    """
    Validates target URL scheme, host, and prevents SSRF/self-target recursion
    to AuthTwin Control Plane endpoints (ports 5000, 5173, etc.), cloud metadata endpoints,
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
        import socket
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
    if parsed.path and parsed.path.startswith(settings.PROXY_PREFIX):
        raise HTTPException(
            status_code=400,
            detail="Target Scope Violation: Candidate resolves to AuthTwin Control Plane."
        )

    # Prevent Cloud Metadata SSRF
    if hostname in ("169.254.169.254", "metadata.google.internal"):
        raise HTTPException(status_code=403, detail="SSRF Violation: Access to cloud metadata endpoint forbidden.")

    return clean_target


async def probe_target_server(target_url: str) -> Dict[str, Any]:
    """Probes target application server without mutating database state."""
    clean_url = validate_target_scope(target_url)
    start_time = datetime.datetime.utcnow()
    try:
        async with httpx.AsyncClient(timeout=4.0, follow_redirects=True) as client:
            res = await client.get(clean_url)
            elapsed_ms = (datetime.datetime.utcnow() - start_time).total_seconds() * 1000.0
            return {
                "target_url": clean_url,
                "is_active": True,
                "status_code": res.status_code,
                "response_time_ms": round(elapsed_ms, 2),
                "server_header": res.headers.get("server", "Target App"),
                "message": f"Target server ACTIVE on {clean_url} (Status: {res.status_code}, Latency: {round(elapsed_ms, 1)}ms)"
            }
    except HTTPException:
        raise
    except Exception as err:
        return {
            "target_url": clean_url,
            "is_active": False,
            "status_code": None,
            "response_time_ms": None,
            "server_header": None,
            "message": f"Target server UNREACHABLE on {clean_url}. Error: {str(err)}"
        }


def get_active_target(db: DBSession) -> Target:
    target = get_active_target_model(db)
    if not target:
        raise HTTPException(
            status_code=404,
            detail="No active project target configuration found. Please select or configure a target application first."
        )
    return target


def set_active_target(db: DBSession, target_url: str) -> Target:
    clean_url = validate_target_scope(target_url)
    target = get_active_target_model(db)
    if not target:
        target = Target(
            id=str(uuid.uuid4()),
            name=f"Target ({clean_url})",
            base_url=clean_url
        )
        db.add(target)
    else:
        target.base_url = clean_url
        target.name = f"Target ({clean_url})"
    db.commit()
    db.refresh(target)
    return target


def list_targets(db: DBSession) -> List[Target]:
    return db.query(Target).order_by(Target.created_at.desc()).all()


def create_target(db: DBSession, name: str, base_url: str, allowed_host_regex: Optional[str] = None) -> Target:
    clean_url = validate_target_scope(base_url)
    target = Target(
        id=str(uuid.uuid4()),
        name=name or f"Target ({clean_url})",
        base_url=clean_url,
        allowed_host_regex=allowed_host_regex
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target


def delete_target(db: DBSession, target_id: str) -> None:
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
