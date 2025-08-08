"""Get pointing from ID endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.instrument import Instrument
from server.auth.auth import get_current_user

router = APIRouter(tags=["UI"])


@router.get("/ajax_pointingfromid")
async def get_pointing_fromID(
    id: str, db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """Get pointing details by ID for the current user's planned pointings."""
    from server.utils.function import isInt
    from server.db.models.gw_alert import GWAlert
    from server.db.models.pointing_event import PointingEvent
    from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum

    if not id or not isInt(id):
        raise HTTPException(status_code=400, detail="Invalid pointing ID format")

    # Convert to integer
    pointing_id = int(id)

    # First check if pointing exists at all
    pointing_exists = db.query(Pointing).filter(Pointing.id == pointing_id).first()

    if not pointing_exists:
        raise HTTPException(
            status_code=404, detail=f"Pointing with ID {pointing_id} does not exist"
        )

    # Check if it belongs to the current user
    if pointing_exists.submitterid != current_user.id:
        raise HTTPException(
            status_code=403,
            detail=f"Pointing {pointing_id} belongs to another user (ID: {pointing_exists.submitterid})",
        )

    # Check if it's in planned status
    if pointing_exists.status != pointing_status_enum.planned:
        raise HTTPException(
            status_code=400,
            detail=f"Pointing {pointing_id} has status '{pointing_exists.status.name}' but only 'planned' pointings can be pre-loaded",
        )

    pointing = pointing_exists

    # Get the alert for this pointing
    pointing_event = (
        db.query(PointingEvent).filter(PointingEvent.pointingid == pointing.id).first()
    )
    if not pointing_event:
        return {}

    alert = db.query(GWAlert).filter(GWAlert.graceid == pointing_event.graceid).first()
    if not alert:
        return {}

    # Extract position
    position_result = (
        db.query(func.ST_AsText(Pointing.position))
        .filter(Pointing.id == pointing_id)
        .first()
    )

    if not position_result or not position_result[0]:
        return {}

    position = position_result[0]
    ra = position.split("POINT(")[1].split(" ")[0]
    dec = position.split("POINT(")[1].split(" ")[1].split(")")[0]

    # Get instrument details
    instrument = (
        db.query(Instrument).filter(Instrument.id == pointing.instrumentid).first()
    )

    # Prepare response
    pointing_json = {
        "ra": ra,
        "dec": dec,
        "graceid": pointing_event.graceid,
        "instrument": f"{pointing.instrumentid}_{instrument.InstrumentType.name if instrument else ''}",
        "band": pointing.band.name if pointing.band else "",
        "depth": pointing.depth,
        "depth_err": pointing.depth_err,
    }

    return pointing_json
