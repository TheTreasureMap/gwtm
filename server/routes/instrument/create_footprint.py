"""Create footprint endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from geoalchemy2 import WKBElement
from shapely.wkb import loads as wkb_loads

from server.db.database import get_db
from server.db.models.instrument import Instrument, FootprintCCD
from server.schemas.instrument import FootprintCCDCreate, FootprintCCDSchema
from server.auth.auth import get_current_user
from server.utils.error_handling import not_found_exception, permission_exception

router = APIRouter(tags=["instruments"])


@router.post("/footprints", response_model=FootprintCCDSchema)
async def create_footprint(
    footprint: FootprintCCDCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Create a new footprint for an instrument.

    Parameters:
    - footprint: Footprint data

    Returns the created footprint
    """
    # Check if the instrument exists
    instrument = (
        db.query(Instrument).filter(Instrument.id == footprint.instrumentid).first()
    )
    if not instrument:
        raise not_found_exception(
            f"Instrument with ID {footprint.instrumentid} not found"
        )

    # Check permissions (only the instrument submitter can add footprints)
    if instrument.submitterid != user.id:
        raise permission_exception(
            "You don't have permission to add footprints to this instrument"
        )

    # Create a new footprint
    new_footprint = FootprintCCD(
        instrumentid=footprint.instrumentid, footprint=footprint.footprint  # WKT format
    )

    db.add(new_footprint)
    db.commit()
    db.refresh(new_footprint)

    # Convert the footprint from WKB to WKT for the response
    if isinstance(new_footprint.footprint, WKBElement):
        new_footprint.footprint = str(wkb_loads(bytes(new_footprint.footprint.data)))

    return new_footprint
