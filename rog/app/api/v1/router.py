from fastapi import APIRouter

from rog.app.api.v1.auth import router as auth_router
from rog.app.api.v1.orgs import router as orgs_router

router = APIRouter()
router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(orgs_router, prefix="/orgs", tags=["orgs"])

