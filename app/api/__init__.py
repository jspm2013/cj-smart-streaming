from fastapi import APIRouter
from . import admin, stream, tokens, health

router = APIRouter()
router.include_router(admin.router, prefix="/admin")
router.include_router(stream.router, prefix="/hls")
router.include_router(tokens.router, prefix="/api")
router.include_router(health.router)