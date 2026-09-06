from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import (
    Session, Transaction, Dependency, Workflow,
    WorkflowNode, WorkflowEdge, ShadowWorkflow
)
from app.schemas import SessionResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])

@router.get("", response_model=List[SessionResponse])
def list_sessions(target_id: Optional[str] = Query(None), db: DBSession = Depends(get_db)):
    query = db.query(Session)
    if target_id:
        query = query.filter(Session.target_id == target_id)
    return query.order_by(Session.started_at.desc()).all()

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: str, db: DBSession = Depends(get_db)):
    session_obj = db.query(Session).filter(Session.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")
    return session_obj


@router.delete("/{session_id}")
def delete_session(session_id: str, db: DBSession = Depends(get_db)):
    """
    Deletes a session and cascadingly removes associated transactions,
    dependencies, workflows, nodes, edges, and shadow workflows.
    """
    session_obj = db.query(Session).filter(Session.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail="Session not found")

    # Delete workflows and shadow workflows
    workflows = db.query(Workflow).filter(Workflow.session_id == session_id).all()
    for wf in workflows:
        db.query(ShadowWorkflow).filter(ShadowWorkflow.source_workflow_id == wf.id).delete(synchronize_session=False)
        db.query(WorkflowEdge).filter(WorkflowEdge.workflow_id == wf.id).delete(synchronize_session=False)
        db.query(WorkflowNode).filter(WorkflowNode.workflow_id == wf.id).delete(synchronize_session=False)
        db.delete(wf)

    # Delete dependencies associated with session's transactions
    tx_ids = [t.id for t in db.query(Transaction.id).filter(Transaction.session_id == session_id).all()]
    if tx_ids:
        db.query(Dependency).filter(
            (Dependency.producer_transaction_id.in_(tx_ids)) | (Dependency.consumer_transaction_id.in_(tx_ids))
        ).delete(synchronize_session=False)

    # Delete transactions and session
    db.query(Transaction).filter(Transaction.session_id == session_id).delete(synchronize_session=False)
    db.delete(session_obj)
    db.commit()

    return {"message": f"Session {session_id} deleted successfully."}


@router.delete("")
def delete_all_sessions(target_id: Optional[str] = Query(None), db: DBSession = Depends(get_db)):
    """
    Clears sessions and dependent workflow/transaction records.
    """
    query = db.query(Session)
    if target_id:
        query = query.filter(Session.target_id == target_id)
    sessions = query.all()

    count = len(sessions)
    for s in sessions:
        delete_session(s.id, db)

    return {"message": f"Deleted {count} sessions."}

