"""Coverage calculator endpoint."""

from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from server.db.database import get_db
from server.auth.auth import get_current_user

router = APIRouter(tags=["UI"])


@router.post("/ajax_coverage_calculator")
async def coverage_calculator(
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Calculate coverage statistics for an alert using real HEALPix implementation."""
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
    from server.db.models.pointing_event import PointingEvent
    from server.utils.function import sanatize_pointing, sanatize_footprint_ccds, project_footprint
    from server.utils.gwtm_io import download_gwtm_file, get_cached_file, set_cached_file
    from server.config import settings
    
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
    
    # Create cache key
    cache_params = f"{graceid}_{mappathinfo}_{inst_cov}_{depth}_{depth_unit}_{approx_cov}"
    cache_key = f"coverage_calc_{hashlib.sha1(cache_params.encode()).hexdigest()}"
    
    # Try to get from cache first
    cached_result = get_cached_file(cache_key, settings)
    if cached_result:
        times, probs, areas = cached_result['times'], cached_result['probs'], cached_result['areas']
    else:
        # Calculate coverage using real HEALPix implementation
        times, probs, areas = await calculate_healpix_coverage(
            graceid, mappathinfo, inst_cov, band_cov, depth, depth_unit, 
            approx_cov, spec_range_low, spec_range_high, spec_range_type, 
            cache_key, db
        )
    
    # Generate the plot
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
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


async def calculate_healpix_coverage(graceid, mappathinfo, inst_cov, band_cov, depth, depth_unit, 
                                   approx_cov, spec_range_low, spec_range_high, spec_range_type, 
                                   cache_key, db):
    """Calculate real HEALPix-based coverage statistics."""
    import numpy as np
    import healpy as hp
    import astropy.coordinates
    import tempfile
    from server.utils.function import sanatize_pointing, sanatize_footprint_ccds, project_footprint, isFloat
    from server.utils.gwtm_io import download_gwtm_file, set_cached_file
    from server.config import settings
    from server.db.models.pointing_event import PointingEvent
    from server.db.models.pointing import Pointing
    from server.db.models.gw_alert import GWAlert
    from server.core.enums.pointing_status import pointing_status as pointing_status_enum
    
    # Handle instrument approximations for large-scale instruments
    approx_dict = {
        47: 76,  # ZTF to ZTF_approx  
        38: 98   # DECam to DECam_approx
    }
    
    areas = []
    times = []
    probs = []
    
    # Download and read the HEALPix map
    try:
        with tempfile.NamedTemporaryFile() as f:
            tmpdata = download_gwtm_file(mappathinfo, source=settings.STORAGE_BUCKET_SOURCE, config=settings, decode=False)
            f.write(tmpdata)
            GWmap = hp.read_map(f.name)
            nside = hp.npix2nside(len(GWmap))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Calculator ERROR: Map not found. {str(e)}")
    
    # Build pointing filter
    pointing_filter = []
    pointing_filter.append(PointingEvent.graceid == graceid)
    pointing_filter.append(Pointing.status == pointing_status_enum.completed)
    pointing_filter.append(PointingEvent.pointingid == Pointing.id)
    pointing_filter.append(Pointing.instrumentid != 49)  # Exclude instrument 49
    
    if inst_cov:
        insts_cov = [int(x) for x in inst_cov.split(',')]
        pointing_filter.append(Pointing.instrumentid.in_(insts_cov))
    
    if depth_unit and depth_unit != 'None':
        from server.core.enums.depth_unit import depth_unit as depth_unit_enum
        try:
            unit_enum = depth_unit_enum[depth_unit]
            pointing_filter.append(Pointing.depth_unit == unit_enum)
        except KeyError:
            pass
        
    if depth and isFloat(depth):
        depth_val = float(depth)
        if 'mag' in depth_unit:
            pointing_filter.append(Pointing.depth >= depth_val)
        elif 'flux' in depth_unit:
            pointing_filter.append(Pointing.depth <= depth_val)
        else:
            raise HTTPException(status_code=400, detail="Unknown depth unit")
    
    # Handle spectral range filtering if provided
    if spec_range_low and spec_range_high and spec_range_type:
        from server.utils.spectral import SpectralRangeHandler
        from server.utils.function import isFloat
        
        try:
            slow, shigh = None, None
            if isFloat(spec_range_low) and isFloat(spec_range_high):
                slow = float(spec_range_low)
                shigh = float(spec_range_high)
                
                # Convert spectral range to common units and apply filter
                if spec_range_type == 'wavelength':
                    from server.core.enums.wavelength_units import wavelength_units
                    unit = [x for x in wavelength_units if spec_range_unit == x.name][0]
                    scale = wavelength_units.get_scale(unit)
                    slow = slow * scale
                    shigh = shigh * scale
                    stype = SpectralRangeHandler.spectralrangetype.wavelength
                elif spec_range_type == 'energy':
                    from server.core.enums.energy_units import energy_units
                    unit = [x for x in energy_units if spec_range_unit == x.name][0]
                    scale = energy_units.get_scale(unit)
                    slow = slow * scale
                    shigh = shigh * scale
                    stype = SpectralRangeHandler.spectralrangetype.energy
                elif spec_range_type == 'frequency':
                    from server.core.enums.frequency_units import frequency_units
                    unit = [x for x in frequency_units if spec_range_unit == x.name][0]
                    scale = frequency_units.get_scale(unit)
                    slow = slow * scale
                    shigh = shigh * scale
                    stype = SpectralRangeHandler.spectralrangetype.frequency
                else:
                    stype = None
                
                if stype is not None:
                    pointing_filter.append(Pointing.inSpectralRange(slow, shigh, stype))
        except Exception:
            # If spectral filtering fails, continue without it
            pass
    
    # Get sorted pointings
    pointings_sorted = db.query(
        Pointing.id,
        Pointing.instrumentid,
        Pointing.pos_angle,
        func.ST_AsText(Pointing.position).label('position'),
        Pointing.band,
        Pointing.depth,
        Pointing.time
    ).join(
        PointingEvent, PointingEvent.pointingid == Pointing.id
    ).filter(
        *pointing_filter
    ).order_by(
        Pointing.time.asc()
    ).all()
    
    # Get instrument IDs and handle approximations
    instrumentids = [p.instrumentid for p in pointings_sorted]
    
    # Add approximation instruments if needed
    if approx_cov:
        for apid in approx_dict.keys():
            if apid in instrumentids:
                instrumentids.append(approx_dict[apid])
    
    # Get footprint information
    from server.db.models.instrument import FootprintCCD
    footprintinfo = db.query(
        func.ST_AsText(FootprintCCD.footprint).label('footprint'),
        FootprintCCD.instrumentid
    ).filter(
        FootprintCCD.instrumentid.in_(instrumentids)
    ).all()
    
    # Get GW T0 time
    time_of_signal = db.query(
        GWAlert.time_of_signal
    ).filter(
        GWAlert.graceid == graceid,
        GWAlert.time_of_signal.isnot(None)
    ).order_by(
        GWAlert.datecreated.desc()
    ).first()
    
    if not time_of_signal or not time_of_signal[0]:
        raise HTTPException(status_code=400, detail="ERROR: Please contact administrator")
    
    time_of_signal = time_of_signal[0]
    
    # Initialize HEALPix calculation variables
    qps = []
    qpsarea = []
    
    NSIDE4area = 512  # This gives pixarea of 0.013 deg^2 per pixel
    pixarea = hp.nside2pixarea(NSIDE4area, degrees=True)
    
    # Process each pointing
    for p in pointings_sorted:
        ra, dec = sanatize_pointing(p.position)
        
        # Select appropriate footprint based on approximation setting
        if approx_cov and p.instrumentid in approx_dict.keys():
            footprint_ccds = [x.footprint for x in footprintinfo if x.instrumentid == approx_dict[p.instrumentid]]
        else:
            footprint_ccds = [x.footprint for x in footprintinfo if x.instrumentid == p.instrumentid]
        
        sanatized_ccds = sanatize_footprint_ccds(footprint_ccds)
        
        # Process each CCD footprint
        for ccd in sanatized_ccds:
            pointing_footprint = project_footprint(ccd, ra, dec, p.pos_angle)
            
            # Extract RA/Dec coordinates from footprint
            ras_poly = [x[0] for x in pointing_footprint][:-1]
            decs_poly = [x[1] for x in pointing_footprint][:-1]
            
            # Convert to cartesian coordinates for HEALPix
            xyzpoly = astropy.coordinates.spherical_to_cartesian(1, np.deg2rad(decs_poly), np.deg2rad(ras_poly))
            
            # Query HEALPix pixels within the polygon
            qp = hp.query_polygon(nside, np.array(xyzpoly).T, inclusive=True)
            qps.extend(qp)
            
            # Separate calculation for area coverage with higher resolution
            qparea = hp.query_polygon(NSIDE4area, np.array(xyzpoly).T, inclusive=True)
            qpsarea.extend(qparea)
            
            # Deduplicate indices so pixels aren't double-counted
            deduped_indices = list(dict.fromkeys(qps))
            deduped_indices_area = list(dict.fromkeys(qpsarea))
            
            # Calculate area coverage
            area = pixarea * len(deduped_indices_area)
            
            # Calculate probability coverage by summing GW map pixel values
            prob = 0
            for ind in deduped_indices:
                prob += GWmap[ind]
            
            # Calculate elapsed time since GW trigger
            elapsed = (p.time - time_of_signal).total_seconds() / 3600
            
            times.append(elapsed)
            probs.append(prob)
            areas.append(area)
    
    # Cache the results
    cache_file = {
        'times': times,
        'probs': probs,
        'areas': areas,
    }
    set_cached_file(cache_key, cache_file, settings)
    
    return times, probs, areas