"""Request DOI endpoint."""

from typing import Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.instrument import Instrument
from server.db.models.users import Users
from server.auth.auth import get_current_user

router = APIRouter(tags=["UI"])


@router.get("/ajax_request_doi")
async def ajax_request_doi(
    graceid: str,
    ids: str = "",
    doi_group_id: Optional[str] = None,
    doi_url: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Request a DOI for a set of pointings."""
    from server.utils.function import create_pointing_doi
    from server.db.models.gw_alert import GWAlert
    from server.db.models.pointing_event import PointingEvent

    # Normalize the graceid - maintain backward compatibility
    normalized_graceid = GWAlert.alternatefromgraceid(graceid)

    if not ids:
        return ""

    # Convert IDs to list of integers
    pointing_ids = [int(x) for x in ids.split(",")]

    # Get all pointings with these IDs that are associated with the graceid
    points = (
        db.query(Pointing)
        .join(PointingEvent, PointingEvent.pointingid == Pointing.id)
        .filter(
            Pointing.id.in_(pointing_ids), PointingEvent.graceid == normalized_graceid
        )
        .all()
    )

    # Get user information
    user = db.query(Users).filter(Users.id == current_user.id).first()

    # Set up creators list
    if doi_group_id:
        # Get creator list from DOI author group
        from server.db.models.doi_author import DOIAuthor

        try:
            valid, creators_list = DOIAuthor.construct_creators(
                doi_group_id, user.id, db
            )
            if valid:
                creators = creators_list
            else:
                # Fall back to current user if group is invalid
                creators = [{"name": f"{user.firstname} {user.lastname}"}]
        except:
            # Fall back to current user if there's an error
            creators = [{"name": f"{user.firstname} {user.lastname}"}]
    else:
        creators = [{"name": f"{user.firstname} {user.lastname}"}]

    # Get instrument names
    insts = (
        db.query(Instrument)
        .filter(Instrument.id.in_([p.instrumentid for p in points]))
        .all()
    )

    inst_set = list(set([i.instrument_name for i in insts]))

    # Create DOI or use existing URL
    if doi_url:
        doi_id, doi_url = 0, doi_url
    else:
        doi_id, doi_url = create_pointing_doi(
            points, normalized_graceid, creators, inst_set
        )

    # Update pointings with DOI information
    for p in points:
        p.doi_url = doi_url
        p.doi_id = doi_id
        p.submitterid = current_user.id  # Ensure submitter is set

    db.commit()

    return doi_url
