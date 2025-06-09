"""Create candidates endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import shapely.geometry

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import PostCandidateRequest, CandidateResponse
from server.auth.auth import get_current_user
from server.utils.error_handling import validation_exception

router = APIRouter(tags=["candidates"])


@router.post("/candidate", response_model=CandidateResponse)
async def post_gw_candidates(
        post_request: PostCandidateRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Post new candidate(s) for a GW event.

    This endpoint accepts either a single candidate or multiple candidates
    for a gravitational wave event.
    """

    # Validate that the graceid exists
    valid_alerts = db.query(GWAlert).filter(GWAlert.graceid == post_request.graceid).all()
    if len(valid_alerts) == 0:
        raise validation_exception("Invalid 'graceid'. Visit https://treasuremap.space/alert_select for valid alerts")

    errors = []
    warnings = []
    valid_candidates = []
    candidate_ids = []

    # Process single candidate
    if post_request.candidate:
        valid_candidates.append(post_request.candidate)

    # Process multiple candidates
    elif post_request.candidates:
        for candidate in post_request.candidates:
            valid_candidates.append(candidate)

    for candidate in valid_candidates:

        # Validate the candidate
        new_candidate = GWCandidate(
            graceid=post_request.graceid,
            submitterid=user.id,
            candidate_name=candidate.candidate_name,
            tns_name=candidate.tns_name,
            tns_url=candidate.tns_url,
            position=shapely.geometry.Point(candidate.ra,
                                            candidate.dec).wkt if candidate.ra is not None and candidate.dec is not None else candidate.position,
            discovery_date=candidate.discovery_date,
            discovery_magnitude=candidate.discovery_magnitude,
            magnitude_central_wave=candidate.magnitude_central_wave,
            magnitude_bandwidth=candidate.magnitude_bandwidth,
            magnitude_unit=candidate.magnitude_unit,
            magnitude_bandpass=candidate.magnitude_bandpass,
            associated_galaxy=candidate.associated_galaxy,
            associated_galaxy_redshift=candidate.associated_galaxy_redshift,
            associated_galaxy_distance=candidate.associated_galaxy_distance
        )

        db.add(new_candidate)
        db.flush()
        candidate_ids.append(new_candidate.id)

    db.commit()

    return CandidateResponse(
        candidate_ids=candidate_ids,
        ERRORS=errors,
        WARNINGS=warnings
    )