"""
Health check router.
"""
from fastapi import APIRouter
from sqlalchemy import text

router = APIRouter(tags=["Health"])


@router.get("/", summary="Health check")
def health_check():
    return {"status": "ok", "service": "VetCoreSoft Cloud API"}


@router.get("/health", summary="Detailed health check")
def health_detail():
    from core.database import engine
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_ok = True
    except Exception:
        pass
    return {"status": "ok" if db_ok else "degraded", "database": "connected" if db_ok else "unreachable"}

