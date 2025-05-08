from fastapi import APIRouter
from .admin import router as admin_router
from .candidate import router as candidate_router
from .doi import router as doi_router
from .event import router as event_router
from .gw_galaxy import router as galaxy_router
from .gw_alert import router as gw_alert_router
from .icecube import router as icecube_router
from .instrument import router as instrument_router
from .pointing import router as pointing_router
from .ui import router as ui_router


router = APIRouter()

# Include all routers
router.include_router(pointing_router)
router.include_router(event_router)
router.include_router(doi_router)
router.include_router(gw_alert_router)
router.include_router(admin_router)
router.include_router(instrument_router)
router.include_router(galaxy_router)
router.include_router(icecube_router)
router.include_router(candidate_router)


# UI routes don't get the API prefix, they're handled separately in main.py
