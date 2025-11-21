"""Cancel all pointings endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_alert import GWAlert
from server.schemas.pointing import CancelAllRequest
from server.auth.auth import get_current_user
from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum
from server.utils import pointing as pointing_utils

router = APIRouter(tags=["pointings"])


@router.post("/cancel_all")
async def cancel_all(
    request: CancelAllRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Cancel all planned pointings for a specific GW event and instrument.
    """
    # Validate instrument exists
    pointing_utils.validate_instrument(request.instrumentid, db)

    # Validate graceid exists
    normalized_graceid = GWAlert.graceidfromalternate(request.graceid)

    # Build the filter
    filter_conditions = [
        Pointing.status == pointing_status_enum.planned,
        Pointing.submitterid == user.id,
        Pointing.instrumentid == request.instrumentid,
        Pointing.id == PointingEvent.pointingid,
        PointingEvent.graceid == normalized_graceid,
    ]

    # Query the pointings
    pointings = db.query(Pointing).filter(*filter_conditions)
    pointing_count = pointings.count()

    # Update the status
    for pointing in pointings:
        pointing.status = pointing_status_enum.cancelled
        pointing.dateupdated = datetime.now()

    db.commit()

    return {"message": f"Updated {pointing_count} Pointings successfully"}
