"""Consolidated router for all event endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .get_candidate_events import router as get_candidate_events_router
from .create_candidate_event import router as create_candidate_event_router
from .update_candidate_event import router as update_candidate_event_router
from .delete_candidate_event import router as delete_candidate_event_router

# Create the main router that includes all event routes
router = APIRouter(tags=["Events"])

# Include all the individual routers
router.include_router(get_candidate_events_router)
router.include_router(create_candidate_event_router)
router.include_router(update_candidate_event_router)
router.include_router(delete_candidate_event_router)