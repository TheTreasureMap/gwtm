"""Get footprints endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
from geoalchemy2 import WKBElement
from shapely.wkb import loads as wkb_loads

from server.db.database import get_db
from server.db.models.instrument import Instrument, FootprintCCD
from server.schemas.instrument import FootprintCCDSchema
from server.auth.auth import get_current_user

router = APIRouter(tags=["instruments"])


@router.get("/footprints", response_model=List[FootprintCCDSchema])
async def get_footprints(
    id: Optional[int] = None,
    name: Optional[str] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get instrument footprints with optional filters.

    Parameters:
    - id: Filter by instrument ID
    - name: Filter by instrument name (fuzzy match)

    Returns a list of footprint objects
    """
    filter_conditions = []

    if id:
        filter_conditions.append(FootprintCCD.instrumentid == id)

    if name:
        filter_conditions.append(FootprintCCD.instrumentid == Instrument.id)

        or_conditions = []
        or_conditions.append(Instrument.instrument_name.contains(name.strip()))
        or_conditions.append(Instrument.nickname.contains(name.strip()))

        filter_conditions.append(or_(*or_conditions))

        # When filtering by name, we need to join with Instrument table
        footprints = (
            db.query(FootprintCCD)
            .join(Instrument, FootprintCCD.instrumentid == Instrument.id)
            .filter(*filter_conditions)
            .all()
        )
    else:
        footprints = db.query(FootprintCCD).filter(*filter_conditions).all()

    # Convert WKB to WKT for the `footprint` field
    for footprint in footprints:
        if isinstance(footprint.footprint, WKBElement):
            footprint.footprint = str(wkb_loads(bytes(footprint.footprint.data)))

    # FastAPI will automatically convert SQLAlchemy models to Pydantic models
    return footprints
