"""Get alert instruments footprints endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from server.db.database import get_db
from server.db.models.instrument import Instrument
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_alert import GWAlert

router = APIRouter(tags=["UI"])


@router.get("/ajax_alertinstruments_footprints")
async def get_alert_instruments_footprints(
    graceid: str = None,
    pointing_status: str = None,
    tos_mjd: float = None,
    db: Session = Depends(get_db),
):
    """Get footprints of instruments that observed a specific alert."""
    from server.utils.function import (
        sanatize_pointing,
        project_footprint,
        sanatize_footprint_ccds,
    )
    from server.db.models.instrument import FootprintCCD
    import json
    import hashlib
    from server.utils.gwtm_io import get_cached_file, set_cached_file
    from server.config import settings

    # First find the alert by graceid, handling alternate IDs
    alert = db.query(GWAlert).filter(GWAlert.graceid == graceid).first()
    if not alert:
        # Try to find by alternate ID
        alert = db.query(GWAlert).filter(GWAlert.alternateid == graceid).first()
        if alert:
            # Use the actual graceid from now on
            graceid = alert.graceid
        else:
            raise HTTPException(status_code=404, detail="Alert not found")

    # Set default status if none provided
    if pointing_status is None:
        pointing_status = "completed"

    # Build pointing filter - need to join with PointingEvent to get alert association
    from server.db.models.pointing_event import PointingEvent

    pointing_filter = []
    pointing_filter.append(PointingEvent.graceid == graceid)
    pointing_filter.append(PointingEvent.pointingid == Pointing.id)

    # Status filtering
    from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum
    
    if pointing_status == "pandc":
        pointing_filter.append(
            or_(Pointing.status == pointing_status_enum.completed, Pointing.status == pointing_status_enum.planned)
        )
    elif pointing_status not in ["all", ""]:
        if pointing_status == "completed":
            pointing_filter.append(Pointing.status == pointing_status_enum.completed)
        elif pointing_status == "planned":
            pointing_filter.append(Pointing.status == pointing_status_enum.planned)
        elif pointing_status == "cancelled":
            pointing_filter.append(Pointing.status == pointing_status_enum.cancelled)

    # Get pointing info
    pointing_info = (
        db.query(
            Pointing.id,
            Pointing.instrumentid,
            Pointing.pos_angle,
            Pointing.time,
            func.ST_AsText(Pointing.position).label("position"),
            Pointing.band,
            Pointing.depth,
            Pointing.depth_unit,
            Pointing.status,
        )
        .join(PointingEvent, PointingEvent.pointingid == Pointing.id)
        .filter(*pointing_filter)
        .all()
    )

    # Cache key based on pointing IDs
    pointing_ids = [p.id for p in pointing_info]
    hash_pointing_ids = hashlib.sha1(json.dumps(pointing_ids).encode()).hexdigest()
    cache_key = f"cache/footprint_{graceid}_{pointing_status}_{hash_pointing_ids}"

    # Try to get from cache first
    cached_overlays = get_cached_file(cache_key, settings)

    if cached_overlays:
        return json.loads(cached_overlays)

    # Not in cache, generate fresh data
    instrument_ids = [p.instrumentid for p in pointing_info]

    # Get instrument info
    instrumentinfo = (
        db.query(Instrument.instrument_name, Instrument.nickname, Instrument.id)
        .filter(Instrument.id.in_(instrument_ids))
        .all()
    )

    # Get footprint info
    from server.db.models.instrument import FootprintCCD

    footprintinfo = (
        db.query(
            func.ST_AsText(FootprintCCD.footprint).label("footprint"),
            FootprintCCD.instrumentid,
        )
        .filter(FootprintCCD.instrumentid.in_(instrument_ids))
        .all()
    )

    # Prepare colors
    colorlist = [
        "#ffe119",
        "#4363d8",
        "#f58231",
        "#42d4f4",
        "#f032e6",
        "#fabebe",
        "#469990",
        "#e6beff",
        "#9A6324",
        "#fffac8",
        "#800000",
        "#aaffc3",
        "#000075",
        "#a9a9a9",
    ]

    # Generate overlays
    inst_overlays = []

    for i, inst in enumerate([x for x in instrumentinfo if x.id != 49]):
        name = (
            inst.nickname
            if inst.nickname and inst.nickname != "None"
            else inst.instrument_name
        )

        try:
            color = colorlist[i]
        except IndexError:
            color = "#" + format(inst.id % 0xFFFFFF, "06x")

        footprint_ccds = [
            x.footprint for x in footprintinfo if x.instrumentid == inst.id
        ]
        sanatized_ccds = sanatize_footprint_ccds(footprint_ccds)
        inst_pointings = [x for x in pointing_info if x.instrumentid == inst.id]
        pointing_geometries = []

        for p in inst_pointings:
            import astropy.time

            t = astropy.time.Time([p.time])
            ra, dec = sanatize_pointing(p.position)

            # Calculate time relative to trigger - use the alert's time_of_signal if tos_mjd not available
            time_value = 0
            if tos_mjd:
                time_value = round(t.mjd[0] - tos_mjd, 3)
            else:
                # Fallback: try to calculate using alert time_of_signal
                if alert and alert.time_of_signal:
                    import astropy.time
                    alert_time = astropy.time.Time(alert.time_of_signal)
                    time_value = round(t.mjd[0] - alert_time.mjd, 3)
                else:
                    # Last resort: use days from Unix epoch as a relative measure
                    # This will at least give different time values for different pointings
                    time_value = round(t.mjd[0] - 40587.0, 3)  # Days since Unix epoch (1970-01-01)

            for ccd in sanatized_ccds:
                pointing_footprint = project_footprint(ccd, ra, dec, p.pos_angle)
                pointing_geometries.append(
                    {
                        "polygon": pointing_footprint,
                        "time": time_value,
                    }
                )

        inst_overlays.append(
            {
                "display": True,
                "name": name,
                "color": color,
                "contours": pointing_geometries,
            }
        )

    # Cache the result
    set_cached_file(cache_key, inst_overlays, settings)

    return inst_overlays
