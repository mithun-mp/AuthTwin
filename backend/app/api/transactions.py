from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import Transaction
from app.schemas import TransactionResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("", response_model=List[TransactionResponse])
def list_transactions(session_id: Optional[str] = Query(None), db: DBSession = Depends(get_db)):
    query = db.query(Transaction)
    if session_id:
        query = query.filter(Transaction.session_id == session_id)
    return query.order_by(Transaction.timestamp.asc()).all()

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(transaction_id: str, db: DBSession = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return tx
