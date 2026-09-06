from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import ShadowWorkflow
from app.schemas import ShadowWorkflowResponse

router = APIRouter(prefix="/shadow-workflows", tags=["Shadow Workflows"])

@router.get("", response_model=List[ShadowWorkflowResponse])
def list_shadow_workflows(db: DBSession = Depends(get_db)):
    return db.query(ShadowWorkflow).order_by(ShadowWorkflow.created_at.desc()).all()

@router.get("/{shadow_id}", response_model=ShadowWorkflowResponse)
def get_shadow_workflow(shadow_id: str, db: DBSession = Depends(get_db)):
    shadow = db.query(ShadowWorkflow).filter(ShadowWorkflow.id == shadow_id).first()
    if not shadow:
        raise HTTPException(status_code=404, detail="Shadow Workflow not found")
    return shadow
