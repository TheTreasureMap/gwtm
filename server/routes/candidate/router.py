"""Consolidated router for all candidate endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .get_candidates import router as get_candidates_router
from .create_candidates import router as create_candidates_router
from .update_candidate import router as update_candidate_router
from .delete_candidates import router as delete_candidates_router

# Create the main router that includes all candidate routes
router = APIRouter(tags=["candidates"])

# Include all the individual routers
router.include_router(get_candidates_router)
router.include_router(create_candidates_router)
router.include_router(update_candidate_router)
router.include_router(delete_candidates_router)