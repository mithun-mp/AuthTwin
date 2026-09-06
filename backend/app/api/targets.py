import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.database import get_db, get_active_target_model

from pydantic import BaseModel
from app.models import Target
from app.schemas import TargetCreate, TargetResponse
from app.api.interceptor import validate_target_scope, TargetVerifyRequest, TargetVerifyResponse, verify_target_server

router = APIRouter(prefix="/targets", tags=["Targets"])

class ActiveTargetUpdateRequest(BaseModel):
    target_url: str

@router.post("/probe", response_model=TargetVerifyResponse)
async def probe_target_endpoint(req: TargetVerifyRequest, db: DBSession = Depends(get_db)):
    """
    Probes candidate target application server without mutating database state.
    """
    return await verify_target_server(req, db)

@router.get("", response_model=List[TargetResponse])
def list_targets(db: DBSession = Depends(get_db)):
    return db.query(Target).order_by(Target.created_at.desc()).all()

@router.get("/active", response_model=TargetResponse)
def get_active_target(db: DBSession = Depends(get_db)):
    target = get_active_target_model(db)
    if not target:
        raise HTTPException(
            status_code=404,
            detail="No active project target configuration found. Please select or configure a target application first."
        )
    return target

@router.post("/active", response_model=TargetResponse)
def set_active_target(req: ActiveTargetUpdateRequest, db: DBSession = Depends(get_db)):
    clean_url = validate_target_scope(req.target_url)
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

@router.post("", response_model=TargetResponse)
def create_target(target_in: TargetCreate, db: DBSession = Depends(get_db)):
    clean_url = validate_target_scope(target_in.base_url)
    target = Target(
        id=str(uuid.uuid4()),
        name=target_in.name or f"Target ({clean_url})",
        base_url=clean_url,
        allowed_host_regex=target_in.allowed_host_regex
    )
    db.add(target)
    db.commit()
    db.refresh(target)
    return target

@router.get("/{target_id}", response_model=TargetResponse)
def get_target(target_id: str, db: DBSession = Depends(get_db)):
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    return target

@router.delete("/{target_id}")
def delete_target(target_id: str, db: DBSession = Depends(get_db)):
    target = db.query(Target).filter(Target.id == target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="Target not found")
    db.delete(target)
    db.commit()
    return {"message": f"Target {target_id} deleted successfully"}

