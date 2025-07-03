"""Consolidated router for all admin endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .fixdata import router as fixdata_router

# Create the main router that includes all admin routes
router = APIRouter(tags=["admin"])

# Include all the individual routers
router.include_router(fixdata_router)
