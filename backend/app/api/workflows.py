from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import Workflow, WorkflowNode, WorkflowEdge, Dependency, Transaction
from app.schemas import (
    WorkflowResponse, WorkflowGraphResponse, WorkflowNodeResponse,
    WorkflowEdgeResponse, DependencyResponse, ShadowWorkflowCreate, ShadowWorkflowResponse
)
from app.shadow.cloner import clone_shadow_workflow

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
    wf = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not wf:
        raise HTTPException(status_code=404, detail="Workflow not found")

    nodes = db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow_id).order_by(WorkflowNode.sequence_index.asc()).all()
    edges = db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == workflow_id).all()

    tx_ids = [n.transaction_id for n in nodes]
    dependencies = db.query(Dependency).filter(Dependency.producer_transaction_id.in_(tx_ids)).all()

    return WorkflowGraphResponse(
        workflow=wf,
        nodes=nodes,
        edges=edges,
        dependencies=dependencies
    )

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
    from app.models import ShadowWorkflow
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

