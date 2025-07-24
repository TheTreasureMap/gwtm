"""Query GW alerts endpoint."""

from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.core.enums.pointingstatus import PointingStatus as pointing_status
from server.schemas.gw_alert import (
    GWAlertSchema,
    GWAlertQueryResponse,
    GWAlertFilterOptionsResponse,
)

router = APIRouter(tags=["gw_alerts"])


@router.get("/query_alerts")
async def query_alerts(
    graceid: Optional[str] = None,
    alert_type: Optional[str] = None,
    role: Optional[str] = None,
    observing_run: Optional[str] = None,
    far: Optional[str] = Query(
        None, description="Filter by FAR: 'all', 'significant', or 'subthreshold'"
    ),
    has_pointings: Optional[bool] = Query(
        False, description="Filter to only alerts with completed pointings"
    ),
    instrument_id: Optional[int] = Query(
        None, description="Filter to only alerts with pointings from specific instrument"
    ),
    include_pointing_count: Optional[bool] = Query(
        False, description="Include pointing count for each alert (when filtered by instrument)"
    ),
    format: Optional[str] = Query(
        "simple",
        description="Response format: 'simple' (list) or 'paginated' (object with metadata)",
    ),
    page: int = Query(
        1, ge=1, description="Page number (1-based, only used with format=paginated)"
    ),
    per_page: int = Query(
        25,
        ge=1,
        le=100,
        description="Items per page (max 100, only used with format=paginated)",
    ),
    db: Session = Depends(get_db),
) -> Union[List[GWAlertSchema], GWAlertQueryResponse]:
    """
    Query GW alerts with optional filters.

    Parameters:
    - graceid: Filter by Grace ID (supports partial text search)
    - alert_type: Filter by alert type
    - role: Filter by role
    - observing_run: Filter by observing run (O2, O3, O4, etc.)
    - far: Filter by FAR: 'all', 'significant', or 'subthreshold'
    - has_pointings: Filter to only alerts with completed pointings
    - instrument_id: Filter to only alerts with pointings from specific instrument
    - include_pointing_count: Include pointing count for each alert (when filtered by instrument)
    - format: Response format - 'simple' returns list (default, backwards compatible), 'paginated' returns object with metadata
    - page: Page number (1-based, only used with format=paginated)
    - per_page: Items per page (max 100, only used with format=paginated)

    Returns either List[GWAlertSchema] (format=simple) or GWAlertQueryResponse (format=paginated)
    """
    filter_conditions = []

    if graceid:
        # Handle alternative GraceID format if needed - use exact matching only
        if graceid.strip():
            search_input = graceid.strip()

            from sqlalchemy import or_

            filter_conditions.append(
                or_(
                    GWAlert.graceid == search_input, GWAlert.alternateid == search_input
                )
            )

    if alert_type:
        filter_conditions.append(GWAlert.alert_type == alert_type)

    if role and role != "all":
        filter_conditions.append(GWAlert.role == role)

    if observing_run and observing_run != "all":
        filter_conditions.append(GWAlert.observing_run == observing_run)

    # Handle FAR filtering with thresholds (matching Flask logic)
    if far and far != "all":
        if far == "significant":
            # Significant events: FAR < threshold
            # Use different thresholds for Burst vs other events (matching Flask)
            from sqlalchemy import case, and_, or_

            filter_conditions.append(
                or_(
                    and_(GWAlert.group == "Burst", GWAlert.far < 3.2e-8),
                    and_(GWAlert.group != "Burst", GWAlert.far < 3.8e-7),
                )
            )
            # Filter out retracted alerts when applying FAR filtering
            filter_conditions.append(GWAlert.alert_type != "Retraction")
        elif far == "subthreshold":
            # Subthreshold events: FAR >= threshold
            from sqlalchemy import case, and_, or_

            filter_conditions.append(
                or_(
                    and_(GWAlert.group == "Burst", GWAlert.far >= 3.2e-8),
                    and_(GWAlert.group != "Burst", GWAlert.far >= 3.8e-7),
                )
            )
            # Filter out retracted alerts when applying FAR filtering
            filter_conditions.append(GWAlert.alert_type != "Retraction")

    # Handle instrument filtering and pointing counts
    if instrument_id is not None or include_pointing_count:
        # When filtering by instrument or including pointing counts, we need to join with pointing tables
        if include_pointing_count and instrument_id is not None:
            # Special logic for getting events contributed - match Flask exactly
            # First, get the count of pointings per graceid using a proper group by query
            pointing_counts_query = (
                db.query(
                    PointingEvent.graceid,
                    func.count(Pointing.id).label('pointing_count')
                )
                .join(Pointing, PointingEvent.pointingid == Pointing.id)
                .filter(
                    Pointing.instrumentid == instrument_id,
                    Pointing.status == pointing_status.completed
                )
                .group_by(PointingEvent.graceid)
                .all()
            )
            
            # Extract unique graceids and create count mapping
            if pointing_counts_query:
                gids = [x.graceid for x in pointing_counts_query]
                pointing_counts_map = {x.graceid: x.pointing_count for x in pointing_counts_query}
                
                # Query GWAlerts for these grace IDs
                results = (
                    db.query(GWAlert)
                    .filter(GWAlert.graceid.in_(gids))
                    .filter(*filter_conditions)
                    .order_by(GWAlert.graceid.desc())  # Sort graceids in reverse order like Flask
                    .all()
                )
                
                # Add pointing counts to each alert
                alerts_with_counts = []
                for alert in results:
                    alert_dict = {**alert.__dict__}
                    alert_dict['pointing_count'] = pointing_counts_map.get(alert.graceid, 0)
                    alerts_with_counts.append(GWAlertSchema(**alert_dict))
                
                # Return processed results directly
                return alerts_with_counts
            else:
                # No events contributed, return empty list
                return []
        else:
            # Standard query but still handle instrument filtering
            base_query = db.query(GWAlert).filter(*filter_conditions)
    else:
        # Standard query without instrument-specific logic
        base_query = db.query(GWAlert).filter(*filter_conditions)

    # Apply has_pointings filter if requested
    if has_pointings:
        # Only include alerts that have completed pointings
        # Use a subquery to find graceids with completed pointings
        if instrument_id is not None:
            # Filter by specific instrument
            pointing_subquery = (
                db.query(PointingEvent.graceid)
                .join(Pointing, Pointing.id == PointingEvent.pointingid)
                .filter(
                    Pointing.status == pointing_status.completed,
                    Pointing.instrumentid == instrument_id
                )
                .distinct()
                .subquery()
            )
        else:
            # Filter by any instrument
            pointing_subquery = (
                db.query(PointingEvent.graceid)
                .join(Pointing, Pointing.id == PointingEvent.pointingid)  
                .filter(Pointing.status == pointing_status.completed)
                .distinct()
                .subquery()
            )

        base_query = base_query.filter(
            GWAlert.graceid.in_(db.query(pointing_subquery.c.graceid))
        )
    elif instrument_id is not None:
        # Filter by instrument even if not requiring pointings
        pointing_subquery = (
            db.query(PointingEvent.graceid)
            .join(Pointing, Pointing.id == PointingEvent.pointingid)
            .filter(
                Pointing.instrumentid == instrument_id,
                Pointing.status == pointing_status.completed
            )
            .distinct()
            .subquery()
        )
        
        base_query = base_query.filter(
            GWAlert.graceid.in_(db.query(pointing_subquery.c.graceid))
        )

    # Get total count
    total = base_query.count()

    # Calculate pagination values
    offset = (page - 1) * per_page
    total_pages = (total + per_page - 1) // per_page  # Ceiling division

    # Return format based on format parameter
    if format == "paginated":
        # Get paginated results
        results = (
            base_query.order_by(GWAlert.datecreated.desc())
            .offset(offset)
            .limit(per_page)
            .all()
        )

        # Process results based on whether we have pointing counts
        if include_pointing_count and instrument_id is not None:
            alerts = []
            for result in results:
                alert = result[0]  # GWAlert object
                pointing_count = result[1]  # pointing count
                # Create alert dict and add pointing count
                alert_dict = {**alert.__dict__}
                alert_dict['pointing_count'] = pointing_count
                alerts.append(GWAlertSchema(**alert_dict))
        else:
            alerts = [GWAlertSchema.model_validate(alert) for alert in results]

        return GWAlertQueryResponse(
            alerts=alerts,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
    else:
        # Simple format (backwards compatible) - return all results as list
        results = base_query.order_by(GWAlert.datecreated.desc()).all()
        
        # Process results based on whether we have pointing counts
        if include_pointing_count and instrument_id is not None:
            alerts = []
            for result in results:
                alert = result[0]  # GWAlert object
                pointing_count = result[1]  # pointing count
                # Create alert dict and add pointing count
                alert_dict = {**alert.__dict__}
                alert_dict['pointing_count'] = pointing_count
                alerts.append(GWAlertSchema(**alert_dict))
            return alerts
        else:
            return [GWAlertSchema.model_validate(alert) for alert in results]


@router.get("/alert_filter_options", response_model=GWAlertFilterOptionsResponse)
async def get_alert_filter_options(db: Session = Depends(get_db)):
    """
    Get available filter options for GW alerts.

    Returns unique values for observing_runs, roles, and alert_types
    from the database to populate filter dropdowns dynamically.
    """
    # Get unique observing runs
    observing_runs = (
        db.query(GWAlert.observing_run)
        .distinct()
        .filter(GWAlert.observing_run.isnot(None))
        .all()
    )
    observing_runs = sorted([run[0] for run in observing_runs if run[0]])

    # Get unique roles
    roles = db.query(GWAlert.role).distinct().filter(GWAlert.role.isnot(None)).all()
    roles = sorted([role[0] for role in roles if role[0]])

    # Get unique alert types
    alert_types = (
        db.query(GWAlert.alert_type)
        .distinct()
        .filter(GWAlert.alert_type.isnot(None))
        .all()
    )
    alert_types = sorted([alert_type[0] for alert_type in alert_types if alert_type[0]])

    return GWAlertFilterOptionsResponse(
        observing_runs=observing_runs, roles=roles, alert_types=alert_types
    )
