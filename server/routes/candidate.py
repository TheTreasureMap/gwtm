from fastapi import APIRouter, Depends, Body
from server.utils.error_handling import validation_exception, not_found_exception, permission_exception, server_exception
from sqlalchemy.orm import Session
from typing import List
from dateutil.parser import parse as date_parse
import shapely.wkb

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import (
    CandidateSchema,
    GetCandidateQueryParams,
    CandidateRequest,
    PostCandidateRequest,
    CandidateResponse,
    CandidateUpdateField,
    PutCandidateRequest,
    PutCandidateResponse,
    DeleteCandidateParams,
    DeleteCandidateResponse
)
from server.auth.auth import get_current_user

router = APIRouter(tags=["candidates"])


@router.get("/candidate", response_model=List[CandidateSchema])
async def get_candidates(
        query_params: GetCandidateQueryParams = Depends(),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Get candidates with optional filters.
    """
    filter_conditions = []

    if query_params.id:
        filter_conditions.append(GWCandidate.id == query_params.id)

    if query_params.ids:
        try:
            ids_list = None
            if isinstance(query_params.ids, str):
                ids_list = query_params.ids.split('[')[1].split(']')[0].split(',')
            elif isinstance(query_params.ids, list):
                ids_list = query_params.ids
            if ids_list:
                filter_conditions.append(GWCandidate.id.in_(ids_list))
        except:
            pass

    if query_params.graceid:
        graceid = GWAlert.graceidfromalternate(query_params.graceid)
        filter_conditions.append(GWCandidate.graceid == graceid)

    if query_params.userid:
        filter_conditions.append(GWCandidate.submitterid == query_params.userid)

    if query_params.submitted_date_after:
        try:
            parsed_date_after = date_parse(query_params.submitted_date_after)
            filter_conditions.append(GWCandidate.datecreated >= parsed_date_after)
        except:
            pass

    if query_params.submitted_date_before:
        try:
            parsed_date_before = date_parse(query_params.submitted_date_before)
            filter_conditions.append(GWCandidate.datecreated <= parsed_date_before)
        except:
            pass

    if query_params.discovery_magnitude_gt is not None:
        filter_conditions.append(GWCandidate.discovery_magnitude >= query_params.discovery_magnitude_gt)

    if query_params.discovery_magnitude_lt is not None:
        filter_conditions.append(GWCandidate.discovery_magnitude <= query_params.discovery_magnitude_lt)

    if query_params.discovery_date_after:
        try:
            parsed_date_after = date_parse(query_params.discovery_date_after)
            filter_conditions.append(GWCandidate.discovery_date >= parsed_date_after)
        except:
            pass

    if query_params.discovery_date_before:
        try:
            parsed_date_before = date_parse(query_params.discovery_date_before)
            filter_conditions.append(GWCandidate.discovery_date <= parsed_date_before)
        except:
            pass

    if query_params.associated_galaxy_name:
        filter_conditions.append(GWCandidate.associated_galaxy.contains(query_params.associated_galaxy_name))

    if query_params.associated_galaxy_redshift_gt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_redshift >= query_params.associated_galaxy_redshift_gt)

    if query_params.associated_galaxy_redshift_lt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_redshift <= query_params.associated_galaxy_redshift_lt)

    if query_params.associated_galaxy_distance_gt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_distance >= query_params.associated_galaxy_distance_gt)

    if query_params.associated_galaxy_distance_lt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_distance <= query_params.associated_galaxy_distance_lt)

    candidates = db.query(GWCandidate).filter(*filter_conditions).all()

    for candidate in candidates:
        # Convert position from WKB to WKT
        if candidate.position:
            position = shapely.wkb.loads(bytes(candidate.position.data))
            candidate.position = str(position)

    return candidates


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


@router.put("/candidate", response_model=PutCandidateRequest)
async def update_candidate(
        request: PutCandidateRequest = Body(..., description="Fields to update"),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
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
        "discovery_date": candidate.discovery_date.isoformat() if candidate.discovery_date else None,
        "discovery_magnitude": candidate.discovery_magnitude,
        "magnitude_central_wave": candidate.magnitude_central_wave,
        "magnitude_bandwidth": candidate.magnitude_bandwidth,
        "magnitude_unit": candidate.magnitude_unit,
        "magnitude_bandpass": candidate.magnitude_bandpass,
        "associated_galaxy": candidate.associated_galaxy,
        "associated_galaxy_redshift": candidate.associated_galaxy_redshift,
        "associated_galaxy_distance": candidate.associated_galaxy_distance
    }
    # Convert to CandidateUpdateField instance
    updated_candidate = CandidateUpdateField(**candidate_dict)

    return PutCandidateRequest(
        id=request.id,
        candidate=updated_candidate
    )


@router.delete("/candidate", response_model=DeleteCandidateResponse)
async def delete_candidates(
        delete_params: DeleteCandidateParams = Body(..., description="Fields to delete"),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Delete candidate(s).

    Provide either:
    - A single candidate ID to delete
    - A list of candidate IDs to delete

    Only the owner of a candidate can delete it.
    Returns information about deleted candidates and any warnings.
    """
    warnings = []
    candidates_to_delete = []

    # Handle single ID
    if delete_params.id is not None:
        candidate = db.query(GWCandidate).filter(GWCandidate.id == delete_params.id).first()
        if not candidate:
            raise not_found_exception(f"No candidate found with 'id': {delete_params.id}")

        if candidate.submitterid != user.id:
            raise permission_exception("Error: Unauthorized. Unable to alter other user's records")

        candidates_to_delete.append(candidate)

    # Handle multiple IDs
    elif delete_params.ids is not None:
        query_ids = delete_params.ids
        candidates = db.query(GWCandidate).filter(GWCandidate.id.in_(query_ids)).all()

        if len(candidates) == 0:
            raise not_found_exception("No candidates found with provided 'ids'")

        # Filter candidates the user is allowed to delete
        candidates_to_delete.extend([x for x in candidates if x.submitterid == user.id])
        if len(candidates_to_delete) < len(candidates):
            warnings.append("Some entries were not deleted. You cannot delete candidates you didn't submit")

    else:
        raise validation_exception(
            message="Missing required parameter", 
            errors=["Either 'id' or 'ids' parameter is required"]
        )

    # Delete the candidates
    if len(candidates_to_delete):
        del_ids = []
        for ctd in candidates_to_delete:
            del_ids.append(ctd.id)
            db.delete(ctd)

        db.commit()

        return DeleteCandidateResponse(
            message=f"Successfully deleted {len(candidates_to_delete)} candidate(s)",
            deleted_ids=del_ids,
            warnings=warnings
        )
    else:
        return DeleteCandidateResponse(
            message="No candidates found with input parameters",
            warnings=warnings
        )
