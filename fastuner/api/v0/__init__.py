"""V0 API routes"""

from fastapi import APIRouter

from .datasets import router as datasets_router
from .finetune import router as finetune_router
from .inference import router as inference_router
from .deployments import router as deployments_router

router = APIRouter()

# Include sub-routers
router.include_router(datasets_router, prefix="/datasets", tags=["datasets"])
router.include_router(finetune_router, prefix="/fine-tune-jobs", tags=["fine-tune"])
router.include_router(deployments_router, prefix="/deployments", tags=["deployments"])
router.include_router(inference_router, prefix="/inference", tags=["inference"])


@router.get("/")
async def v0_root():
    """V0 API root endpoint"""
    return {
        "version": "v0",
        "endpoints": [
            "/v0/datasets",
            "/v0/fine-tune-jobs",
            "/v0/deployments",
            "/v0/inference",
        ],
    }
