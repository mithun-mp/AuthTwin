from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import Dependency, Transaction
from app.schemas import DependencyResponse

router = APIRouter(prefix="/dependencies", tags=["Dependencies"])

@router.get("", response_model=List[DependencyResponse])
def list_dependencies(
    session_id: Optional[str] = Query(None),
    db: DBSession = Depends(get_db)
):
    query = db.query(Dependency)
    if session_id:
        tx_ids = [tx.id for tx in db.query(Transaction.id).filter(Transaction.session_id == session_id).all()]
        query = query.filter(Dependency.producer_transaction_id.in_(tx_ids))
    return query.all()

@router.get("/{dependency_id}", response_model=DependencyResponse)
def get_dependency(dependency_id: str, db: DBSession = Depends(get_db)):
    dep = db.query(Dependency).filter(Dependency.id == dependency_id).first()
    if not dep:
        raise HTTPException(status_code=404, detail="Dependency not found")
    return dep
