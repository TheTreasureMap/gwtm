"""Footprint type enum endpoint."""

from fastapi import APIRouter
from typing import List

from server.schemas.enums import EnumOption, EnumResponse

router = APIRouter(tags=["enums"])


@router.get("/footprint_type", response_model=EnumResponse)
async def get_footprint_type_options():
    """
    Get all available footprint type options.

    Returns a list of all supported footprint shape types for instruments.
    """
    options = []

    # Create human-readable names and descriptions
    type_descriptions = {
        "Rectangular": "Rectangular footprint with specified height and width",
        "Circular": "Circular footprint with specified radius",
        "Polygon": "Custom polygon footprint with user-defined vertices",
    }

    type_display_names = {
        "Rectangular": "Rectangular",
        "Circular": "Circular", 
        "Polygon": "Polygon",
    }

    footprint_types = ["Rectangular", "Circular", "Polygon"]
    
    for ftype in footprint_types:
        options.append(
            EnumOption(
                name=type_display_names.get(ftype, ftype),
                value=ftype,
                description=type_descriptions.get(
                    ftype, f"Footprint type: {ftype}"
                ),
            )
        )

    return EnumResponse(enum_type="footprint_type", options=options)