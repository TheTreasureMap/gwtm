"""Consolidated router for all instrument endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .get_instruments import router as get_instruments_router
from .get_footprints import router as get_footprints_router
from .create_instrument import router as create_instrument_router
from .create_footprint import router as create_footprint_router

# Create the main router that includes all instrument routes
router = APIRouter(tags=["instruments"])

# Include all the individual routers
router.include_router(get_instruments_router)
router.include_router(get_footprints_router)
router.include_router(create_instrument_router)
router.include_router(create_footprint_router)