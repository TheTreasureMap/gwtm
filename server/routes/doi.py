import json

from fastapi import APIRouter, Depends, Request, Response, Body
from server.utils.error_handling import validation_exception, not_found_exception, permission_exception
from server.core.enums.pointing_status import pointing_status as pointing_status_enum
from sqlalchemy.orm import Session
from typing import List, Dict, Optional

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.instrument import Instrument
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_alert import GWAlert
from server.db.models.users import Users
from server.db.models.doi_author import DOIAuthor, DOIAuthorGroup
from server.auth.auth import get_current_user
from server.schemas.doi import (
    DOIAuthorSchema,
    DOIAuthorGroupSchema,
    DOIPointingInfo,
    DOIPointingsResponse,
    DOIRequestResponse
)
from server.utils.function import create_pointing_doi

router = APIRouter(tags=["DOI"])



@router.get("/doi_pointings", response_model=DOIPointingsResponse)
async def get_doi_pointings(
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Get all pointings with DOIs requested by the current user.

    Returns:
    - List of pointings with DOI information
    """
    # Query pointings with DOIs, ensuring we only get pointings that actually have DOI information
    pointings = db.query(Pointing).filter(
        Pointing.submitterid == user.id,
        Pointing.doi_id.isnot(None),  # Changed from != None to .isnot(None) for proper SQLAlchemy syntax
        Pointing.doi_url.isnot(None)   # Also check that doi_url is not None
    ).all()

    result = []
    for pointing in pointings:
        # Get event information - need to join with PointingEvent to get graceid
        pointing_events = db.query(PointingEvent).filter(PointingEvent.pointingid == pointing.id).all()
        graceid = pointing_events[0].graceid if pointing_events else "Unknown"

        # Get instrument information
        instrument = db.query(Instrument).filter(Instrument.id == pointing.instrumentid).first()
        instrument_name = instrument.instrument_name if instrument else "Unknown"

        # Convert status enum to string if needed
        status_str = pointing.status.name if hasattr(pointing.status, 'name') else str(pointing.status)

        result.append(DOIPointingInfo(
            id=pointing.id,
            graceid=graceid,
            instrument_name=instrument_name,
            status=status_str,
            doi_url=pointing.doi_url,
            doi_id=pointing.doi_id
        ))

    return DOIPointingsResponse(pointings=result)

@router.get("/doi_author_groups", response_model=List[DOIAuthorGroupSchema])
async def get_doi_author_groups(
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Get all DOI author groups for the current user.

    Returns:
    - List of DOI author groups
    """
    groups = db.query(DOIAuthorGroup).filter(DOIAuthorGroup.userid == user.id).all()
    return groups


@router.get("/doi_authors/{group_id}", response_model=List[DOIAuthorSchema])
async def get_doi_authors(
        group_id: int,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Get all DOI authors for a specific group.

    Parameters:
    - group_id: DOI author group ID

    Returns:
    - List of DOI authors
    """
    # First check if the group belongs to the user
    group = db.query(DOIAuthorGroup).filter(
        DOIAuthorGroup.id == group_id,
        DOIAuthorGroup.userid == user.id
    ).first()

    if not group:
        raise permission_exception("You don't have permission to access this DOI author group")

    authors = db.query(DOIAuthor).filter(DOIAuthor.author_groupid == group_id).all()
    return authors
