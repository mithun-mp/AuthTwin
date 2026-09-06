import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session as DBSession
from app.database import get_db, get_active_target_model
from app.models import Target, Identity, OpenAPISpec
from app.schemas import HARImportResult, OpenAPISpecResponse
from app.ingestion.har_parser import parse_har_content
from app.identity.session_tracker import process_and_group_session
from app.openapi.loader import load_and_save_openapi
from app.dependencies.analyzer import analyze_session_dependencies
from app.workflows.wsg_generator import generate_workflow_state_graph

router = APIRouter(prefix="/import", tags=["Imports"])

@router.post("/har", response_model=HARImportResult)
async def import_har(
    file: UploadFile = File(...),
    target_id: Optional[str] = Form(None),
    identity_id: Optional[str] = Form(None),
    db: DBSession = Depends(get_db)
):
    try:
        content_bytes = await file.read()
        content_str = content_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    # Imports must always attach to the configured project target.
    is_invalid_target = not target_id or str(target_id).strip().lower() in ("none", "undefined", "null", "")
    if is_invalid_target:
        target = get_active_target_model(db)
        target_id = target.id
    else:
        target = db.query(Target).filter(Target.id == target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target not found")

    # 1. Parse HAR
    transactions_raw, warnings = parse_har_content(content_str)
    if not transactions_raw:
        raise HTTPException(status_code=400, detail="HAR contains no valid HTTP transactions")

    # 2. Group Session & Identity
    session_obj, db_transactions = process_and_group_session(
        db=db,
        target_id=target_id,
        transactions_raw=transactions_raw,
        explicit_identity_id=identity_id
    )

    # 3. Auto-match OpenAPI operations if spec exists
    spec = db.query(OpenAPISpec).filter(OpenAPISpec.target_id == target_id).first()
    if spec:
        from app.openapi.loader import match_transactions_to_operations
        match_transactions_to_operations(db, spec)

    # 4. Dependency Analysis
    analyze_session_dependencies(db, session_obj.id)

    # 5. Workflow State Graph Generation
    generate_workflow_state_graph(db, session_obj.id)

    return HARImportResult(
        target_id=target_id,
        session_id=session_obj.id,
        imported_count=len(db_transactions),
        skipped_count=len(warnings),
        warnings=warnings,
        transactions=db_transactions
    )


@router.post("/openapi", response_model=OpenAPISpecResponse)
async def import_openapi(
    file: UploadFile = File(...),
    target_id: Optional[str] = Form(None),
    db: DBSession = Depends(get_db)
):
    try:
        content_bytes = await file.read()
        content_str = content_bytes.decode("utf-8")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")

    is_invalid_target = not target_id or str(target_id).strip().lower() in ("none", "undefined", "null", "")
    if is_invalid_target:
        target = get_active_target_model(db)
        target_id = target.id
    elif not db.query(Target).filter(Target.id == target_id).first():
        raise HTTPException(status_code=404, detail="Target not found")

    spec_obj = load_and_save_openapi(db, target_id, content_str)
    return spec_obj
