"""Consolidated router for all pointing endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .create_pointings import router as create_pointings_router
from .get_pointings import router as get_pointings_router
from .update_pointings import router as update_pointings_router
from .cancel_all import router as cancel_all_router
from .request_doi import router as request_doi_router
from .test_refactoring import router as test_refactoring_router

# Create the main router that includes all pointing routes
router = APIRouter(tags=["pointings"])

# Include all the individual routers
router.include_router(create_pointings_router)
router.include_router(get_pointings_router)
router.include_router(update_pointings_router)
router.include_router(cancel_all_router)
router.include_router(request_doi_router)
router.include_router(test_refactoring_router)