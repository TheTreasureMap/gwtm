"""Update candidate endpoint."""

from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
import shapely.geometry
import shapely.wkb

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import PutCandidateRequest, CandidateUpdateField
from server.auth.auth import get_current_user
from server.utils.error_handling import not_found_exception, permission_exception

router = APIRouter(tags=["candidates"])


@router.put("/candidate", response_model=PutCandidateRequest)
async def update_candidate(
    request: PutCandidateRequest = Body(..., description="Fields to update"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Update an existing candidate.

    Only the owner of the candidate can update it.
    Returns either a success response with the updated candidate or a failure response with errors.
    """
    # Find the candidate
    candidate = db.query(GWCandidate).filter(GWCandidate.id == request.id).first()

    if not candidate:
        raise not_found_exception(f"No candidate found with id: {request.id}")

    # Check permissions
    if candidate.submitterid != user.id:
        raise permission_exception("Unable to alter other user's candidate records")

    update = request.candidate.dict(exclude_unset=True)
    # Copy values from the Pydantic schema to the SQLAlchemy model
    for key, value in update.items():
        if hasattr(candidate, key):
            setattr(candidate, key, value)

    position = candidate.position

    # Update ra or dec in the wkt string position
    if "ra" in update or "dec" in update:
        if update["ra"] is not None and update["dec"] is not None:
            position = shapely.geometry.Point(update["ra"], update["dec"]).wkt
            candidate.position = position
        elif update["ra"] is not None:
            position = shapely.geometry.Point(update["ra"], candidate.dec).wkt
            candidate.position = position
        elif update["dec"] is not None:
            position = shapely.geometry.Point(candidate.ra, update["dec"]).wkt
            candidate.position = position

    db.commit()
    db.refresh(candidate)

    # copy the updated candidate to CandidateUpdateField object
    candidate_dict = {
        "graceid": candidate.graceid,
        "submitterid": candidate.submitterid,
        "candidate_name": candidate.candidate_name,
        "datecreated": candidate.datecreated,
        "tns_name": candidate.tns_name,
        "tns_url": candidate.tns_url,
        # convert position from wkb to wkt and then to string
        "position": str(shapely.wkb.loads(bytes(candidate.position.data))),
        # convert discovery_date to string
        "discovery_date": (
            candidate.discovery_date.isoformat() if candidate.discovery_date else None
        ),
        "discovery_magnitude": candidate.discovery_magnitude,
        "magnitude_central_wave": candidate.magnitude_central_wave,
        "magnitude_bandwidth": candidate.magnitude_bandwidth,
        "magnitude_unit": candidate.magnitude_unit,
        "magnitude_bandpass": candidate.magnitude_bandpass,
        "associated_galaxy": candidate.associated_galaxy,
        "associated_galaxy_redshift": candidate.associated_galaxy_redshift,
        "associated_galaxy_distance": candidate.associated_galaxy_distance,
    }
    # Convert to CandidateUpdateField instance
    updated_candidate = CandidateUpdateField(**candidate_dict)

    return PutCandidateRequest(id=request.id, candidate=updated_candidate)
