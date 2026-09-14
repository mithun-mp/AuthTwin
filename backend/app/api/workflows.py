from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.core.database import get_db
from app.models.models import Workflow, WorkflowNode, WorkflowEdge, ShadowWorkflow
from app.schemas.schemas import (
    WorkflowResponse, WorkflowGraphResponse, ShadowWorkflowCreate, ShadowWorkflowResponse
)
from app.services.shadow_service import clone_shadow_workflow
from app.services.workflow_service import get_workflow_graph_details

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.get("", response_model=List[WorkflowResponse])
def list_workflows(db: DBSession = Depends(get_db)):
    return db.query(Workflow).order_by(Workflow.created_at.desc()).all()

@router.get("/{workflow_id}", response_model=WorkflowResponse)
def get_workflow(workflow_id: str, db: DBSession = Depends(get_db)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return wf

@router.get("/{workflow_id}/graph", response_model=WorkflowGraphResponse)
def get_workflow_graph(workflow_id: str, db: DBSession = Depends(get_db)):
    try:
        return get_workflow_graph_details(db, workflow_id)
    except ValueError as err:
        raise HTTPException(status_code=404, detail=str(err))

@router.post("/{workflow_id}/clone", response_model=ShadowWorkflowResponse)
def clone_workflow(
    workflow_id: str,
    clone_in: ShadowWorkflowCreate,
    db: DBSession = Depends(get_db)
):
    try:
        shadow_wf = clone_shadow_workflow(
            db=db,
            source_workflow_id=workflow_id,
            shadow_identity_id=clone_in.shadow_identity_id
        )
        return shadow_wf
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: str, db: DBSession = Depends(get_db)):
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    db.query(ShadowWorkflow).filter(ShadowWorkflow.source_workflow_id == workflow_id).delete(synchronize_session=False)
    db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id).delete(synchronize_session=False)
    db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).delete(synchronize_session=False)
    db.delete(wf)
    db.commit()
    return {"message": f"Workflow {workflow_id} deleted successfully."}

@router.delete("")
def delete_all_workflows(db: DBSession = Depends(get_db)):
    wfs = db.query(Workflow).all()
    count = len(wfs)
    for wf in wfs:
        delete_workflow(wf.id, db)
    return {"message": f"Deleted {count} workflows."}
