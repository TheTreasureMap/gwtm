"""Delete test alerts endpoint."""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.auth.auth import verify_admin
from server.utils.gwtm_io import list_gwtm_bucket, delete_gwtm_files
from server.config import settings
from server.utils.function import by_chunk
from server.db.models.gw_alert import GWAlert
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_galaxy import GWGalaxyEntry
from server.db.models.candidate import GWCandidate

router = APIRouter(tags=["gw_alerts"])


@router.post("/del_test_alerts")
async def del_test_alerts(
    db: Session = Depends(get_db),
    user=Depends(verify_admin),  # Only admin can delete test alerts
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
    filter.append(GWAlert.role == "test")

    # Query for all test alerts that aren't like the ones we want to keep
    gwalerts = db.query(GWAlert).filter(*filter).all()
    gids_to_rm = [x.graceid for x in gwalerts]

    # Query for pointings and pointing events from graceids
    pointing_events = (
        db.query(PointingEvent).filter(PointingEvent.graceid.in_(gids_to_rm)).all()
    )
    pointing_ids = [x.pointingid for x in pointing_events]
    pointings = db.query(Pointing).filter(Pointing.id.in_(pointing_ids)).all()

    # Query for galaxy lists and galaxy list entries from graceids
    try:
        from server.db.models.gw_alert import GWGalaxyList

        galaxylists = (
            db.query(GWGalaxyList).filter(GWGalaxyList.graceid.in_(gids_to_rm)).all()
        )
        galaxylist_ids = [x.id for x in galaxylists]
        galaxyentries = (
            db.query(GWGalaxyEntry)
            .filter(GWGalaxyEntry.listid.in_(galaxylist_ids))
            .all()
        )
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
        objects = list_gwtm_bucket(
            container="test", source=settings.STORAGE_BUCKET_SOURCE, config=settings
        )
        objects_to_delete = [
            o
            for o in objects
            if not any(t in o for t in testids)
            and "alert.json" not in o
            and o != "test/"
        ]

        if len(objects_to_delete):
            total = 0
            for items in by_chunk(objects_to_delete, 1000):
                total += len(items)
                delete_gwtm_files(
                    keys=items, source=settings.STORAGE_BUCKET_SOURCE, config=settings
                )
    except Exception as e:
        # Log the error but continue with the database changes
        print(f"Error deleting files: {str(e)}")

    # Commit all changes
    db.commit()

    return {"message": "Successfully deleted test alerts and associated data"}
