"""Consolidated router for all GW galaxy endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .get_event_galaxies import router as get_event_galaxies_router
from .post_event_galaxies import router as post_event_galaxies_router
from .remove_event_galaxies import router as remove_event_galaxies_router
from .get_glade import router as get_glade_router

# Create the main router that includes all GW galaxy routes
router = APIRouter(tags=["galaxies"])

# Include all the individual routers
router.include_router(get_event_galaxies_router)
router.include_router(post_event_galaxies_router)
router.include_router(remove_event_galaxies_router)
router.include_router(get_glade_router)