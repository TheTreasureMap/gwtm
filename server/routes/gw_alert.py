import io
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from fastapi.openapi.models import Response

from server.utils.error_handling import not_found_exception, validation_exception
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.schemas.gw_alert import GWAlertSchema
from server.auth.auth import get_current_user, verify_admin
from server.utils.gwtm_io import download_gwtm_file, list_gwtm_bucket, delete_gwtm_files
from server.config import Settings as settings
from server.utils.function import by_chunk
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_galaxy import GWGalaxyEntry
from server.db.models.candidate import GWCandidate

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


@router.post("/post_alert", response_model=GWAlertSchema)
async def post_alert(
        alert_data: GWAlertSchema,
        db: Session = Depends(get_db),
        user=Depends(verify_admin)  # Only admin can post alerts
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


@router.get(
    "/gw_skymap",
    response_description="FITS file containing the gravitational wave skymap",
    responses={
        200: {
            "content": {"application/fits": {}},
            "description": "The skymap FITS file for the specified gravitational wave event"
        },
        404: {
            "description": "Skymap not found for the specified event"
        }
    }
)
async def get_gw_skymap(
        graceid: str = Query(..., description="Grace ID of the GW event"),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
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
    skymap_path = f"fit/{path_info}.fits.gz"

    # Download and return the file
    try:
        file_content = download_gwtm_file(filename=skymap_path, source=settings.STORAGE_BUCKET_SOURCE, config=settings,
                                          decode=False)

        # Create a streaming response with the binary content
        filename = f"{graceid}_skymap.fits.gz"
        return StreamingResponse(
            io.BytesIO(file_content),
            media_type="application/fits",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/fits"
            }
        )
    except Exception as e:
        raise not_found_exception(f"Error in retrieving skymap file: {skymap_path}")

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


@router.post("/del_test_alerts")
async def del_test_alerts(
        db: Session = Depends(get_db),
        user=Depends(verify_admin)  # Only admin can delete test alerts
):
    """
    Delete test alerts (admin only).

    This endpoint removes test alerts from the database and related storage.
    """
    # Set up filter conditions
    filter = []
    testids = []
    alert_to_keep = "MS181101ab"
    filter.append(~GWAlert.graceid.contains(alert_to_keep))

    # Add date-based test IDs to exclusion list
    for td in [-1, 0, 1]:
        dd = datetime.now() + timedelta(days=td)
        yy = str(dd.year)[2:4]
        mm = dd.month if dd.month >= 10 else f"0{dd.month}"
        dd = dd.day if dd.day >= 10 else f"0{dd.day}"
        graceidlike = f"MS{yy}{mm}{dd}"

        testids.append(graceidlike)
        filter.append(~GWAlert.graceid.contains(graceidlike))

    # Add the alert to keep to both the filter and the testids list
    filter.append(~GWAlert.graceid.contains(alert_to_keep))
    testids.append(alert_to_keep)

    # Only delete test alerts
    filter.append(GWAlert.role == 'test')

    # Query for all test alerts that aren't like the ones we want to keep
    gwalerts = db.query(GWAlert).filter(*filter).all()
    gids_to_rm = [x.graceid for x in gwalerts]

    # Query for pointings and pointing events from graceids
    pointing_events = db.query(PointingEvent).filter(PointingEvent.graceid.in_(gids_to_rm)).all()
    pointing_ids = [x.pointingid for x in pointing_events]
    pointings = db.query(Pointing).filter(Pointing.id.in_(pointing_ids)).all()

    # Query for galaxy lists and galaxy list entries from graceids
    try:
        from server.db.models.gw_alert import GWGalaxyList
        galaxylists = db.query(GWGalaxyList).filter(GWGalaxyList.graceid.in_(gids_to_rm)).all()
        galaxylist_ids = [x.id for x in galaxylists]
        galaxyentries = db.query(GWGalaxyEntry).filter(GWGalaxyEntry.listid.in_(galaxylist_ids)).all()
    except ImportError:
        # If the model isn't available, create empty lists
        galaxylists = []
        galaxyentries = []

    # Query for candidates to delete
    candidates = db.query(GWCandidate).filter(GWCandidate.graceid.in_(gids_to_rm)).all()

    # Delete in order (to avoid foreign key constraints)
    if len(candidates) > 0:
        for c in candidates:
            db.delete(c)

    if len(galaxyentries) > 0:
        for ge in galaxyentries:
            db.delete(ge)

    if len(galaxylists) > 0:
        for gl in galaxylists:
            db.delete(gl)

    if len(pointings) > 0:
        for p in pointings:
            db.delete(p)

    if len(pointing_events) > 0:
        for pe in pointing_events:
            db.delete(pe)

    if len(gwalerts) > 0:
        for ga in gwalerts:
            db.delete(ga)

    # Delete files from storage
    try:
        objects = list_gwtm_bucket(container="test", source=settings.STORAGE_BUCKET_SOURCE, config=settings)
        objects_to_delete = [
            o for o in objects if not any(t in o for t in testids) and 'alert.json' not in o and o != 'test/'
        ]

        if len(objects_to_delete):
            total = 0
            for items in by_chunk(objects_to_delete, 1000):
                total += len(items)
                delete_gwtm_files(keys=items, source=settings.STORAGE_BUCKET_SOURCE, config=settings)
    except Exception as e:
        # Log the error but continue with the database changes
        print(f"Error deleting files: {str(e)}")

    # Commit all changes
    db.commit()

    return {"message": "Successfully deleted test alerts and associated data"}
