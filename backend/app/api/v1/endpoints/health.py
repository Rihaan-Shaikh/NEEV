from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import logging
from app.db.session import get_db

logger = logging.getLogger("neev.health")
router = APIRouter()

@router.get("/live")
async def health_live():
    return {"status": "live", "service": "NEEV Core API"}

@router.get("/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {
            "status": "ready",
            "service": "NEEV Core API",
            "database": "connected",
            "environment": "operational"
        }
    except Exception as e:
        logger.error(f"PostgreSQL readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database readiness check failed: unable to reach PostgreSQL database."
        )
