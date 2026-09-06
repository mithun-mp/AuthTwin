from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import OpenAPISpec
from app.schemas import OpenAPISpecResponse

router = APIRouter(prefix="/openapi", tags=["OpenAPI"])

@router.get("/specs", response_model=List[OpenAPISpecResponse])
def list_openapi_specs(
    target_id: Optional[str] = Query(None),
    db: DBSession = Depends(get_db)
):
    query = db.query(OpenAPISpec)
    if target_id:
        query = query.filter(OpenAPISpec.target_id == target_id)
    return query.order_by(OpenAPISpec.created_at.desc()).all()

@router.get("/specs/{spec_id}", response_model=OpenAPISpecResponse)
def get_openapi_spec(spec_id: str, db: DBSession = Depends(get_db)):
    spec = db.query(OpenAPISpec).filter(OpenAPISpec.id == spec_id).first()
    if not spec:
        raise HTTPException(status_code=404, detail="OpenAPI specification not found")
    return spec
