"""Footprint unit enum endpoint."""

from fastapi import APIRouter
from typing import List

from server.schemas.enums import EnumOption, EnumResponse

router = APIRouter(tags=["enums"])


@router.get("/footprint_unit", response_model=EnumResponse)
async def get_footprint_unit_options():
    """
    Get all available footprint unit options.

    Returns a list of all supported units for specifying footprint dimensions.
    """
    options = []

    # Create human-readable names and descriptions
    unit_descriptions = {
        "deg": "Degrees - Standard angular measurement",
        "arcmin": "Arc Minutes - 1/60th of a degree",
        "arcsec": "Arc Seconds - 1/3600th of a degree",
    }

    unit_display_names = {
        "deg": "Degrees",
        "arcmin": "Arc Minutes",
        "arcsec": "Arc Seconds",
    }

    footprint_units = ["deg", "arcmin", "arcsec"]
    
    for unit in footprint_units:
        options.append(
            EnumOption(
                name=unit_display_names.get(unit, unit),
                value=unit,
                description=unit_descriptions.get(
                    unit, f"Footprint unit: {unit}"
                ),
            )
        )

    return EnumResponse(enum_type="footprint_unit", options=options)