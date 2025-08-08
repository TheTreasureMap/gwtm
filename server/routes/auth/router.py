"""Authentication router configuration."""

from fastapi import APIRouter
from .login import router as login_router

# Create main auth router
router = APIRouter(prefix="/auth")

# Include sub-routers
router.include_router(login_router)