"""Consolidated router for all UI endpoints."""

from datetime import datetime
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

# Temporary import for sun/moon calculation
try:
    import astropy.time
    from astropy.coordinates import get_body

    ASTROPY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Astropy not available: {e}")
    ASTROPY_AVAILABLE = False

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


# Temporary sun/moon position endpoint for testing
class TempSunMoonPositions(BaseModel):
    """Temporary sun and moon positions response model."""

    sun_ra: float
    sun_dec: float
    moon_ra: float
    moon_dec: float
    time_of_signal: str


@router.get("/temp_sun_moon_positions", response_model=TempSunMoonPositions)
async def temp_get_sun_moon_positions(
    time_of_signal: str = Query(
        ..., description="ISO timestamp of the gravitational wave signal"
    )
):
    """Temporary endpoint for sun/moon positions until main celestial router is working."""
    if not ASTROPY_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Astropy library not available for celestial calculations",
        )

    try:
        # Parse the input timestamp
        if time_of_signal.endswith("Z"):
            dt = datetime.fromisoformat(time_of_signal[:-1])
        else:
            dt = datetime.fromisoformat(time_of_signal)

        # Convert to Astropy Time object
        t = astropy.time.Time(dt, format="datetime", scale="utc")

        # Get sun and moon positions
        sun = get_body("sun", t)
        moon = get_body("moon", t)

        return TempSunMoonPositions(
            sun_ra=sun.ra.deg,
            sun_dec=sun.dec.deg,
            moon_ra=moon.ra.deg,
            moon_dec=moon.dec.deg,
            time_of_signal=time_of_signal,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid time format: {str(e)}")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate positions: {str(e)}"
        )
