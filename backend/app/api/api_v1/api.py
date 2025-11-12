from fastapi import APIRouter

from app.api.api_v1.endpoints import auth, documents, folders, health, sharing, users, integrations

router = APIRouter()

router.include_router(auth.router, prefix="/auth", tags=["authentication"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(folders.router, prefix="/folders", tags=["folders"])
router.include_router(sharing.router, prefix="/sharing", tags=["sharing"])
router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
