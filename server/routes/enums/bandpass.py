"""Bandpass enum endpoint."""

from fastapi import APIRouter
from typing import List

from server.core.enums.bandpass import Bandpass
from server.schemas.enums import EnumOption, EnumResponse

router = APIRouter(tags=["enums"])


@router.get("/bandpass", response_model=EnumResponse)
async def get_bandpass_options():
    """
    Get all available bandpass options.

    Returns a list of all supported bandpass filters that can be used
    when submitting pointing observations.
    """
    options = []

    for bandpass in Bandpass:
        # Create human-readable names for some special cases
        display_name = {
            "i": "i (lowercase)",
            "I": "I (uppercase)",
            "UVW1": "UV W1",
            "UVW2": "UV W2",
            "UVM2": "UV M2",
            "XRT": "X-ray Telescope",
            "UHF": "Ultra High Frequency",
            "VHF": "Very High Frequency",
        }.get(bandpass.name, bandpass.name)

        options.append(
            EnumOption(
                name=display_name,
                value=bandpass.name,
                description=f"Bandpass filter: {bandpass.name}",
            )
        )

    return EnumResponse(enum_type="bandpass", options=options)
