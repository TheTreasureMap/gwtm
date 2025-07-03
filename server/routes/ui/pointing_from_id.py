"""Get pointing from ID endpoint."""

from fastapi import APIRouter, Depends
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
        return {}

    # Convert to integer
    pointing_id = int(id)

    # Query pointings with filter conditions
    filters = [
        Pointing.submitterid == current_user.id,
        Pointing.status == pointing_status_enum.planned,
        Pointing.id == pointing_id,
    ]

    pointing = db.query(Pointing).filter(*filters).first()

    if not pointing:
        return {}

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
