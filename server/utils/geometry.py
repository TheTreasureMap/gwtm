"""Coordinate transforms, footprint projection, and pointing crossmatch utilities."""

import re
import math
import ephem
import geoalchemy2
import numpy as np
from typing import List, Dict, Any, Tuple, Optional

from .type_checks import float_or_none


def sanatize_pointing(position: str) -> Tuple[float, float]:
    """
    Extract RA and Dec from a position string.

    Args:
        position: String representation of a point, e.g., "POINT(123.456 -45.678)"

    Returns:
        Tuple of (ra, dec) as floats
    """
    try:
        coords = position.split("POINT(")[1].split(")")[0].split(" ")
        ra = float(coords[0])
        dec = float(coords[1])
        # PostGIS returns longitude in -180..+180; normalize to 0..360 for astronomy
        if ra < 0:
            ra += 360.0
        return ra, dec
    except (IndexError, ValueError):
        return 0.0, 0.0


def sanatize_footprint_ccds(
    footprint_ccds: List[str],
) -> List[List[Tuple[float, float]]]:
    """
    Convert footprint strings to coordinate lists.

    Args:
        footprint_ccds: List of footprint strings (WKT format)

    Returns:
        List of coordinate lists, where each coordinate is an (ra, dec) tuple
    """
    result = []
    for footprint in footprint_ccds:
        try:
            # Extract coordinates from POLYGON string
            coords_str = re.search(r"POLYGON\(\((.*)\)\)", footprint).group(1)
            coords_pairs = coords_str.split(",")
            coords = []
            for pair in coords_pairs:
                x, y = map(float, pair.strip().split(" "))
                coords.append((x, y))
            result.append(coords)
        except (AttributeError, ValueError):
            continue
    return result


def ra_dec_to_uvec(ra, dec):
    """Convert RA/Dec to unit vector on celestial sphere."""
    phi = np.deg2rad(90 - dec)
    theta = np.deg2rad(ra)
    x = np.cos(theta) * np.sin(phi)
    y = np.sin(theta) * np.sin(phi)
    z = np.cos(phi)
    return x, y, z


def uvec_to_ra_dec(x, y, z):
    """Convert unit vector to RA/Dec."""
    r = np.sqrt(x**2 + y**2 + z**2)
    x /= r
    y /= r
    z /= r
    theta = np.arctan2(y, x)
    phi = np.arccos(z)
    dec = 90 - np.rad2deg(phi)
    if theta < 0:
        ra = 360 + np.rad2deg(theta)
    else:
        ra = np.rad2deg(theta)
    return ra, dec


def x_rot(theta_deg):
    """Rotation matrix around x-axis."""
    theta = np.deg2rad(theta_deg)
    return np.matrix(
        [
            [1, 0, 0],
            [0, np.cos(theta), -np.sin(theta)],
            [0, np.sin(theta), np.cos(theta)],
        ]
    )


def y_rot(theta_deg):
    """Rotation matrix around y-axis."""
    theta = np.deg2rad(theta_deg)
    return np.matrix(
        [
            [np.cos(theta), 0, np.sin(theta)],
            [0, 1, 0],
            [-np.sin(theta), 0, np.cos(theta)],
        ]
    )


def z_rot(theta_deg):
    """Rotation matrix around z-axis."""
    theta = np.deg2rad(theta_deg)
    return np.matrix(
        [
            [np.cos(theta), -np.sin(theta), 0],
            [np.sin(theta), np.cos(theta), 0],
            [0, 0, 1],
        ]
    )


def project_footprint(
    footprint: List[Tuple[float, float]],
    ra: float,
    dec: float,
    pos_angle: Optional[float] = None,
) -> List[Tuple[float, float]]:
    """
    Project a footprint to a new position with optional rotation using spherical geometry.

    Args:
        footprint: List of (ra, dec) tuples defining the footprint
        ra: Right ascension of the center
        dec: Declination of the center
        pos_angle: Position angle for rotation (degrees)

    Returns:
        Projected footprint as a list of (ra, dec) tuples
    """
    if pos_angle is None:
        pos_angle = 0.0

    # Convert footprint coordinates to unit vectors
    footprint_zero_center_ra = np.asarray([pt[0] for pt in footprint])
    footprint_zero_center_dec = np.asarray([pt[1] for pt in footprint])
    footprint_zero_center_uvec = ra_dec_to_uvec(
        footprint_zero_center_ra, footprint_zero_center_dec
    )
    footprint_zero_center_x, footprint_zero_center_y, footprint_zero_center_z = (
        footprint_zero_center_uvec
    )

    proj_footprint = []
    for idx in range(footprint_zero_center_x.shape[0]):
        vec = np.asarray(
            [
                footprint_zero_center_x[idx],
                footprint_zero_center_y[idx],
                footprint_zero_center_z[idx],
            ]
        )
        # Apply spherical rotations: position angle, declination, then RA
        new_vec = vec @ x_rot(-pos_angle) @ y_rot(dec) @ z_rot(-ra)
        new_x, new_y, new_z = new_vec.flat
        pt_ra, pt_dec = uvec_to_ra_dec(new_x, new_y, new_z)
        proj_footprint.append((pt_ra, pt_dec))

    return proj_footprint


def polygons2footprints(
    polygons: List[List[List[float]]], time: float = 0
) -> List[Dict[str, Any]]:
    """
    Convert list of polygon coordinates to footprint objects with time.

    Args:
        polygons: List of polygon coordinate lists
        time: Time value to associate with the footprints

    Returns:
        List of footprint objects with 'polygon' and 'time' keys
    """
    footprints = []
    for poly in polygons:
        # Convert from [lon, lat] to [ra, dec]
        footprint = [(coord[0], coord[1]) for coord in poly]
        footprints.append({"polygon": footprint, "time": time})
    return footprints


def pointing_crossmatch(pointing, otherpointings, dist_thresh=None):
    """Check if a pointing matches any existing pointings."""
    if dist_thresh is None:

        filtered_pointings = [
            x
            for x in otherpointings
            if (
                x.status == pointing.status
                and x.instrumentid == int(pointing.instrumentid)
                and x.band == pointing.band
                and x.time == pointing.time
                and x.pos_angle == float_or_none(pointing.pos_angle)
            )
        ]

        for p in filtered_pointings:
            p_pos = str(geoalchemy2.shape.to_shape(p.position))
            if sanatize_pointing(p_pos) == sanatize_pointing(pointing.position):
                return True

    else:

        p_ra, p_dec = sanatize_pointing(pointing.position)

        filtered_pointings = [
            x
            for x in otherpointings
            if (
                x.status == pointing.status
                and x.instrumentid == int(pointing.instrumentid)
                and x.band == pointing.band
            )
        ]

        for p in filtered_pointings:
            ra, dec = sanatize_pointing(str(geoalchemy2.shape.to_shape(p.position)))
            sep = 206264.806 * (float(ephem.separation((ra, dec), (p_ra, p_dec))))
            if sep < dist_thresh:
                return True

    return False
