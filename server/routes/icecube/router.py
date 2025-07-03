"""Consolidated router for all IceCube endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .post_icecube_notice import router as post_icecube_notice_router

# Create the main router that includes all IceCube routes
router = APIRouter(tags=["icecube"])

# Include all the individual routers
router.include_router(post_icecube_notice_router)
