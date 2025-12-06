"""Main FastAPI application"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import logging

from fastuner.config import get_settings
from fastuner.api.v0 import router as v0_router

settings = get_settings()

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Fastuner API",
    description="One-Click Model Deployment & Fine-Tuning Service for AWS SageMaker",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if not settings.is_production else "An error occurred",
        },
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "Fastuner API",
        "version": "0.1.0",
        "status": "running",
        "environment": settings.environment,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


# Include API routers
app.include_router(v0_router, prefix="/v0", tags=["v0"])


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "fastuner.api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production,
        workers=settings.api_workers if settings.is_production else 1,
    )
