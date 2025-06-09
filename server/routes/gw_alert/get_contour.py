"""Get GW contour endpoint."""

from fastapi import APIRouter, Depends, Query
from fastapi.openapi.models import Response
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.auth.auth import get_current_user
from server.utils.error_handling import not_found_exception
from server.utils.gwtm_io import download_gwtm_file
from server.config import Settings as settings

router = APIRouter(tags=["gw_alerts"])


@router.get("/gw_contour")
async def get_gw_contour(
    graceid: str = Query(..., description="Grace ID of the GW event"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get the contour for a GW alert.

    Parameters:
    - graceid: The Grace ID of the GW event

    Returns the contour JSON file
    """
    # Normalize the graceid
    graceid = GWAlert.graceidfromalternate(graceid)

    # Get the latest alert for this graceid
    alerts = db.query(GWAlert).filter(GWAlert.graceid == graceid).order_by(GWAlert.datecreated.desc()).all()

    if not alerts:
        raise not_found_exception(f"No alert found with graceid: {graceid}")

    # Extract alert info
    alert = alerts[0]
    alert_types = [x.alert_type for x in alerts]
    latest_alert_type = alert.alert_type
    num = len([x for x in alert_types if x == latest_alert_type]) - 1
    alert_type = latest_alert_type if num < 1 else latest_alert_type + str(num)

    # Build path info
    path_info = f"{graceid}-{alert_type}"
    contour_path = f"fit/{path_info}-contours-smooth.json"

    try:
        file_content = download_gwtm_file(filename=contour_path, source=settings.STORAGE_BUCKET_SOURCE, config=settings)
        return Response(content=file_content, media_type="application/json")
    except Exception as e:
        raise not_found_exception(f"Error in retrieving Contour file: {contour_path}")