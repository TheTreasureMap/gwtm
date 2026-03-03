"""Renormalize skymap endpoint."""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from server.db.database import get_db

router = APIRouter(tags=["UI"])


@router.get("/ajax_renormalize_skymap")
async def renormalize_skymap(
    graceid: str = Query(...),
    alert_id: int = Query(...),
    approx_cov: int = Query(default=1),
    inst_cov: str = Query(default=""),
    inst_plan: str = Query(default=""),
    depth_cov: str = Query(default=None),
    depth_unit: str = Query(default=""),
    band_cov: str = Query(default=""),
    spec_range_type: str = Query(default=""),
    spec_range_unit: str = Query(default=""),
    spec_range_low: str = Query(default=None),
    spec_range_high: str = Query(default=None),
    download: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """Renormalize GW skymap by masking covered pixels and recalculating contours."""
    import numpy as np
    import healpy as hp
    import hashlib
    import json
    import tempfile
    import astropy.coordinates
    from io import BytesIO

    from server.db.models.pointing import Pointing
    from server.db.models.pointing_event import PointingEvent
    from server.db.models.gw_alert import GWAlert
    from server.db.models.instrument import FootprintCCD
    from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum
    from server.utils.function import (
        sanatize_pointing,
        sanatize_footprint_ccds,
        project_footprint,
        isFloat,
    )
    from server.utils.gwtm_io import (
        download_gwtm_file,
        get_cached_file,
        set_cached_file,
    )
    from server.config import settings

    # Resolve alternate graceid
    alert = db.query(GWAlert).filter(GWAlert.graceid == graceid).first()
    if not alert:
        alert = db.query(GWAlert).filter(GWAlert.alternateid == graceid).first()
        if alert:
            graceid = alert.graceid
        else:
            raise HTTPException(status_code=404, detail="Alert not found")

    # Build pointing filter
    pointing_filter = []
    pointing_filter.append(PointingEvent.graceid == graceid)
    pointing_filter.append(PointingEvent.pointingid == Pointing.id)
    pointing_filter.append(Pointing.instrumentid != 49)

    # Completed instruments
    comp_mask = Pointing.status == pointing_status_enum.completed
    if inst_cov:
        insts_cov = [int(x) for x in inst_cov.split(",") if x.strip()]
        comp_mask = comp_mask & Pointing.instrumentid.in_(insts_cov)

    # Planned instruments
    if inst_plan:
        plan_mask = Pointing.status == pointing_status_enum.planned
        insts_plan = [int(x) for x in inst_plan.split(",") if x.strip()]
        plan_mask = plan_mask & Pointing.instrumentid.in_(insts_plan)
        pointing_filter.append(or_(comp_mask, plan_mask))
    else:
        pointing_filter.append(comp_mask)

    # Depth filter
    if depth_unit and depth_unit not in ("None", ""):
        from server.core.enums.depthunit import DepthUnit as depth_unit_enum
        try:
            unit_enum = depth_unit_enum[depth_unit]
            pointing_filter.append(Pointing.depth_unit == unit_enum)
        except KeyError:
            pass
    if depth_cov and isFloat(depth_cov):
        depth_val = float(depth_cov)
        if "mag" in depth_unit:
            pointing_filter.append(Pointing.depth >= depth_val)
        elif "flux" in depth_unit:
            pointing_filter.append(Pointing.depth <= depth_val)

    # Spectral range filter
    if spec_range_low and spec_range_high and spec_range_type:
        from server.utils.spectral import SpectralRangeHandler
        try:
            if isFloat(spec_range_low) and isFloat(spec_range_high):
                slow = float(spec_range_low)
                shigh = float(spec_range_high)
                if spec_range_type == "wavelength":
                    from server.core.enums.wavelengthunits import WavelengthUnits as wu
                    unit = [x for x in wu if spec_range_unit == x.name][0]
                    slow *= wu.get_scale(unit)
                    shigh *= wu.get_scale(unit)
                    stype = SpectralRangeHandler.spectralrangetype.wavelength
                elif spec_range_type == "energy":
                    from server.core.enums.energyunits import EnergyUnits as eu
                    unit = [x for x in eu if spec_range_unit == x.name][0]
                    slow *= eu.get_scale(unit)
                    shigh *= eu.get_scale(unit)
                    stype = SpectralRangeHandler.spectralrangetype.energy
                elif spec_range_type == "frequency":
                    from server.core.enums.frequencyunits import FrequencyUnits as fu
                    unit = [x for x in fu if spec_range_unit == x.name][0]
                    slow *= fu.get_scale(unit)
                    shigh *= fu.get_scale(unit)
                    stype = SpectralRangeHandler.spectralrangetype.frequency
                else:
                    stype = None
                if stype is not None:
                    pointing_filter.append(Pointing.inSpectralRange(slow, shigh, stype))
        except Exception:
            pass

    pointings_sorted = (
        db.query(
            Pointing.id,
            Pointing.instrumentid,
            Pointing.pos_angle,
            func.ST_AsText(Pointing.position).label("position"),
            Pointing.time,
        )
        .join(PointingEvent, PointingEvent.pointingid == Pointing.id)
        .filter(*pointing_filter)
        .order_by(Pointing.time.asc())
        .all()
    )

    if not pointings_sorted:
        # No pointings selected — return empty payload
        return {"detection_overlays": []}

    # Get skymap URL from the specific alert version
    specific_alert = db.query(GWAlert).filter(GWAlert.id == alert_id).first()
    mappathinfo = specific_alert.skymap_fits_url if specific_alert else alert.skymap_fits_url
    if not mappathinfo:
        raise HTTPException(status_code=400, detail="No skymap URL found for this alert")

    # Cache key based on pointing IDs + params
    pointing_ids = sorted([p.id for p in pointings_sorted])
    cache_params = f"{graceid}_{alert_id}_{approx_cov}_{hashlib.sha1(json.dumps(pointing_ids).encode()).hexdigest()}"
    cache_key = f"normed_skymap_{cache_params}"

    # Instrument approximations (ZTF→ZTF_approx, DECam→DECam_approx)
    approx_dict = {47: 76, 38: 98}

    # Get footprint CCDs
    instrument_ids = list({p.instrumentid for p in pointings_sorted})
    if approx_cov == 1:
        for apid in approx_dict:
            if apid in instrument_ids:
                instrument_ids.append(approx_dict[apid])

    footprintinfo = (
        db.query(
            func.ST_AsText(FootprintCCD.footprint).label("footprint"),
            FootprintCCD.instrumentid,
        )
        .filter(FootprintCCD.instrumentid.in_(instrument_ids))
        .all()
    )

    # Download and read the HEALPix map
    try:
        with tempfile.NamedTemporaryFile(suffix=".fits") as f:
            tmpdata = download_gwtm_file(
                mappathinfo,
                source=settings.STORAGE_BUCKET_SOURCE,
                config=settings,
                decode=False,
            )
            f.write(tmpdata)
            f.flush()
            GWmap = hp.read_map(f.name)
            nside = hp.npix2nside(len(GWmap))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Map not found: {str(e)}")

    # Mask covered pixels
    covered_pixels = set()
    for p in pointings_sorted:
        ra, dec = sanatize_pointing(p.position)
        if approx_cov == 1 and p.instrumentid in approx_dict:
            fp_ccds = [x.footprint for x in footprintinfo if x.instrumentid == approx_dict[p.instrumentid]]
        else:
            fp_ccds = [x.footprint for x in footprintinfo if x.instrumentid == p.instrumentid]
        for ccd in sanatize_footprint_ccds(fp_ccds):
            footprint = project_footprint(ccd, ra, dec, p.pos_angle)
            ras_poly = [x[0] for x in footprint][:-1]
            decs_poly = [x[1] for x in footprint][:-1]
            xyzpoly = astropy.coordinates.spherical_to_cartesian(
                1, np.deg2rad(decs_poly), np.deg2rad(ras_poly)
            )
            qp = hp.query_polygon(nside, np.array(xyzpoly).T, inclusive=True)
            covered_pixels.update(qp.tolist())

    if download:
        # Build renormalized FITS file
        import astropy.io.fits

        normed = GWmap.copy()
        for pix in covered_pixels:
            normed[pix] = 0.0
        total = normed.sum()
        if total > 0:
            normed /= total

        nside_out = hp.npix2nside(len(normed))
        header = astropy.io.fits.Header()
        header["PIXTYPE"] = "HEALPIX"
        header["ORDERING"] = "RING"
        header["NSIDE"] = nside_out
        header["FIRSTPIX"] = 0
        header["LASTPIX"] = len(normed) - 1
        hdu = astropy.io.fits.BinTableHDU.from_columns(
            [astropy.io.fits.Column(name="PROB", format="E", array=normed)],
            header=header,
        )
        hdul = astropy.io.fits.HDUList([astropy.io.fits.PrimaryHDU(), hdu])
        buf = BytesIO()
        hdul.writeto(buf)
        buf.seek(0)
        filename = f"{cache_key}.fits"
        return StreamingResponse(
            buf,
            media_type="application/fits",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # Visualize: calculate 50% and 90% contours from renormalized map
    # Try cache first
    cache_key_path = f"cache/{cache_key}_contours"
    cached = get_cached_file(cache_key_path, settings)
    if cached:
        contour_data = json.loads(cached) if isinstance(cached, str) else cached
    else:
        normed = GWmap.copy()
        for pix in covered_pixels:
            normed[pix] = 0.0
        total = normed.sum()
        if total > 0:
            normed /= total

        contour_data = _calculate_contours(normed, nside)
        set_cached_file(cache_key_path, contour_data, settings)

    detection_overlays = [
        {
            "display": True,
            "name": "GW Contour (renormalized)",
            "color": "#e6194B",
            "contours": contour_data,
        }
    ]
    return {"detection_overlays": detection_overlays}


def _calculate_contours(prob_map: "np.ndarray", nside: int) -> list:
    """Calculate 50% and 90% credible-interval contours from a probability map."""
    import numpy as np
    import healpy as hp

    # Sort pixels by probability descending
    sort_idx = np.argsort(prob_map)[::-1]
    cumsum = np.cumsum(prob_map[sort_idx])

    contours = []
    for level in (0.5, 0.9):
        # Pixels inside this credible level
        inside = sort_idx[cumsum <= level]
        if len(inside) == 0:
            continue

        # Convert pixel centres to (ra, dec) pairs and group into rough polygons
        # Use healpy boundaries for each pixel (expensive for many pixels — downsample if needed)
        target_nside = min(nside, 64)  # Limit resolution for speed
        if nside > target_nside:
            # Downgrade map
            downgraded = hp.ud_grade(prob_map, target_nside)
            sort_idx_d = np.argsort(downgraded)[::-1]
            cumsum_d = np.cumsum(downgraded[sort_idx_d])
            inside = sort_idx_d[cumsum_d <= level]
            work_nside = target_nside
        else:
            work_nside = nside

        # Get pixel boundaries and build polygon list
        polygon_points = []
        step = max(1, len(inside) // 500)  # Sample at most 500 pixels per level
        for pix in inside[::step]:
            corners = hp.boundaries(work_nside, int(pix), step=1)  # shape (3, 4)
            # Convert unit-sphere Cartesian to RA/Dec
            theta, phi = hp.vec2ang(corners.T)
            ra = np.degrees(phi)
            dec = 90.0 - np.degrees(theta)
            polygon_points.append([[float(r), float(d)] for r, d in zip(ra, dec)])

        if polygon_points:
            contours.append({"polygon": polygon_points[0], "time": 0})

    return contours
