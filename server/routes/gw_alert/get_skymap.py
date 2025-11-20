"""Get GW skymap endpoint."""

import io
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.auth.auth import get_current_user
from server.utils.error_handling import not_found_exception
from server.utils.gwtm_io import download_gwtm_file
from server.config import Settings as settings

router = APIRouter(tags=["gw_alerts"])


@router.get(
    "/gw_skymap",
    response_description="FITS file containing the gravitational wave skymap",
    responses={
        200: {
            "content": {"application/fits": {}},
            "description": "The skymap FITS file for the specified gravitational wave event",
        },
        404: {"description": "Skymap not found for the specified event"},
    },
)
async def get_gw_skymap(
    graceid: str = Query(..., description="Grace ID of the GW event"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get the skymap FITS file for a gravitational wave alert.

    Parameters:
    - graceid: The Grace ID of the GW event

    Returns:
    - A binary response containing the FITS file with the skymap data
    """
    # Normalize the graceid
    graceid = GWAlert.graceidfromalternate(graceid)

    # Get the latest alert for this graceid
    alerts = (
        db.query(GWAlert)
        .filter(GWAlert.graceid == graceid)
        .order_by(GWAlert.datecreated.desc())
        .all()
    )

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
    skymap_path = f"fit/{path_info}.fits.gz"

    # Download and return the file
    try:
        file_content = download_gwtm_file(
            filename=skymap_path,
            source=settings.STORAGE_BUCKET_SOURCE,
            config=settings,
            decode=False,
        )

        # Create a streaming response with the binary content
        filename = f"{graceid}_skymap.fits.gz"
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/fits",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/fits",
            },
        )
    except Exception as e:
        raise not_found_exception(f"Error in retrieving skymap file: {skymap_path}")
