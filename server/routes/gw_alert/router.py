"""Consolidated router for all GW alert endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .query_alerts import router as query_alerts_router
from .post_alert import router as post_alert_router
from .get_skymap import router as get_skymap_router
from .get_contour import router as get_contour_router
from .get_grb_moc import router as get_grb_moc_router
from .delete_test_alerts import router as delete_test_alerts_router

# Create the main router that includes all GW alert routes
router = APIRouter(tags=["gw_alerts"])

# Include all the individual routers
router.include_router(query_alerts_router)
router.include_router(post_alert_router)
router.include_router(get_skymap_router)
router.include_router(get_contour_router)
router.include_router(get_grb_moc_router)
router.include_router(delete_test_alerts_router)