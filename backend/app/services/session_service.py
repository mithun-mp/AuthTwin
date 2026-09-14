import hashlib
import uuid
import datetime
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session as DBSession
from app.models.models import Identity, Session, Transaction

def get_token_fingerprint(headers: dict) -> Optional[str]:
    """Generates a safe SHA-256 fingerprint for an authentication token or session cookie."""
    if not headers:
        return None
    for k, v in headers.items():
        if str(k).lower() in ("authorization", "cookie", "x-api-key"):
            if v:
                return hashlib.sha256(str(v).encode("utf-8")).hexdigest()[:16]
    return None

def process_and_group_session(
    db: DBSession,
    target_id: str,
    transactions_raw: List[Dict[str, Any]],
    explicit_identity_id: Optional[str] = None
) -> Tuple[Session, List[Transaction]]:
    """
    Groups raw transactions into a logical Session, binds an Identity (or creates default Primary),
    and persists Session and Transactions to DB with redacted headers.
    """
    if not transactions_raw:
        raise ValueError("Cannot group empty transaction list into session")

    # Find token fingerprint from raw unredacted headers
    fingerprint = None
    for t in transactions_raw:
        raw_hdrs = t.get("raw_req_headers", {})
        fp = get_token_fingerprint(raw_hdrs)
        if fp:
            fingerprint = fp
            break

    # Resolve Identity
    identity = None
    if explicit_identity_id:
        identity = db.query(Identity).filter(Identity.id == explicit_identity_id).first()

    if not identity:
        identity = db.query(Identity).filter(Identity.target_id == target_id, Identity.role == "Primary").first()
        if not identity:
            identity = db.query(Identity).filter(Identity.target_id == target_id).first()
            
    if not identity:
        raise ValueError("No identity configured for target. Please create an identity first.")

    session_obj = Session(
        id=str(uuid.uuid4()),
        target_id=target_id,
        identity_id=identity.id,
        name=f"Session - {identity.name} ({fingerprint[:6] if fingerprint else 'anonymous'})",
        token_fingerprint=fingerprint,
        status="ACTIVE"
    )
    db.add(session_obj)
    db.flush()

    db_transactions = []
    for t_data in transactions_raw:
        raw_ts = t_data["timestamp"]
        if isinstance(raw_ts, str):
            try:
                raw_ts = datetime.datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
            except Exception:
                raw_ts = datetime.datetime.utcnow()

        tx = Transaction(
            id=t_data["id"],
            session_id=session_obj.id,
            timestamp=raw_ts,
            method=t_data["method"],
            url=t_data["url"],
            path=t_data["path"],
            query_params=t_data["query_params"],
            req_headers=t_data["req_headers"],  # Redacted headers
            req_body=t_data["req_body"],
            res_status=t_data["res_status"],
            res_headers=t_data["res_headers"],  # Redacted headers
            res_body=t_data["res_body"],
            operation_id=t_data.get("operation_id")
        )
        db.add(tx)
        db_transactions.append(tx)

    db.commit()
    return session_obj, db_transactions
