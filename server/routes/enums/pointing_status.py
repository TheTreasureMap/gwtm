"""Pointing status enum endpoint."""

from fastapi import APIRouter
from typing import List

from server.core.enums.pointingstatus import PointingStatus
from server.schemas.enums import EnumOption, EnumResponse

router = APIRouter(tags=["enums"])


@router.get("/pointing_status", response_model=EnumResponse)
async def get_pointing_status_options():
    """
    Get all available pointing status options.

    Returns a list of all supported pointing statuses that indicate
    the current state of a pointing observation.
    """
    options = []

    # Create human-readable names and descriptions
    status_descriptions = {
        "planned": "Observation is planned but not yet executed",
        "completed": "Observation has been successfully completed",
        "cancelled": "Observation was cancelled and will not be executed",
    }

    status_display_names = {
        "planned": "Planned",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }

    for status in PointingStatus:
        options.append(
            EnumOption(
                name=status_display_names.get(status.name, status.name.title()),
                value=status.name,
                description=status_descriptions.get(
                    status.name, f"Status: {status.name}"
                ),
            )
        )

    return EnumResponse(enum_type="pointing_status", options=options)
