"""Get GRB MOC file endpoint."""

from fastapi import APIRouter, Depends, Query
from fastapi.openapi.models import Response
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.auth.auth import get_current_user
from server.utils.error_handling import not_found_exception, validation_exception
from server.utils.gwtm_io import download_gwtm_file
from server.config import Settings as settings

router = APIRouter(tags=["gw_alerts"])


@router.get("/grb_moc_file")
async def get_grbmoc(
    graceid: str = Query(..., description="Grace ID of the GW event"),
    instrument: str = Query(..., description="Instrument name (gbm, lat, or bat)"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get the GRB MOC file for a GW alert.

    Parameters:
    - graceid: The Grace ID of the GW event
    - instrument: Instrument name (gbm, lat, or bat)

    Returns the MOC file
    """
    # Normalize the graceid
    graceid = GWAlert.graceidfromalternate(graceid)

    # Validate instrument
    instrument = instrument.lower()
    if instrument not in ['gbm', 'lat', 'bat']:
        raise validation_exception("Valid instruments are in ['gbm', 'lat', 'bat']")

    # Map instrument names to their full names
    instrument_dictionary = {'gbm': 'Fermi', 'lat': 'LAT', 'bat': 'BAT'}

    # Build path
    moc_filepath = f"fit/{graceid}-{instrument_dictionary[instrument]}.json"

    try:
        file_content = download_gwtm_file(filename=moc_filepath, source=settings.STORAGE_BUCKET_SOURCE, config=settings)
        return Response(content=file_content, media_type="application/json")
    except Exception as e:
        raise not_found_exception(f"MOC file for GW-Alert: '{graceid}' and instrument: '{instrument}' does not exist!")