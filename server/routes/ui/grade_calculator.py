"""Grade calculator endpoint."""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_alert import GWAlert
from server.auth.auth import get_current_user

router = APIRouter(tags=["UI"])


@router.post("/ajax_grade_calculator")
async def grade_calculator(
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Calculate grades for pointings based on various metrics."""
    data = await request.json()

    pointing_ids = data.get("pointing_ids", [])
    if not pointing_ids:
        raise HTTPException(status_code=400, detail="No pointings specified")

    # Get the pointings
    pointings = db.query(Pointing).filter(Pointing.id.in_(pointing_ids)).all()

    # Calculate grades for each pointing based on actual metrics
    results = {}

    # Get associated GW alerts for time grading
    pointing_events = (
        db.query(PointingEvent).filter(PointingEvent.pointingid.in_(pointing_ids)).all()
    )

    event_map = {pe.pointingid: pe.graceid for pe in pointing_events}

    for pointing in pointings:
        # Get the associated GW alert
        graceid = event_map.get(pointing.id)
        time_grade = 0.5  # Default
        position_grade = 0.5  # Default
        depth_grade = 0.5  # Default

        if graceid:
            alert = db.query(GWAlert).filter(GWAlert.graceid == graceid).first()
            if alert and alert.time_of_signal and pointing.time:
                # Time grade: earlier observations get higher grades
                time_diff_hours = (
                    pointing.time - alert.time_of_signal
                ).total_seconds() / 3600
                if time_diff_hours <= 1:
                    time_grade = 1.0
                elif time_diff_hours <= 6:
                    time_grade = 0.9
                elif time_diff_hours <= 24:
                    time_grade = 0.7
                elif time_diff_hours <= 72:
                    time_grade = 0.5
                else:
                    time_grade = 0.3

        # Position grade: simplified calculation based on alert coordinates
        if graceid and alert and alert.avgra is not None and alert.avgdec is not None:
            # Get pointing coordinates
            position_result = (
                db.query(func.ST_AsText(Pointing.position))
                .filter(Pointing.id == pointing.id)
                .first()
            )
            if position_result and position_result[0]:
                try:
                    pos_str = position_result[0]
                    pointing_ra = float(pos_str.split("POINT(")[1].split(" ")[0])
                    pointing_dec = float(pos_str.split(" ")[1].split(")")[0])

                    # Simple angular distance calculation (rough approximation)
                    ra_diff = abs(pointing_ra - alert.avgra)
                    dec_diff = abs(pointing_dec - alert.avgdec)
                    angular_dist = (ra_diff**2 + dec_diff**2) ** 0.5

                    # Grade based on distance from alert center
                    if angular_dist <= 5:
                        position_grade = 1.0
                    elif angular_dist <= 15:
                        position_grade = 0.8
                    elif angular_dist <= 30:
                        position_grade = 0.6
                    else:
                        position_grade = 0.3
                except:
                    position_grade = 0.5

        # Depth grade: deeper observations get higher grades
        if pointing.depth is not None:
            if pointing.depth >= 23:
                depth_grade = 1.0
            elif pointing.depth >= 21:
                depth_grade = 0.8
            elif pointing.depth >= 19:
                depth_grade = 0.6
            else:
                depth_grade = 0.4

        # Calculate weighted overall grade
        overall_grade = time_grade * 0.4 + position_grade * 0.4 + depth_grade * 0.2

        results[pointing.id] = {
            "time_grade": round(time_grade, 2),
            "position_grade": round(position_grade, 2),
            "depth_grade": round(depth_grade, 2),
            "overall_grade": round(overall_grade, 2),
        }

    return results
