"""Sun and moon position calculations using Astropy."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

try:
    import astropy.time
    from astropy.coordinates import get_body

    ASTROPY_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Astropy not available: {e}")
    ASTROPY_AVAILABLE = False

router = APIRouter(tags=["celestial"])


@router.get("/test_celestial")
async def test_celestial():
    """Test endpoint to verify celestial router is working."""
    return {
        "message": "Celestial router is working",
        "astropy_available": ASTROPY_AVAILABLE,
    }


class SunMoonPositions(BaseModel):
    """Sun and moon positions response model."""

    sun_ra: float
    sun_dec: float
    moon_ra: float
    moon_dec: float
    time_of_signal: str


@router.get("/sun_moon_positions", response_model=SunMoonPositions)
async def get_sun_moon_positions(
    time_of_signal: str = Query(
        ..., description="ISO timestamp of the gravitational wave signal"
    )
):
    """
    Get sun and moon positions at the time of a gravitational wave signal.

    Uses the same Astropy calculation as the Flask version for consistency.

    Parameters:
    - time_of_signal: ISO timestamp string (e.g., "2019-04-25T08:18:26.000000Z")

    Returns:
    - sun_ra: Sun right ascension in degrees
    - sun_dec: Sun declination in degrees
    - moon_ra: Moon right ascension in degrees
    - moon_dec: Moon declination in degrees
    - time_of_signal: Original timestamp for reference
    """
    # Check if Astropy is available
    if not ASTROPY_AVAILABLE:
        raise HTTPException(
            status_code=500,
            detail="Astropy library not available for celestial calculations",
        )

    try:
        # Parse the input timestamp - handle various formats
        if time_of_signal.endswith("Z"):
            # Remove Z suffix and parse
            dt = datetime.fromisoformat(time_of_signal[:-1])
        else:
            dt = datetime.fromisoformat(time_of_signal)

        # Convert to Astropy Time object (exactly like Flask version)
        t = astropy.time.Time(dt, format="datetime", scale="utc")

        # Get sun position (exactly like Flask version)
        sun = get_body("sun", t)
        sun_ra = sun.ra.deg
        sun_dec = sun.dec.deg

        # Get moon position (exactly like Flask version)
        moon = get_body("moon", t)
        moon_ra = moon.ra.deg
        moon_dec = moon.dec.deg

        return SunMoonPositions(
            sun_ra=sun_ra,
            sun_dec=sun_dec,
            moon_ra=moon_ra,
            moon_dec=moon_dec,
            time_of_signal=time_of_signal,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid time format: {time_of_signal}. Expected ISO format like '2019-04-25T08:18:26.000000Z'",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to calculate celestial positions: {str(e)}"
        )
