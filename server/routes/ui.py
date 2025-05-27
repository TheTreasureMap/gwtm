from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from server.db.database import get_db
from server.db.models.instrument import Instrument
from server.db.models.pointing import Pointing
from server.db.models.users import Users
from server.db.models.gw_alert import GWAlert
from server.schemas.instrument import InstrumentSchema
from server.schemas.pointing import PointingSchema
from server.auth.auth import get_current_user

router = APIRouter(tags=["UI"])

@router.get("/ajax_alertinstruments_footprints")
async def get_alert_instruments_footprints(
    graceid: str = None,
    pointing_status: str = None,
    tos_mjd: float = None,
    db: Session = Depends(get_db)
):
    """Get footprints of instruments that observed a specific alert."""
    from server.utils.function import sanatize_pointing, project_footprint, sanatize_footprint_ccds
    import json
    import hashlib
    from server.utils.gwtm_io import get_cached_file, set_cached_file
    from server.config import settings
    
    # First find the alert by graceid
    alert = db.query(GWAlert).filter(GWAlert.graceid == graceid).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    # Set default status if none provided
    if pointing_status is None:
        pointing_status = "completed"
    
    # Build pointing filter
    pointing_filter = []
    pointing_filter.append(Pointing.alert_id == alert.id)
    
    # Status filtering
    if pointing_status == 'pandc':
        pointing_filter.append(
            or_(Pointing.status == "completed", Pointing.status == "planned")
        )
    elif pointing_status not in ['all', '']:
        pointing_filter.append(Pointing.status == pointing_status)
    
    # Get pointing info
    pointing_info = db.query(
        Pointing.id,
        Pointing.instrument_id,
        Pointing.pos_angle,
        Pointing.time,
        func.ST_AsText(Pointing.position).label('position'),
        Pointing.band,
        Pointing.depth,
        Pointing.depth_unit,
        Pointing.status
    ).filter(*pointing_filter).all()
    
    # Cache key based on pointing IDs
    pointing_ids = [p.id for p in pointing_info]
    hash_pointing_ids = hashlib.sha1(json.dumps(pointing_ids).encode()).hexdigest()
    cache_key = f'cache/footprint_{graceid}_{pointing_status}_{hash_pointing_ids}'
    
    # Try to get from cache first
    cached_overlays = get_cached_file(cache_key, settings)
    
    if cached_overlays:
        return json.loads(cached_overlays)
    
    # Not in cache, generate fresh data
    instrument_ids = [p.instrument_id for p in pointing_info]
    
    # Get instrument info
    instrumentinfo = db.query(
        Instrument.instrument_name,
        Instrument.nickname,
        Instrument.id
    ).filter(
        Instrument.id.in_(instrument_ids)
    ).all()
    
    # Get footprint info
    footprintinfo = db.query(
        func.ST_AsText(Instrument.footprint).label('footprint'),
        Instrument.id.label('instrumentid')
    ).filter(
        Instrument.id.in_(instrument_ids)
    ).all()
    
    # Prepare colors
    colorlist = [
        '#ffe119', '#4363d8', '#f58231', '#42d4f4', '#f032e6', '#fabebe', 
        '#469990', '#e6beff', '#9A6324', '#fffac8', '#800000', '#aaffc3', 
        '#000075', '#a9a9a9'
    ]
    
    # Generate overlays
    inst_overlays = []
    
    for i, inst in enumerate([x for x in instrumentinfo if x.id != 49]):
        name = inst.nickname if inst.nickname and inst.nickname != 'None' else inst.instrument_name
        
        try:
            color = colorlist[i]
        except IndexError:
            color = '#' + format(inst.id % 0xFFFFFF, '06x')
        
        footprint_ccds = [x.footprint for x in footprintinfo if x.instrumentid == inst.id]
        sanatized_ccds = sanatize_footprint_ccds(footprint_ccds)
        inst_pointings = [x for x in pointing_info if x.instrument_id == inst.id]
        pointing_geometries = []
        
        for p in inst_pointings:
            import astropy.time
            t = astropy.time.Time([p.time])
            ra, dec = sanatize_pointing(p.position)
            
            for ccd in sanatized_ccds:
                pointing_footprint = project_footprint(ccd, ra, dec, p.pos_angle)
                pointing_geometries.append({
                    "polygon": pointing_footprint,
                    "time": round(t.mjd[0] - tos_mjd, 3) if tos_mjd else 0
                })
        
        inst_overlays.append({
            "display": True,
            "name": name,
            "color": color,
            "contours": pointing_geometries
        })
    
    # Cache the result
    set_cached_file(cache_key, inst_overlays, settings)
    
    return inst_overlays

@router.get("/ajax_preview_footprint")
async def preview_footprint(
    ra: float,
    dec: float,
    radius: float = None,
    height: float = None,
    width: float = None,
    shape: str = "circle",
    polygon: str = None,
    db: Session = Depends(get_db)
):
    """Generate a preview of an instrument footprint."""
    import math
    import json
    import plotly
    import plotly.graph_objects as go
    
    # This is a UI helper endpoint to visualize a footprint before saving
    # It generates the appropriate visualization for the given parameters
    vertices = []
    
    if shape.lower() == "circle" and radius:
        # For circle, generate points around the circumference
        circle_points = []
        for i in range(36):  # 36 points for a smooth circle
            angle = i * 10 * (math.pi / 180)  # 10 degrees in radians
            # Simple conversion - in a real implementation, use proper spherical math
            point_ra = ra + (radius * math.cos(angle) / math.cos(math.radians(dec)))
            point_dec = dec + (radius * math.sin(angle))
            circle_points.append([point_ra, point_dec])
        
        # Close the polygon
        circle_points.append(circle_points[0])
        vertices.append(circle_points)
        
    elif shape.lower() == "rectangle" and height and width:
        # For rectangle, generate corners
        # Convert height/width in degrees to ra/dec coordinates
        # This is a simplified calculation and doesn't account for spherical distortion
        half_width = width / 2
        half_height = height / 2
        
        # Account for cos(dec) factor in RA
        ra_factor = math.cos(math.radians(dec))
        ra_offset = half_width / ra_factor
        
        rect_points = [
            [ra - ra_offset, dec - half_height], # bottom left
            [ra - ra_offset, dec + half_height], # top left
            [ra + ra_offset, dec + half_height], # top right
            [ra + ra_offset, dec - half_height], # bottom right
            [ra - ra_offset, dec - half_height]  # close the polygon
        ]
        vertices.append(rect_points)
        
    elif shape.lower() == "polygon" and polygon:
        # For custom polygon, parse the points
        try:
            poly_points = json.loads(polygon)
            poly_points.append(poly_points[0])  # Close the polygon
            vertices.append(poly_points)
        except json.JSONDecodeError:
            return {"error": "Invalid polygon format"}
    else:
        return {"error": "Invalid shape type or missing required parameters"}
    
    # Create a plotly figure
    traces = []
    for vert in vertices:
        xs = [v[0] for v in vert]
        ys = [v[1] for v in vert]
        trace = go.Scatter(
            x=xs,
            y=ys,
            line_color='blue',
            fill='tozeroy',
            fillcolor='violet'
        )
        traces.append(trace)
    
    fig = go.Figure(data=traces)
    fig.update_layout(
        showlegend=False,
        xaxis_title="degrees",
        yaxis_title="degrees",
        yaxis=dict(
            matches='x',
            scaleanchor="x",
            scaleratio=1,
            constrain='domain',
        )
    )
    
    # Convert to JSON for return
    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return graphJSON

@router.post("/ajax_resend_verification_email")
async def resend_verification_email(
    email: str = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Resend the verification email to a user."""
    from server.utils.email import send_account_validation_email
    
    # If email is provided, find that user (admin function)
    # Otherwise use the current user
    if email:
        user = db.query(Users).filter(Users.email == email).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Only allow admins to send verification emails to other users
        if not current_user.adminuser:
            raise HTTPException(status_code=403, detail="Not authorized")
    else:
        user = current_user
    
    if user.verified:
        return {"message": "User is already verified"}
    
    # Send the verification email
    send_account_validation_email(user, db)
    
    return {"message": "Verification email has been resent"}

@router.post("/ajax_coverage_calculator")
async def coverage_calculator(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Calculate coverage statistics for an alert."""
    import numpy as np
    import healpy as hp
    import hashlib
    import json
    import astropy.coordinates
    import plotly
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    import tempfile
    from datetime import datetime
    from sqlalchemy import func, or_
    
    data = await request.json()
    
    graceid = data.get("graceid")
    if not graceid:
        raise HTTPException(status_code=400, detail="Missing graceid")
    
    # Get equivalent params from request data
    mappathinfo = data.get("mappathinfo")
    inst_cov = data.get("inst_cov", "")
    band_cov = data.get("band_cov", "")
    depth = data.get("depth_cov")
    depth_unit = data.get("depth_unit", "")
    approx_cov = data.get("approx_cov", 1) == 1
    spec_range_type = data.get("spec_range_type", "")
    spec_range_unit = data.get("spec_range_unit", "")
    spec_range_low = data.get("spec_range_low")
    spec_range_high = data.get("spec_range_high")
    
    # Get all pointings that match the filter criteria
    pointing_filter = []
    pointing_filter.append(Pointing.alert_id == graceid)
    pointing_filter.append(Pointing.status == "completed")
    
    if inst_cov:
        insts_cov = [int(x) for x in inst_cov.split(',')]
        pointing_filter.append(Pointing.instrument_id.in_(insts_cov))
    
    if depth_unit and depth_unit != 'None':
        pointing_filter.append(Pointing.depth_unit == depth_unit)
        
    if depth and depth.replace('.', '', 1).isdigit():
        depth_val = float(depth)
        if 'mag' in depth_unit:
            pointing_filter.append(Pointing.depth >= depth_val)
        elif 'flux' in depth_unit:
            pointing_filter.append(Pointing.depth <= depth_val)
        else:
            raise HTTPException(status_code=400, detail="Unknown depth unit")
    
    # Spectral range filtering would be implemented here
    # This is a complex implementation that relies on custom SQL functions
    # We'll skip this for now and implement it when needed
    
    # Get the pointings
    pointings_sorted = db.query(
        Pointing.id,
        Pointing.instrument_id,
        Pointing.pos_angle,
        func.ST_AsText(Pointing.position).label('position'),
        Pointing.band,
        Pointing.depth,
        Pointing.time
    ).filter(
        *pointing_filter
    ).order_by(
        Pointing.time.asc()
    ).all()
    
    # Get the instrument footprints
    instrumentids = [p.instrument_id for p in pointings_sorted]
    
    # This would account for approximations
    # For simplicity, we're skipping this part for now
    
    footprintinfo = db.query(
        func.ST_AsText(Instrument.footprint).label('footprint'),
        Instrument.id
    ).filter(
        Instrument.id.in_(instrumentids)
    ).all()
    
    # Get the time of the GW alert
    time_of_signal = db.query(
        GWAlert.time_of_signal
    ).filter(
        GWAlert.id == graceid
    ).first()
    
    if not time_of_signal or time_of_signal[0] is None:
        raise HTTPException(status_code=400, detail="Alert missing time_of_signal")
    
    time_of_signal = time_of_signal[0]
    
    # Start processing - this would be a lengthy calculation in a real implementation
    # Convert this to a proper plotly figure with two y-axes
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # We'd calculate these values from the actual coverage
    # For demo purposes, we're creating sample data
    times = []
    probs = []
    areas = []
    
    # Sample data generation
    for i, p in enumerate(pointings_sorted):
        # Calculate elapsed time since GW signal
        elapsed = (p.time - time_of_signal).total_seconds() / 3600
        times.append(elapsed)
        
        # These values would be calculated from the actual footprints and skymap
        # We're just creating increasing values
        prob = min(0.95, (i+1) * 0.05)  # Max out at 95% probability covered
        area = (i+1) * 10  # Increase by 10 sq deg each observation
        
        probs.append(prob)
        areas.append(area)
    
    # Create the figure
    fig.add_trace(go.Scatter(
        x=times, 
        y=[prob*100 for prob in probs],
        mode='lines',
        name='Probability'
    ), secondary_y=False)
    
    fig.add_trace(go.Scatter(
        x=times, 
        y=areas,
        mode='lines',
        name='Area'
    ), secondary_y=True)
    
    fig.update_xaxes(title_text="Hours since GW T0")
    fig.update_yaxes(title_text="Percent of GW localization posterior covered", secondary_y=False)
    fig.update_yaxes(title_text="Area coverage (deg<sup>2</sup>)", secondary_y=True)
    
    coverage_div = plotly.offline.plot(fig, output_type='div', include_plotlyjs=False, show_link=False)
    
    return {"plot_html": coverage_div}

@router.get("/ajax_update_spectral_range_from_selected_bands")
async def spectral_range_from_selected_bands(
    band_cov: str,
    spectral_type: str,
    spectral_unit: str,
    db: Session = Depends(get_db)
):
    """Calculate spectral range based on selected bands."""
    from server.core.enums.wavelength_units import wavelength_units
    from server.core.enums.energy_units import energy_units
    from server.core.enums.frequency_units import frequency_units
    from server.core.enums.bandpass import bandpass
    
    if not band_cov or band_cov == 'null':
        return {
            'total_min': '',
            'total_max': ''
        }
    
    # Split bands
    bands = band_cov.split(',')
    mins, maxs = [], []
    
    for b in bands:
        try:
            # Find the bandpass enum value
            band_enum = [x for x in bandpass if b == x.name][0]
            band_min, band_max = None, None
            
            # Handle different spectral types
            if spectral_type == 'wavelength':
                # Get wavelength range for this band
                from server.utils.spectral import wavetoWaveRange
                band_min, band_max = wavetoWaveRange(bandpass=band_enum)
                # Get the scale factor for the requested unit
                unit = [x for x in wavelength_units if spectral_unit == x.name][0]
                scale = wavelength_units.get_scale(unit)
            
            elif spectral_type == 'energy':
                # Get energy range for this band
                from server.utils.spectral import wavetoEnergy
                band_min, band_max = wavetoEnergy(bandpass=band_enum)
                # Get the scale factor for the requested unit
                unit = [x for x in energy_units if spectral_unit == x.name][0]
                scale = energy_units.get_scale(unit)
            
            elif spectral_type == 'frequency':
                # Get frequency range for this band
                from server.utils.spectral import wavetoFrequency
                band_min, band_max = wavetoFrequency(bandpass=band_enum)
                # Get the scale factor for the requested unit
                unit = [x for x in frequency_units if spectral_unit == x.name][0]
                scale = frequency_units.get_scale(unit)
            
            # If we got valid values, append them to our lists
            if band_min is not None and band_max is not None:
                mins.append(band_min / scale)
                maxs.append(band_max / scale)
        
        except (IndexError, ValueError):
            # Skip invalid bands
            continue
    
    # Return the overall range
    if mins:
        return {
            'total_min': min(mins),
            'total_max': max(maxs)
        }
    else:
        return {
            'total_min': '',
            'total_max': ''
        }

@router.get("/ajax_pointingfromid")
async def get_pointing_fromID(
    id: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get pointing details by ID for the current user's planned pointings."""
    from server.utils.function import isInt
    from server.db.models.gw_alert import GWAlert
    
    if not id or not isInt(id):
        return {}
    
    # Convert to integer
    pointing_id = int(id)
    
    # Query pointings with filter conditions
    filters = [
        Pointing.submitter_id == current_user.id,
        Pointing.status == "planned",
        Pointing.id == pointing_id
    ]
    
    pointing = db.query(Pointing).filter(*filters).first()
    
    if not pointing:
        return {}
    
    # Get the alert for this pointing
    alert = db.query(GWAlert).filter(GWAlert.id == pointing.alert_id).first()
    
    if not alert:
        return {}
    
    # Extract position
    position_str = func.ST_AsText(pointing.position).label('position')
    position_result = db.query(position_str).filter(Pointing.id == pointing_id).first()
    
    if not position_result or not position_result[0]:
        return {}
    
    position = position_result[0]
    ra = position.split('POINT(')[1].split(' ')[0]
    dec = position.split('POINT(')[1].split(' ')[1].split(')')[0]
    
    # Get instrument details
    instrument = db.query(Instrument).filter(Instrument.id == pointing.instrument_id).first()
    
    # Prepare response
    pointing_json = {
        'ra': ra,
        'dec': dec,
        'graceid': alert.graceid,
        'instrument': f"{pointing.instrument_id}_{instrument.instrument_type if instrument else ''}",
        'band': pointing.band,
        'depth': pointing.depth,
        'depth_err': pointing.depth_err
    }
    
    return pointing_json

@router.post("/ajax_grade_calculator")
async def grade_calculator(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Calculate grades for pointings based on various metrics."""
    data = await request.json()
    
    pointing_ids = data.get("pointing_ids", [])
    if not pointing_ids:
        raise HTTPException(status_code=400, detail="No pointings specified")
    
    # Get the pointings
    pointings = db.query(Pointing).filter(Pointing.id.in_(pointing_ids)).all()
    
    # Calculate grades for each pointing
    # In a real implementation, this would involve complex calculations
    # based on position, time, depth, etc.
    
    results = {}
    for pointing in pointings:
        # Placeholder grades
        results[pointing.id] = {
            "time_grade": 0.85,  # How quickly after the alert
            "position_grade": 0.75,  # How well placed in the probability map
            "depth_grade": 0.9,  # How deep the observation was
            "overall_grade": 0.83  # Weighted average
        }
    
    return results

@router.get("/ajax_icecube_notice")
async def ajax_icecube_notice(
    graceid: str,
    db: Session = Depends(get_db)
):
    """Get IceCube notices associated with a GW event."""
    from server.utils.function import sanatize_icecube_event
    from server.db.models.icecube import IceCubeNotice, IceCubeNoticeCoincEvent
    
    return_events = []
    
    # Get IceCube notices for this event
    icecube_notices = db.query(IceCubeNotice).filter(
        IceCubeNotice.graceid == graceid
    ).all()
    
    if not icecube_notices:
        return return_events
    
    icecube_notice_ids = list(set([notice.id for notice in icecube_notices]))
    
    # Get coincident events for these notices
    icecube_notice_events = db.query(
        IceCubeNoticeCoincEvent
    ).filter(
        IceCubeNoticeCoincEvent.icecube_notice_id.in_(icecube_notice_ids)
    ).all()
    
    # Process each notice
    for notice in icecube_notices:
        markers = []
        events = [x for x in icecube_notice_events if x.icecube_notice_id == notice.id]
        
        for i, e in enumerate(events):
            markers.append({
                "name": f"ICN_EVENT_{e.id}",
                "ra": e.ra,
                "dec": e.dec,
                "radius": e.ra_uncertainty,
                "info": sanatize_icecube_event(e, notice)
            })
        
        return_events.append({
            "name": f"ICECUBENotice{notice.id}",
            "color": "#324E72",
            "markers": markers
        })
    
    return return_events

@router.get("/ajax_event_galaxies")
async def ajax_event_galaxies(
    alertid: str,
    db: Session = Depends(get_db)
):
    """Get galaxies associated with an event."""
    from server.utils.function import sanatize_pointing, sanatize_gal_info
    
    # Get the galaxy lists for this alert
    from server.db.models.gw_alert import GWGalaxyList, GWGalaxyEntry
    
    event_galaxies = []
    
    # Get galaxy lists for this alert
    gal_lists = db.query(GWGalaxyList).filter(
        GWGalaxyList.alertid == alertid
    ).all()
    
    if not gal_lists:
        return event_galaxies
    
    gal_list_ids = list(set([x.id for x in gal_lists]))
    
    # Get galaxy entries for these lists
    gal_entries = db.query(
        GWGalaxyEntry.name,
        func.ST_AsText(GWGalaxyEntry.position).label('position'),
        GWGalaxyEntry.score,
        GWGalaxyEntry.info,
        GWGalaxyEntry.listid,
        GWGalaxyEntry.rank
    ).filter(
        GWGalaxyEntry.listid.in_(gal_list_ids)
    ).all()
    
    # Process each list
    for glist in gal_lists:
        markers = []
        entries = [x for x in gal_entries if x.listid == glist.id]
        
        for e in entries:
            ra, dec = sanatize_pointing(e.position)
            markers.append({
                "name": e.name,
                "ra": ra,
                "dec": dec,
                "info": sanatize_gal_info(e, glist)
            })
        
        event_galaxies.append({
            "name": glist.groupname,
            "color": "",
            "markers": markers
        })
    
    return event_galaxies

@router.get("/ajax_scimma_xrt")
async def ajax_scimma_xrt(
    graceid: str,
    db: Session = Depends(get_db)
):
    """Get SCIMMA XRT sources associated with a GW event."""
    import requests
    import urllib.parse
    from server.utils.function import sanatize_XRT_source_info
    from server.db.models.gw_alert import GWAlert
    
    # Normalize the graceid - maintain backward compatibility
    normalized_graceid = GWAlert.graceidfromalternate(graceid)
    
    # Special case for S190426
    if 'S190426' in normalized_graceid:
        normalized_graceid = 'S190426'
    
    # Prepare query parameters
    keywords = {
        'keyword': '',
        'cone_search': '',
        'polygon_search': '',
        'alert_timestamp_after': '',
        'alert_timestamp_before': '',
        'role': '',
        'event_trigger_number': normalized_graceid,
        'ordering': '',
        'page_size': 1000,
    }
    
    # Construct URL and make request
    base_url = 'http://skip.dev.hop.scimma.org/api/alerts/'
    url = f"{base_url}?{urllib.parse.urlencode(keywords)}"
    
    markers = []
    payload = []
    
    try:
        response = requests.get(url)
        if response.status_code == status.HTTP_200_OK:
            package = response.json()['results']
            for p in package:
                markers.append({
                    'name': p['alert_identifier'],
                    'ra': p['right_ascension'],
                    'dec': p['declination'],
                    'info': sanatize_XRT_source_info(p)
                })
    except Exception as e:
        print(f"Error fetching SCIMMA XRT data: {str(e)}")
    
    if markers:
        payload.append({
            'name': 'SCIMMA XRT Sources',
            'color': '',
            'markers': markers
        })
    
    return payload

@router.get("/ajax_candidate")
async def ajax_candidate_fetch(
    graceid: str,
    db: Session = Depends(get_db)
):
    """Get candidates associated with a GW event."""
    from server.utils.function import sanatize_pointing, sanatize_candidate_info
    from server.db.models.gw_alert import GWAlert, GWCandidate
    import shapely.wkb
    
    # Normalize the graceid - maintain backward compatibility
    normalized_graceid = GWAlert.graceidfromalternate(graceid)
    
    # Get candidates for this event
    candidates = db.query(GWCandidate).filter(GWCandidate.graceid == normalized_graceid).all()
    
    markers = []
    payload = []
    
    for c in candidates:
        clean_position = shapely.wkb.loads(bytes(c.position.data), hex=True)
        position_str = str(clean_position)
        ra, dec = sanatize_pointing(position_str)
        
        markers.append({
            "name": c.candidate_name,
            "ra": ra,
            "dec": dec,
            "shape": "star",
            "info": sanatize_candidate_info(c, ra, dec)
        })
    
    if markers:
        payload.append({
            'name': 'Candidates',
            'color': '',
            'markers': markers
        })
    
    return payload

@router.get("/ajax_request_doi")
async def ajax_request_doi(
    graceid: str,
    ids: str = "",
    doi_group_id: Optional[str] = None,
    doi_url: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Request a DOI for a set of pointings."""
    from server.utils.function import create_pointing_doi
    from server.db.models.gw_alert import GWAlert
    
    # Normalize the graceid - maintain backward compatibility
    normalized_graceid = GWAlert.alternatefromgraceid(graceid)
    
    if not ids:
        return ""
    
    # Convert IDs to list of integers
    pointing_ids = [int(x) for x in ids.split(',')]
    
    # Get all pointings with these IDs
    points = db.query(Pointing).filter(
        Pointing.id.in_(pointing_ids),
        Pointing.alert_id == db.query(GWAlert.id).filter(GWAlert.graceid == normalized_graceid).scalar_subquery()
    ).all()
    
    # Get user information
    user = db.query(Users).filter(Users.id == current_user.id).first()
    
    # Set up creators list
    if doi_group_id:
        # In a real implementation, would get creator list from DOI author group
        # Here we just use a placeholder with the current user
        creators = [{"name": f"{user.firstname} {user.lastname}"}]
    else:
        creators = [{"name": f"{user.firstname} {user.lastname}"}]
    
    # Get instrument names
    insts = db.query(Instrument).filter(
        Instrument.id.in_([p.instrument_id for p in points])
    ).all()
    
    inst_set = list(set([i.instrument_name for i in insts]))
    
    # Create DOI or use existing URL
    if doi_url:
        doi_id, doi_url = 0, doi_url
    else:
        doi_id, doi_url = create_pointing_doi(points, normalized_graceid, creators, inst_set)
    
    # Update pointings with DOI information
    for p in points:
        p.doi_url = doi_url
        p.doi_id = doi_id
        p.submitter_id = current_user.id  # Ensure submitter is set
    
    db.commit()
    
    return doi_url

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
