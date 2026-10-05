import os
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
def health_check(db: Session = Depends(get_db)):
    """
    Application health status and database connectivity check.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "app_name": settings.APP_NAME,
        "environment": settings.APP_ENV,
        "database": db_status,
        "embedding_provider": settings.EMBEDDING_PROVIDER,
        "llm_provider": settings.LLM_PROVIDER,
    }
