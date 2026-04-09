from fastapi import APIRouter
from app.api.v1.api import api_router as v1_router

router = APIRouter()
router.include_router(v1_router, prefix="/api/v1")