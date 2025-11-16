from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api import deps
from app.api.api_v1.api import router as api_v1_router
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware
from app.db.dynamodb_session import DynamoDBSession


def create_application() -> FastAPI:
    """Create and configure the FastAPI application."""
    # Initialize logging
    setup_logging()

    # Create FastAPI app
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        version="1.0.0",
        docs_url=None if settings.ENVIRONMENT == "production" else "/docs",
        redoc_url=None if settings.ENVIRONMENT == "production" else "/redoc",
    )

    # Setup exception handlers
    setup_exception_handlers(app)

    # CORS configuration - allowing all origins as CORS will be handled by API Gateway
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Setup other middlewares
    setup_middleware(app)

    # Include API router
    app.include_router(api_v1_router, prefix=settings.API_V1_STR)

    # Root endpoint for health checks
    @app.get("/")
    async def root():
        """Health check endpoint"""
        return JSONResponse(
            content={"message": "Data Room API is running", "version": "1.0.0"},
            status_code=200,
        )

    # Additional health endpoints directly at the root level
    @app.get("/health")
    async def health_check():
        """Basic health check endpoint"""
        return {
            "status": "healthy",
            "api_version": "1.0.0",
            "environment": settings.ENVIRONMENT,
        }

    @app.get("/health/detailed")
    async def detailed_health_check(db: DynamoDBSession = Depends(deps.get_db)):
        """Detailed health check that validates database connectivity"""
        # Check database connectivity
        try:
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

    return app


# Create the app instance
app = create_application()

# This file is run using UV from the run script, no need for the uvicorn entry point here
if __name__ == "__main__":
    # Allows for direct execution using `python -m app.main`
    import subprocess

    subprocess.run(
        ["uv", "run", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
    )
