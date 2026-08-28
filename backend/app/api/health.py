from fastapi import APIRouter
router = APIRouter()
@router.get("/health")
def health_check():
    return {"status": "healthy"}
@router.get("/ready")
def ready_check():
    return {"status": "ready"}