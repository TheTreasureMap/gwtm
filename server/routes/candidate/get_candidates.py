"""Get candidates endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from dateutil.parser import parse as date_parse
import shapely.wkb

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import CandidateSchema, GetCandidateQueryParams
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