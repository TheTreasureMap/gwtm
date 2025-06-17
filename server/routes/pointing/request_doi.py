"""Request DOI for pointings endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_alert import GWAlert
from server.schemas.pointing import DOIRequest
from server.schemas.doi import DOIRequestResponse
from server.auth.auth import get_current_user
from server.utils.error_handling import validation_exception
from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum
from server.utils import pointing as pointing_utils

router = APIRouter(tags=["pointings"])


@router.post("/request_doi", response_model=DOIRequestResponse)
async def request_doi(
        request: DOIRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Request a DOI for completed pointings.
    """
    # Build the filter for pointings
    filter_conditions = [
        Pointing.submitterid == user.id
    ]

    # Handle id or ids (these don't require PointingEvent join)
    if request.id:
        filter_conditions.append(Pointing.id == request.id)
    elif request.ids:
        filter_conditions.append(Pointing.id.in_(request.ids))

    # Only join with PointingEvent if graceid is specified
    if request.graceid:
        normalized_graceid = GWAlert.graceidfromalternate(request.graceid)
        # Query the pointings with explicit join
        points = db.query(Pointing).join(
            PointingEvent, Pointing.id == PointingEvent.pointingid
        ).filter(
            *filter_conditions,
            PointingEvent.graceid == normalized_graceid
        ).all()
    else:
        # Query without join when only using ID filters
        points = db.query(Pointing).filter(*filter_conditions).all()

    # Validate and prepare for DOI request
    warnings = []
    doi_points = []

    for p in points:
        # Check if pointing is completed and doesn't already have a DOI
        if p.status == pointing_status_enum.completed and p.doi_id is None:
            doi_points.append(p)
        else:
            warning_msg = f"Invalid doi request for pointing: {p.id}"
            if p.status != pointing_status_enum.completed:
                warning_msg += f" (status: {p.status})"
            if p.doi_id is not None:
                warning_msg += " (already has DOI)"
            warnings.append(warning_msg)

    if len(doi_points) == 0:
        raise validation_exception(
            message="No valid pointings found for DOI request",
            errors=["All pointings must be completed and not already have a DOI"]
        )

    # Get the GW event IDs from the pointings
    pointing_events = db.query(PointingEvent).filter(
        PointingEvent.pointingid.in_([x.id for x in doi_points])
    ).all()
    gids = list(set([pe.graceid for pe in pointing_events]))

    if len(gids) > 1:
        raise validation_exception(
            message="Multiple events detected",
            errors=["Pointings must be only for a single GW event for a DOI request"]
        )

    gid = gids[0]

    # Prepare DOI creators
    creators = pointing_utils.prepare_doi_creators(
        request.creators, request.doi_group_id, user, db
    )

    # Create or use provided DOI
    if request.doi_url:
        doi_id, doi_url = 0, request.doi_url
    else:
        doi_id, doi_url = pointing_utils.create_doi_for_pointings(
            doi_points, gid, creators, db
        )

    # Update pointing records with DOI information
    if doi_id is not None:
        for p in doi_points:
            p.doi_url = doi_url
            p.doi_id = doi_id

        db.commit()

    return DOIRequestResponse(DOI_URL=doi_url, WARNINGS=warnings)
