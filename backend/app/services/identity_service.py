import uuid
from typing import List, Optional
from sqlalchemy.orm import Session as DBSession
from fastapi import HTTPException
from app.core.database import get_active_target_model
from app.models.models import Identity, Target

def list_identities(db: DBSession, target_id: Optional[str] = None) -> List[Identity]:
    query = db.query(Identity)
    if target_id:
        query = query.filter(Identity.target_id == target_id)
    return query.all()

def create_identity(
    db: DBSession,
    name: str,
    role: str = "Primary",
    auth_type: str = "Bearer",
    target_id: Optional[str] = None
) -> Identity:
    target = None
    if target_id:
        target = db.query(Target).filter(Target.id == target_id).first()

    if not target:
        target = get_active_target_model(db)

    if not target:
        target = Target(
            id=str(uuid.uuid4()),
            name="Default Target App",
            base_url="http://127.0.0.1:8001"
        )
        db.add(target)
        db.commit()
        db.refresh(target)

    identity = Identity(
        id=str(uuid.uuid4()),
        target_id=target.id,
        name=name,
        role=role or "Primary",
        auth_type=auth_type or "Bearer"
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)
    return identity

def get_identity(db: DBSession, identity_id: str) -> Identity:
    identity = db.query(Identity).filter(Identity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity

def delete_identity(db: DBSession, identity_id: str) -> None:
    identity = db.query(Identity).filter(Identity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    db.delete(identity)
    db.commit()
