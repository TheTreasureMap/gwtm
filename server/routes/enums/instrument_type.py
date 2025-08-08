"""Instrument type enum endpoint."""

from fastapi import APIRouter
from typing import List

from server.core.enums.instrumenttype import InstrumentType
from server.schemas.enums import EnumOption, EnumResponse

router = APIRouter(tags=["enums"])


@router.get("/instrument_type", response_model=EnumResponse)
async def get_instrument_type_options():
    """
    Get all available instrument type options.

    Returns a list of all supported instrument types that categorize
    telescopes and observing instruments.
    """
    options = []

    # Create human-readable names and descriptions
    type_descriptions = {
        "photometric": "Photometric instruments measure brightness and colors of astronomical objects",
        "spectroscopic": "Spectroscopic instruments analyze the spectrum of light from astronomical objects",
    }

    type_display_names = {
        "photometric": "Photometric",
        "spectroscopic": "Spectroscopic",
    }

    for inst_type in InstrumentType:
        options.append(
            EnumOption(
                name=type_display_names.get(inst_type.name, inst_type.name.title()),
                value=inst_type.name,
                description=type_descriptions.get(
                    inst_type.name, f"Instrument type: {inst_type.name}"
                ),
            )
        )

    return EnumResponse(enum_type="instrument_type", options=options)
