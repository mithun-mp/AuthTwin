from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check():
    return {
        "status": "healthy",
        "service": "AuthTwin Backend",
        "milestone": "Milestone 1 — Workflow Reconstruction Foundation"
    }
