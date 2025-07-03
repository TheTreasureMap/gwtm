"""Post GW alert endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.schemas.gw_alert import GWAlertSchema
from server.auth.auth import verify_admin

router = APIRouter(tags=["gw_alerts"])


@router.post("/post_alert", response_model=GWAlertSchema)
async def post_alert(
    alert_data: GWAlertSchema,
    db: Session = Depends(get_db),
    user=Depends(verify_admin),  # Only admin can post alerts
):
    """
    Post a new GW alert (admin only).

    Parameters:
    - Alert data in the request body

    Returns the created GW Alert object
    """
    alert_instance = GWAlert(**alert_data.dict())
    db.add(alert_instance)
    db.commit()
    db.refresh(alert_instance)

    return alert_instance
