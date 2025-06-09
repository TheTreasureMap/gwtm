"""Create pointings endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.schemas.pointing import PointingCreateRequest, PointingResponse
from server.auth.auth import get_current_user
from server.utils import pointing as pointing_utils

router = APIRouter(tags=["pointings"])


@router.post("/pointings", response_model=PointingResponse)
async def add_pointings(
        request: PointingCreateRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Add new pointings to the database.
    """
    # Initialize variables
    points = []
    errors = []
    warnings = []

    # Validate graceid exists
    pointing_utils.validate_graceid(request.graceid, db)

    # Prepare DOI creators if DOI is requested
    creators = None
    if request.request_doi:
        creators = pointing_utils.prepare_doi_creators(
            request.creators, request.doi_group_id, user, db
        )

    # Get instruments for validation
    instruments_dict = pointing_utils.get_instruments_dict(db)

    # Get existing pointings for duplicate check
    existing_pointings = db.query(Pointing).filter(
        Pointing.id == PointingEvent.pointingid,
        PointingEvent.graceid == request.graceid
    ).all()

    # Process pointings (either single or multiple)
    pointings_to_process = []
    if request.pointing:
        pointings_to_process = [request.pointing]
    elif request.pointings:
        pointings_to_process = request.pointings

    for pointing_data in pointings_to_process:
        try:
            # Check if this is an update to a planned pointing
            if hasattr(pointing_data, 'id') and pointing_data.id:
                # Handle planned pointing update
                pointing_obj = pointing_utils.handle_planned_pointing_update(
                    pointing_data, user.id, db
                )
            else:
                # Validate and resolve instrument reference
                instrument_id = pointing_utils.validate_instrument_reference(
                    pointing_data, instruments_dict
                )
                
                # Create new pointing object
                pointing_obj = pointing_utils.create_pointing_from_schema(
                    pointing_data, user.id, instrument_id
                )
                
                # Check for duplicates
                if pointing_utils.check_duplicate_pointing(pointing_obj, existing_pointings):
                    errors.append([f"Object: {pointing_data.dict()}", ["Pointing already submitted"]])
                    continue

            points.append(pointing_obj)
            db.add(pointing_obj)

        except Exception as e:
            errors.append([f"Object: {pointing_data.model_dump()}", [str(e)]])

    # Flush to get pointing IDs
    db.flush()

    # Create pointing events (this should always happen when we have valid points and graceid)
    if points:  # Only create pointing events if we have valid points
        for p in points:
            pointing_event = PointingEvent(
                pointingid=p.id,
                graceid=request.graceid
            )
            db.add(pointing_event)

    db.flush()
    db.commit()

    # Handle DOI creation if requested
    doi_url = None
    if request.request_doi and points:
        if request.doi_url:
            doi_id, doi_url = 0, request.doi_url
        else:
            doi_id, doi_url = pointing_utils.create_doi_for_pointings(
                points, request.graceid, creators, db
            )

        if doi_id is not None:
            for p in points:
                p.doi_url = doi_url
                p.doi_id = doi_id

            db.flush()
            db.commit()

    # Return response
    return PointingResponse(
        pointing_ids=[p.id for p in points],
        ERRORS=errors,
        WARNINGS=warnings,
        DOI=doi_url
    )