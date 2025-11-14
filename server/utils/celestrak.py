"""
CelesTrak satellite tracking functionality for Fermi spacecraft positioning.

This module provides functions to:
1. Download TLE (Two-Line Element) data from CelesTrak
2. Calculate Fermi spacecraft position at specific times
3. Determine Earth limb for sky coverage calculations
4. Support Fermi/GBM instrument coverage analysis
"""

import math
import numpy as np
from datetime import datetime
from typing import Tuple, Union, Optional
from urllib.request import urlopen
from bs4 import BeautifulSoup
from shapely.geometry import Point, Polygon

try:
    import ephem
except ImportError:
    ephem = None


def get_data_from_tle(
    datetime_obj: datetime, 
    tle_lat_offset: float = 0, 
    tle_lon_offset: float = 0.21
) -> Tuple[Union[float, bool], Union[float, bool], Union[float, bool]]:
    """
    Get Fermi spacecraft position from CelesTrak TLE data.
    
    Args:
        datetime_obj: DateTime object for when to calculate position
        tle_lat_offset: Latitude correction offset (default: 0)
        tle_lon_offset: Longitude correction offset (default: 0.21)
        
    Returns:
        Tuple of (longitude, latitude, elevation) or (False, False, False) on error
        
    Raises:
        ImportError: If ephem library is not available
        Exception: If TLE data cannot be retrieved or parsed
    """
    if ephem is None:
        raise ImportError("ephem library is required for TLE calculations")
    
    # Download TLE data for Fermi spacecraft (CATNR=33053) using new CelesTrak API
    url = "https://celestrak.org/NORAD/elements/gp.php?CATNR=33053&FORMAT=tle"
    
    try:
        data = urlopen(url)
        tle_raw = data.read().decode('utf-8')
        
        # The new API returns TLE data directly, split into lines
        tle_lines = [line.strip() for line in tle_raw.split('\n') if line.strip()]
        
        if len(tle_lines) < 3:
            print(f"Warning: Only got {len(tle_lines)} TLE lines: {tle_lines}")
            return False, False, False
            
        # TLE format: Line 0 = name, Line 1 = first data line, Line 2 = second data line
        tle_obj = tle_lines
            
        # Create spacecraft instance from TLE data
        fermi = ephem.readtle(tle_obj[0], tle_obj[1], tle_obj[2])
        
        # Create observer at Earth center
        observer_fermi = ephem.Observer()
        observer_fermi.lat = '0'
        observer_fermi.long = '0'
        observer_fermi.date = ephem.date(datetime_obj)
        
        # Compute spacecraft position
        fermi.compute(observer_fermi)
        
        # Extract position data
        lat = np.degrees(fermi.sublat.znorm)
        lon = np.degrees(fermi.sublong.norm)
        elevation = fermi.elevation
        
        # Apply offset corrections
        lon = lon - tle_lon_offset
        lat = lat - tle_lat_offset
        
        # Check if spacecraft is in South Atlantic Anomaly (SAA)
        # If in SAA, Fermi/GBM is not operational
        saa_lon_vertices = [
            33.900, 12.398, -9.103, -30.605, -38.400, -45.000, -65.000, 
            -84.000, -89.200, -94.300, -94.300, -86.100, 33.900
        ]
        saa_lat_vertices = [
            -30.000, -19.867, -9.733, 0.400, 2.000, 2.000, -1.000, 
            -6.155, -8.880, -14.220, -18.404, -30.000, -30.000
        ]
        saa_poly = Polygon(list(zip(saa_lon_vertices, saa_lat_vertices)))
        
        # Convert longitude to SAA coordinate system
        sat_pos = Point(-(360 - lon), lat)
        in_saa = saa_poly.contains(sat_pos)
        
        if in_saa:
            return False, False, False
            
        return lon, lat, elevation
        
    except Exception as e:
        print(f"Error retrieving TLE data: {str(e)}")
        return False, False, False


def deg2dm(deg: float) -> Tuple[int, float]:
    """
    Convert decimal degrees to degrees and decimal minutes.
    
    Args:
        deg: Decimal degrees
        
    Returns:
        Tuple of (degrees, minutes)
    """
    sign = np.sign(deg)
    deg = np.abs(deg)
    d = np.floor(deg)
    m = (deg - d) * 60
    return int(sign * d), m


def get_geo_center(datetime_obj: datetime, lon: float, lat: float) -> Tuple[float, float]:
    """
    Get the geocenter coordinates (RA/Dec) from spacecraft position.
    
    This calculates the point on the celestial sphere that is directly
    opposite to the spacecraft's zenith direction.
    
    Args:
        datetime_obj: DateTime object for calculation
        lon: Spacecraft longitude in degrees
        lat: Spacecraft latitude in degrees
        
    Returns:
        Tuple of (ra_geocenter, dec_geocenter) in degrees
        
    Raises:
        ImportError: If ephem library is not available
    """
    if ephem is None:
        raise ImportError("ephem library is required for geocenter calculations")
    
    # Create observer at spacecraft location
    observer = ephem.Observer()
    
    # Convert longitude to +E (-180 to 180)
    if lon > 180:
        lon = (lon % 180) - 180
        
    lon_deg, lon_min = deg2dm(lon)
    lat_deg, lat_min = deg2dm(lat)
    
    lon_string = f'{lon_deg}:{lon_min}'
    lat_string = f'{lat_deg}:{lat_min}'
    
    observer.lon = lon_string
    observer.lat = lat_string
    observer.date = ephem.date(datetime_obj)
    
    # Get RA/Dec of zenith (altitude = 90 degrees)
    ra_zenith_radians, dec_zenith_radians = observer.radec_of('0', '90')
    
    # Convert to degrees
    ra_zenith = np.degrees(ra_zenith_radians)
    dec_zenith = np.degrees(dec_zenith_radians)
    
    # Calculate geocenter (opposite point)
    ra_geocenter = (ra_zenith + 180) % 360
    dec_geocenter = -1 * dec_zenith
    
    return ra_geocenter, dec_geocenter


def get_earth_sat_pos(datetime_obj: datetime) -> Tuple[Union[float, bool], Union[float, bool], Union[float, bool]]:
    """
    Get Earth's position as seen from Fermi spacecraft.
    
    This function calculates where Earth appears in the sky from Fermi's perspective,
    which is used to determine what sky regions are blocked by Earth's limb.
    
    Args:
        datetime_obj: DateTime object for calculation
        
    Returns:
        Tuple of (ra_geocenter, dec_geocenter, earth_radius_degrees) or (False, False, False)
    """
    tle_lon_offset = 0.21
    tle_lat_offset = 0
    
    try:
        lon, lat, elevation = get_data_from_tle(
            datetime_obj, 
            tle_lat_offset=tle_lat_offset, 
            tle_lon_offset=tle_lon_offset
        )
    except Exception:
        return False, False, False
        
    if not all([lon, lat, elevation]):
        return False, False, False
        
    # Get geocenter coordinates
    ra_geocenter, dec_geocenter = get_geo_center(datetime_obj, lon, lat)
    
    # Calculate Earth's angular size as seen from spacecraft
    EARTH_RADIUS = 6378.140 * 1000  # Earth radius in meters
    dtor = math.pi / 180
    elev = elevation + EARTH_RADIUS  # Total distance from Earth center
    earth_size_rad = np.arcsin(EARTH_RADIUS / elev) / dtor  # Angular radius in degrees
    
    return ra_geocenter, dec_geocenter, earth_size_rad


def make_earth_contour(ra: float, dec: float, radius: float) -> list:
    """
    Create Earth limb contour for sky coverage calculations.
    
    This generates a circular contour representing Earth's limb as seen from Fermi,
    which defines the boundary of sky regions blocked by Earth.
    
    Args:
        ra: Right ascension of Earth center in degrees
        dec: Declination of Earth center in degrees  
        radius: Angular radius of Earth in degrees
        
    Returns:
        List of (ra, dec) coordinate pairs forming Earth's limb contour
    """
    from server.utils.function import project_footprint
    
    # Generate circle points
    thetas = np.linspace(0, -2 * np.pi, 200)
    ras = radius * np.cos(thetas)
    decs = radius * np.sin(thetas)
    contour = np.c_[ras, decs]
    
    # Project onto sky coordinates
    earth_contour = project_footprint(contour, ra, dec, 0)
    
    return earth_contour


def calculate_fermi_gbm_coverage(datetime_obj: datetime) -> Optional[dict]:
    """
    Calculate Fermi/GBM sky coverage for a given time.
    
    This is the main function for determining what sky regions are visible
    to the Fermi Gamma-Ray Burst Monitor at a specific time.
    
    Args:
        datetime_obj: DateTime for coverage calculation
        
    Returns:
        Dictionary with coverage information or None if calculation fails:
        {
            'earth_ra': Earth center RA,
            'earth_dec': Earth center Dec,
            'earth_radius': Earth angular radius,
            'earth_contour': List of limb coordinates,
            'spacecraft_lon': Fermi longitude,
            'spacecraft_lat': Fermi latitude,
            'spacecraft_elevation': Fermi elevation
        }
    """
    # Get spacecraft position
    lon, lat, elevation = get_data_from_tle(datetime_obj)
    
    if not all([lon, lat, elevation]):
        return None
        
    # Get Earth position as seen from spacecraft
    ra_geocenter, dec_geocenter, earth_radius = get_earth_sat_pos(datetime_obj)
    
    if not all([ra_geocenter, dec_geocenter, earth_radius]):
        return None
        
    # Generate Earth limb contour
    earth_contour = make_earth_contour(ra_geocenter, dec_geocenter, earth_radius)
    
    return {
        'earth_ra': ra_geocenter,
        'earth_dec': dec_geocenter, 
        'earth_radius': earth_radius,
        'earth_contour': earth_contour,
        'spacecraft_lon': lon,
        'spacecraft_lat': lat,
        'spacecraft_elevation': elevation
    }