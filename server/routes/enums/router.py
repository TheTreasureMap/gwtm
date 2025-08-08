"""Consolidated router for all enum endpoints."""

from fastapi import APIRouter
from typing import Dict, List

from server.schemas.enums import EnumOption, AllEnumsResponse
from server.core.enums.bandpass import Bandpass
from server.core.enums.depthunit import DepthUnit
from server.core.enums.pointingstatus import PointingStatus
from server.core.enums.instrumenttype import InstrumentType

# Import individual routers
from .bandpass import router as bandpass_router
from .depth_unit import router as depth_unit_router
from .pointing_status import router as pointing_status_router
from .instrument_type import router as instrument_type_router

# Create main enums router
router = APIRouter(prefix="/enums", tags=["enums"])

# Include individual enum routers
router.include_router(bandpass_router)
router.include_router(depth_unit_router)
router.include_router(pointing_status_router)
router.include_router(instrument_type_router)


def _get_bandpass_options() -> List[EnumOption]:
    """Get bandpass options (shared logic)."""
    options = []
    for bandpass in Bandpass:
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
    return options


def _get_depth_unit_options() -> List[EnumOption]:
    """Get depth unit options (shared logic)."""
    options = []
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
    return options


def _get_pointing_status_options() -> List[EnumOption]:
    """Get pointing status options (shared logic)."""
    options = []
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
    return options


def _get_instrument_type_options() -> List[EnumOption]:
    """Get instrument type options (shared logic)."""
    options = []
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
    return options


@router.get("/all", response_model=AllEnumsResponse)
async def get_all_enums():
    """
    Get all enum options in a single request.

    This endpoint returns all enum types and their options in one response,
    which can be more efficient for applications that need multiple enum types.
    """
    return AllEnumsResponse(
        enums={
            "bandpass": _get_bandpass_options(),
            "depth_unit": _get_depth_unit_options(),
            "pointing_status": _get_pointing_status_options(),
            "instrument_type": _get_instrument_type_options(),
        }
    )
