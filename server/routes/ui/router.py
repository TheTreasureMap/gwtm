"""Consolidated router for all UI endpoints."""

from fastapi import APIRouter

# Import all individual route modules
from .alert_instruments_footprints import router as alert_instruments_footprints_router
from .preview_footprint import router as preview_footprint_router
from .resend_verification_email import router as resend_verification_email_router
from .coverage_calculator import router as coverage_calculator_router
from .spectral_range_from_bands import router as spectral_range_from_bands_router
from .pointing_from_id import router as pointing_from_id_router
from .grade_calculator import router as grade_calculator_router
from .icecube_notice import router as icecube_notice_router
from .event_galaxies import router as event_galaxies_router
from .scimma_xrt import router as scimma_xrt_router
from .candidate_fetch import router as candidate_fetch_router
from .request_doi import router as request_doi_router
from .alert_type import router as alert_type_router

# Create the main router that includes all UI routes
router = APIRouter(tags=["UI"])

# Include all the individual routers
router.include_router(alert_instruments_footprints_router)
router.include_router(preview_footprint_router)
router.include_router(resend_verification_email_router)
router.include_router(coverage_calculator_router)
router.include_router(spectral_range_from_bands_router)
router.include_router(pointing_from_id_router)
router.include_router(grade_calculator_router)
router.include_router(icecube_notice_router)
router.include_router(event_galaxies_router)
router.include_router(scimma_xrt_router)
router.include_router(candidate_fetch_router)
router.include_router(request_doi_router)
router.include_router(alert_type_router)