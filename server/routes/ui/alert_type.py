"""Alert type endpoint."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert

router = APIRouter(tags=["UI"])


@router.get("/ajax_alerttype")
async def ajax_get_eventcontour(
    urlid: str,
    db: Session = Depends(get_db)
):
    """Get event contour and alert information."""
    from server.utils.function import get_farrate_farunit, polygons2footprints
    from server.utils.gwtm_io import download_gwtm_file
    from server.config import settings
    import pandas as pd
    
    # Parse the URL ID to get alert ID and alert type
    url_parts = urlid.split('_')
    alert_id = url_parts[0]
    alert_type = url_parts[1]
    if len(url_parts) > 2:
        alert_type += url_parts[2]
    
    # Get the alert
    alert = db.query(GWAlert).filter(GWAlert.id == int(alert_id)).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Determine storage path
    s3path = 'fit' if alert.role == 'observation' else 'test'
    
    # Format FAR (False Alarm Rate) for human readability
    human_far = ""
    if alert.far != 0:
        far_rate, far_unit = get_farrate_farunit(alert.far)
        human_far = f"once per {round(far_rate, 2)} {far_unit}"
    
    # Format time coincidence FAR
    human_time_coinc_far = ""
    if alert.time_coincidence_far != 0 and alert.time_coincidence_far is not None:
        time_coinc_farrate, time_coinc_farunit = get_farrate_farunit(alert.time_coincidence_far)
        time_coinc_farrate = round(time_coinc_farrate, 2)
        human_time_coinc_far = f"once per {round(time_coinc_farrate, 2)} {time_coinc_farunit}"
    
    # Format time-sky position coincidence FAR
    human_time_skypos_coinc_far = ""
    if alert.time_sky_position_coincidence_far != 0 and alert.time_sky_position_coincidence_far is not None:
        time_skypos_coinc_farrate, time_skypos_coinc_farunit = get_farrate_farunit(alert.time_sky_position_coincidence_far)
        time_skypos_coinc_farrate = round(time_skypos_coinc_farrate, 2)
        human_time_skypos_coinc_far = f"once per {round(time_skypos_coinc_farrate, 2)} {time_skypos_coinc_farunit}"
    
    # Format time difference
    if alert.time_difference is not None:
        alert.time_difference = round(alert.time_difference, 3)
    
    # Format distance and error
    distance_with_error = ""
    if alert.distance is not None:
        alert.distance = round(alert.distance, 3)
        if alert.distance_error is not None:
            alert.distance_error = round(alert.distance_error, 3)
            distance_with_error = f"{alert.distance} ± {alert.distance_error} Mpc"
    
    # Format areas
    if alert.area_50 is not None:
        alert.area_50 = f"{round(alert.area_50, 3)} deg<sup>2</sup>"
    if alert.area_90 is not None:
        alert.area_90 = f"{round(alert.area_90, 3)} deg<sup>2</sup>"
    
    # Round probability values
    if alert.prob_bns is not None:
        alert.prob_bns = round(alert.prob_bns, 5)
    if alert.prob_nsbh is not None:
        alert.prob_nsbh = round(alert.prob_nsbh, 5)
    if alert.prob_gap is not None:
        alert.prob_gap = round(alert.prob_gap, 5)
    if alert.prob_bbh is not None:
        alert.prob_bbh = round(alert.prob_bbh, 5)
    if alert.prob_terrestrial is not None:
        alert.prob_terrestrial = round(alert.prob_terrestrial, 5)
    if alert.prob_hasns is not None:
        alert.prob_hasns = round(alert.prob_hasns, 5)
    if alert.prob_hasremenant is not None:
        alert.prob_hasremenant = round(alert.prob_hasremenant, 5)
    
    # Prepare detection overlays
    detection_overlays = []
    path_info = alert.graceid + '-' + alert_type
    
    # Try to download contours
    contour_path = f'{s3path}/{path_info}-contours-smooth.json'
    try:
        contours_data = download_gwtm_file(contour_path, source=settings.STORAGE_BUCKET_SOURCE, config=settings)
        contours_df = pd.read_json(contours_data)
        
        contour_geometry = []
        for contour in contours_df['features']:
            contour_geometry.extend(contour['geometry']['coordinates'])
        
        detection_overlays.append({
            "display": True,
            "name": "GW Contour",
            "color": '#e6194B',
            "contours": polygons2footprints(contour_geometry, 0)
        })
    except Exception as e:
        print(f"Error downloading contours: {str(e)}")
    
    # Prepare payload
    payload = {
        'hidden_alertid': alert_id,
        'detection_overlays': detection_overlays,
        'alert_group': alert.group,
        'alert_detectors': alert.detectors,
        'alert_time_of_signal': alert.time_of_signal,
        'alert_timesent': alert.timesent,
        'alert_human_far': human_far,
        'alert_distance_plus_error': distance_with_error,
        'alert_centralfreq': alert.centralfreq,
        'alert_duration': alert.duration,
        'alert_prob_bns': alert.prob_bns,
        'alert_prob_nsbh': alert.prob_nsbh,
        'alert_prob_gap': alert.prob_gap,
        'alert_prob_bbh': alert.prob_bbh,
        'alert_prob_terrestrial': alert.prob_terrestrial,
        'alert_prob_hasns': alert.prob_hasns,
        'alert_prob_hasremenant': alert.prob_hasremenant,
        'alert_area_50': alert.area_50,
        'alert_area_90': alert.area_90,
        'alert_avgra': alert.avgra,
        'alert_avgdec': alert.avgdec,
        'alert_gcn_notice_id': alert.gcn_notice_id,
        'alert_ivorn': alert.ivorn,
        'alert_ext_coinc_observatory': alert.ext_coinc_observatory,
        'alert_ext_coinc_search': alert.ext_coinc_search,
        'alert_time_difference': alert.time_difference,
        'alert_time_coincidence_far': human_time_coinc_far,
        'alert_time_sky_position_coincidence_far': human_time_skypos_coinc_far,
        'selected_alert_type': alert.alert_type
    }
    
    return payload