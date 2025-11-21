"""Get DOI pointings endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.instrument import Instrument
from server.db.models.pointing_event import PointingEvent
from server.auth.auth import get_current_user
from server.schemas.doi import DOIPointingInfo, DOIPointingsResponse

router = APIRouter(tags=["DOI"])


@router.get("/doi_pointings", response_model=DOIPointingsResponse)
async def get_doi_pointings(
    db: Session = Depends(get_db), user=Depends(get_current_user)
):
    """
    Get all pointings with DOIs requested by the current user.

    Returns:
    - List of pointings with DOI information
    """
    # Query pointings with DOIs, ensuring we only get pointings that actually have DOI information
    pointings = (
        db.query(Pointing)
        .filter(
            Pointing.submitterid == user.id,
            Pointing.doi_id.isnot(
                None
            ),  # Changed from != None to .isnot(None) for proper SQLAlchemy syntax
            Pointing.doi_url.isnot(None),  # Also check that doi_url is not None
        )
        .all()
    )

    result = []
    for pointing in pointings:
        # Get event information - need to join with PointingEvent to get graceid
        pointing_events = (
            db.query(PointingEvent)
            .filter(PointingEvent.pointingid == pointing.id)
            .all()
        )
        graceid = pointing_events[0].graceid if pointing_events else "Unknown"

        # Get instrument information
        instrument = (
            db.query(Instrument).filter(Instrument.id == pointing.instrumentid).first()
        )
        instrument_name = instrument.instrument_name if instrument else "Unknown"

        # Convert status enum to string if needed
        status_str = (
            pointing.status.name
            if hasattr(pointing.status, "name")
            else str(pointing.status)
        )

        result.append(
            DOIPointingInfo(
                id=pointing.id,
                graceid=graceid,
                instrument_name=instrument_name,
                status=status_str,
                doi_url=pointing.doi_url,
                doi_id=pointing.doi_id,
            )
        )

    return DOIPointingsResponse(pointings=result)
