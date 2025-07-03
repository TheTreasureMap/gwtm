"""Get event galaxies endpoint."""

from typing import List, Optional
import datetime
from dateutil.parser import parse as date_parse
from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.gw_galaxy import GWGalaxyEntry, GWGalaxyList
from server.auth.auth import get_current_user
from server.schemas.gw_galaxy import GWGalaxyEntrySchema
from server.utils.error_handling import validation_exception

router = APIRouter(tags=["galaxies"])


@router.get("/event_galaxies", response_model=List[GWGalaxyEntrySchema])
async def get_event_galaxies(
    graceid: str = Query(..., description="Grace ID of the GW event"),
    timesent_stamp: Optional[str] = None,
    listid: Optional[int] = None,
    groupname: Optional[str] = None,
    score_gt: Optional[float] = None,
    score_lt: Optional[float] = None,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get galaxies associated with a GW event.
    """
    filter_conditions = [GWGalaxyEntry.listid == GWGalaxyList.id]

    # Normalize the graceid
    graceid = GWAlert.graceidfromalternate(graceid)
    filter_conditions.append(GWGalaxyList.graceid == graceid)

    if timesent_stamp:
        try:
            time = date_parse(timesent_stamp)
        except ValueError:
            raise validation_exception(
                message="Error parsing date",
                errors=[
                    f"Timestamp should be in %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00"
                ],
            )

        # Find the alert with the given time and graceid
        alert = (
            db.query(GWAlert)
            .filter(
                GWAlert.timesent < time + datetime.timedelta(seconds=15),
                GWAlert.timesent > time - datetime.timedelta(seconds=15),
                GWAlert.graceid == graceid,
            )
            .first()
        )

        if not alert:
            raise validation_exception(
                message=f"Invalid 'timesent_stamp' for event {graceid}",
                errors=[
                    f"Please visit http://treasuremap.space/alerts?graceids={graceid} for valid timesent stamps for this event"
                ],
            )

        filter_conditions.append(GWGalaxyList.alertid == str(alert.id))

    if listid:
        filter_conditions.append(GWGalaxyList.id == listid)
    if groupname:
        filter_conditions.append(GWGalaxyList.groupname == groupname)
    if score_gt is not None:
        filter_conditions.append(GWGalaxyEntry.score >= score_gt)
    if score_lt is not None:
        filter_conditions.append(GWGalaxyEntry.score <= score_lt)

    galaxy_entries = (
        db.query(GWGalaxyEntry)
        .join(GWGalaxyList, GWGalaxyList.id == GWGalaxyEntry.listid)
        .filter(*filter_conditions)
        .all()
    )

    # Convert GeoAlchemy2 Geography to a string for Pydantic
    result_entries = []
    for entry in galaxy_entries:
        entry_dict = {
            "id": entry.id,
            "listid": entry.listid,
            "name": entry.name,
            "score": entry.score,
            "rank": entry.rank,
            "info": entry.info,
        }

        # Convert position to WKT string
        if entry.position:
            shape = to_shape(entry.position)
            entry_dict["position"] = str(shape)

        result_entries.append(GWGalaxyEntrySchema(**entry_dict))

    return result_entries
