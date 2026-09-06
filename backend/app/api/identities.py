import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.database import get_db, get_active_target_model
from app.models import Identity, Target
from app.schemas import IdentityCreate, IdentityResponse

router = APIRouter(prefix="/identities", tags=["Identities"])

@router.get("", response_model=List[IdentityResponse])
def list_identities(target_id: Optional[str] = Query(None), db: DBSession = Depends(get_db)):
    query = db.query(Identity)
    if target_id:
        query = query.filter(Identity.target_id == target_id)
    return query.all()

@router.post("", response_model=IdentityResponse)
def create_identity(identity_in: IdentityCreate, db: DBSession = Depends(get_db)):
    target = None
    if identity_in.target_id:
        target = db.query(Target).filter(Target.id == identity_in.target_id).first()

    if not target:
        target = get_active_target_model(db)

    if not target:
        # Auto-create active Target model if none exists yet
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
        name=identity_in.name,
        role=identity_in.role or "Primary",
        auth_type=identity_in.auth_type or "Bearer"
    )
    db.add(identity)
    db.commit()
    db.refresh(identity)
    return identity

@router.get("/{identity_id}", response_model=IdentityResponse)
def get_identity(identity_id: str, db: DBSession = Depends(get_db)):
    identity = db.query(Identity).filter(Identity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return identity

@router.delete("/{identity_id}")
def delete_identity(identity_id: str, db: DBSession = Depends(get_db)):
    identity = db.query(Identity).filter(Identity.id == identity_id).first()
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    db.delete(identity)
    db.commit()
    return {"message": f"Identity {identity_id} deleted successfully."}

