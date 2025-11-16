import logging

from fastapi import APIRouter, Depends
from loguru import logger

from app.api import deps
from app.core.config import settings
from app.db.dynamodb_session import DynamoDBSession

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
async def detailed_health_check(db: DynamoDBSession = Depends(deps.get_db)):
    """
    Detailed health check that validates database connectivity.

    Returns extended information about system health.
    """
    # Check database connectivity
    try:
        # Check DynamoDB connectivity by attempting to list tables
        # or access a known table to verify connection
        tables = list(db.dynamodb.tables.all())
        db_status = "connected" if tables else "no tables found but connected"
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
