"""Get candidates endpoint."""

import operator
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

# Data-driven filter definitions: (param_name, model_column, comparison_operator)
RANGE_FILTERS = [
    ("discovery_magnitude_gt", GWCandidate.discovery_magnitude, operator.ge),
    ("discovery_magnitude_lt", GWCandidate.discovery_magnitude, operator.le),
    (
        "associated_galaxy_redshift_gt",
        GWCandidate.associated_galaxy_redshift,
        operator.ge,
    ),
    (
        "associated_galaxy_redshift_lt",
        GWCandidate.associated_galaxy_redshift,
        operator.le,
    ),
    (
        "associated_galaxy_distance_gt",
        GWCandidate.associated_galaxy_distance,
        operator.ge,
    ),
    (
        "associated_galaxy_distance_lt",
        GWCandidate.associated_galaxy_distance,
        operator.le,
    ),
]

DATE_FILTERS = [
    ("submitted_date_after", GWCandidate.datecreated, operator.ge),
    ("submitted_date_before", GWCandidate.datecreated, operator.le),
    ("discovery_date_after", GWCandidate.discovery_date, operator.ge),
    ("discovery_date_before", GWCandidate.discovery_date, operator.le),
]


@router.get("/candidate", response_model=List[CandidateSchema])
async def get_candidates(
    query_params: GetCandidateQueryParams = Depends(),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get candidates with optional filters.
    """
    filter_conditions = []

    # Special-case filters with unique logic
    if query_params.id:
        filter_conditions.append(GWCandidate.id == query_params.id)

    if query_params.ids:
        try:
            ids_list = None
            if isinstance(query_params.ids, str):
                ids_list = query_params.ids.split("[")[1].split("]")[0].split(",")
            elif isinstance(query_params.ids, list):
                ids_list = query_params.ids
            if ids_list:
                filter_conditions.append(GWCandidate.id.in_(ids_list))
        except (ValueError, TypeError, IndexError):
            pass  # Skip filter if value cannot be parsed

    if query_params.graceid:
        graceid = GWAlert.graceidfromalternate(query_params.graceid)
        filter_conditions.append(GWCandidate.graceid == graceid)

    if query_params.userid:
        filter_conditions.append(GWCandidate.submitterid == query_params.userid)

    if query_params.associated_galaxy_name:
        filter_conditions.append(
            GWCandidate.associated_galaxy.contains(query_params.associated_galaxy_name)
        )

    # Date filters — parse string to datetime, skip on parse failure
    for param_name, column, op in DATE_FILTERS:
        value = getattr(query_params, param_name, None)
        if value is not None:
            try:
                parsed = date_parse(value) if isinstance(value, str) else value
                filter_conditions.append(op(column, parsed))
            except (ValueError, TypeError, IndexError):
                pass  # Skip filter if value cannot be parsed

    # Numeric range filters
    for param_name, column, op in RANGE_FILTERS:
        value = getattr(query_params, param_name, None)
        if value is not None:
            filter_conditions.append(op(column, value))

    candidates = db.query(GWCandidate).filter(*filter_conditions).all()

    for candidate in candidates:
        # Convert position from WKB to WKT
        if candidate.position:
            position = shapely.wkb.loads(bytes(candidate.position.data))
            candidate.position = str(position)

    return candidates
