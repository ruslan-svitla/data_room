from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.api import deps
from app.core.config import settings

router = APIRouter()


@router.get("/", summary="Health check")
async def health_check():
    """
    Health check endpoint for the API.

    Returns basic information about the application status.
    """
    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
    }


@router.get("/detailed", summary="Detailed health check")
async def detailed_health_check(db: AsyncSession = Depends(deps.get_db)):
    """
    Detailed health check that validates database connectivity.

    Returns extended information about system health.
    """
    # Check database connectivity
    try:
        # Execute a simple query to check database connection
        result = await db.execute(text("SELECT 1"))
        db_status = "connected" if result.scalar() == 1 else "error"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "api_version": "1.0.0",
        "environment": settings.ENVIRONMENT,
        "database": db_status,
        "settings": {
            "debug": settings.DEBUG,
            "project_name": settings.PROJECT_NAME,
        },
    }
