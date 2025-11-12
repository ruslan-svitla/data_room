from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.api_v1.api import router as api_v1_router
from app.core.config import settings
from app.core.errors import setup_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import setup_middleware


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

    # Setup middlewares
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
