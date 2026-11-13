from fastapi import APIRouter
from fastapi.responses import JSONResponse
from starlette import status
from app.db import check_db_ready

router = APIRouter(tags=["health"])


@router.get("/health")
def liveness():
    """Liveness probe - always 200, no DB call."""
    return {"status": "ok"}


@router.get("/ready")
def readiness():
    """Readiness probe - runs SELECT 1; returns 503 if DB is unreachable."""
    if check_db_ready():
        return {"status": "ready"}
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"status": "unavailable"},
    )
