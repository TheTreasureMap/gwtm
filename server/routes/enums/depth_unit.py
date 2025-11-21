"""Depth unit enum endpoint."""

from fastapi import APIRouter
from typing import List

from server.core.enums.depthunit import DepthUnit
from server.schemas.enums import EnumOption, EnumResponse

router = APIRouter(tags=["enums"])


@router.get("/depth_unit", response_model=EnumResponse)
async def get_depth_unit_options():
    """
    Get all available depth unit options.

    Returns a list of all supported depth units that can be used
    when specifying observation depth measurements.
    """
    options = []

    # Create human-readable names and descriptions
    unit_descriptions = {
        "ab_mag": "AB Magnitude - Standard astronomical magnitude system",
        "vega_mag": "Vega Magnitude - Magnitude system referenced to Vega",
        "flux_erg": "Flux (erg/cm²/s) - Energy flux in CGS units",
        "flux_jy": "Flux (Jy) - Flux density in Janskys",
    }

    unit_display_names = {
        "ab_mag": "AB Magnitude",
        "vega_mag": "Vega Magnitude",
        "flux_erg": "Flux (erg/cm²/s)",
        "flux_jy": "Flux (Jy)",
    }

    for unit in DepthUnit:
        options.append(
            EnumOption(
                name=unit_display_names.get(unit.name, unit.name),
                value=unit.name,
                description=unit_descriptions.get(
                    unit.name, f"Depth unit: {unit.name}"
                ),
            )
        )

    return EnumResponse(enum_type="depth_unit", options=options)
