"""Query GW alerts endpoint."""

from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.schemas.gw_alert import GWAlertSchema
from server.auth.auth import get_current_user

router = APIRouter(tags=["gw_alerts"])


@router.get("/query_alerts", response_model=List[GWAlertSchema])
async def query_alerts(
    graceid: Optional[str] = None,
    alert_type: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Query GW alerts with optional filters.

    Parameters:
    - graceid: Filter by Grace ID
    - alert_type: Filter by alert type

    Returns a list of GW Alert objects
    """
    filter_conditions = []

    if graceid:
        # Handle alternative GraceID format if needed
        # Implementation will depend on the graceidfromalternate function
        filter_conditions.append(GWAlert.graceid == graceid)

    if alert_type:
        filter_conditions.append(GWAlert.alert_type == alert_type)

    if role:
        filter_conditions.append(GWAlert.role == role)

    alerts = db.query(GWAlert).filter(*filter_conditions).order_by(GWAlert.datecreated.desc()).all()

    return alerts