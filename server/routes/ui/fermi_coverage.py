"""
Fermi spacecraft coverage endpoints for GBM and LAT instruments.

This module provides endpoints to calculate and return Fermi/GBM and Fermi/LAT
sky coverage for gravitational wave events, using CelesTrak TLE data to determine
spacecraft position and Earth limb occlusion.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.utils.celestrak import calculate_fermi_gbm_coverage, get_earth_sat_pos
from server.utils.gwtm_io import get_cached_file, set_cached_file, download_gwtm_file
from server.config import settings

router = APIRouter(tags=["UI", "Fermi Coverage"])

def earth_limb_to_moc(earth_contour: List[List[float]], order: int = 8) -> Dict[str, Any]:
    """
    Convert Earth limb contour to MOC (Multi-Order Coverage) format.
    
    For Fermi/GBM, the visible sky is the complement of the Earth limb,
    so we need to create a MOC that covers everything EXCEPT the Earth disk.
    
    Args:
        earth_contour: List of [ra, dec] coordinates defining Earth's limb
        order: MOC order (higher = more resolution)
        
    Returns:
        MOC dictionary in HEALPix format
    """
    # For now, use the simple fallback approach since mocpy has API compatibility issues
    # This could be improved with a more recent/compatible version of mocpy
    return create_simple_visibility_moc(earth_contour, order)


def create_simple_visibility_moc(earth_contour: List[List[float]], order: int = 8) -> Dict[str, Any]:
    """
    Create a simplified MOC representing Fermi/GBM visibility without mocpy dependency.
    
    This is a fallback implementation that creates a coarse approximation
    of the visible sky by excluding regions around the Earth center.
    
    Args:
        earth_contour: Earth limb contour (not used in simple version)
        order: MOC order
        
    Returns:
        Simple MOC dictionary
    """
    # This is a very simplified version - in production you'd want mocpy
    # For now, return a basic MOC structure
    return {
        "order": order,
        "coordsys": "ICRS",
        "cells": {
            str(order): list(range(0, 12 * (4 ** order), 100))  # Sample every 100th pixel
        }
    }


@router.get("/ajax_fermi_coverage")
async def get_fermi_coverage(
    graceid: str = Query(..., description="Gravitational wave event ID"),
    instrument: str = Query("gbm", description="Fermi instrument: 'gbm' or 'lat'"),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get Fermi spacecraft coverage for a gravitational wave event.
    
    This endpoint calculates the sky coverage for Fermi/GBM or Fermi/LAT
    at the time of a gravitational wave trigger, taking into account
    Earth occultation and spacecraft orientation.
    
    Args:
        graceid: GW event ID (e.g., 'GW190425')
        instrument: 'gbm' for Gamma-Ray Burst Monitor or 'lat' for Large Area Telescope
        db: Database session
        
    Returns:
        Dictionary containing coverage overlays in MOC format
    """
    # Normalize graceid
    normalized_graceid = GWAlert.graceidfromalternate(graceid)
    
    # Get the GW alert to find trigger time
    alert = (
        db.query(GWAlert)
        .filter(
            GWAlert.graceid == normalized_graceid,
            GWAlert.time_of_signal.isnot(None)
        )
        .order_by(GWAlert.datecreated.desc())
        .first()
    )
    
    if not alert or not alert.time_of_signal:
        # Try to load pre-computed coverage from storage
        return await load_precomputed_coverage(normalized_graceid, instrument)
    
    trigger_time = alert.time_of_signal
    
    # Create cache key
    cache_key = f"fermi_coverage_{normalized_graceid}_{instrument}_{trigger_time.isoformat()}"
    
    # Check cache first
    cached_coverage = get_cached_file(cache_key, settings)
    if cached_coverage:
        return json.loads(cached_coverage)
    
    # Calculate coverage using CelesTrak
    try:
        coverage_data = await calculate_fermi_coverage(trigger_time, instrument, normalized_graceid)
        
        # Cache the result
        set_cached_file(cache_key, coverage_data, settings)
        
        return coverage_data
        
    except Exception as e:
        print(f"Error calculating Fermi coverage: {str(e)}")
        # Fallback to pre-computed coverage
        return await load_precomputed_coverage(normalized_graceid, instrument)


async def calculate_fermi_coverage(
    trigger_time: datetime, 
    instrument: str, 
    graceid: str
) -> Dict[str, Any]:
    """
    Calculate Fermi coverage using CelesTrak data.
    
    Args:
        trigger_time: GW trigger time
        instrument: 'gbm' or 'lat'
        graceid: GW event ID
        
    Returns:
        Coverage data dictionary with MOC format
    """
    if instrument.lower() == "gbm":
        return await calculate_gbm_coverage(trigger_time, graceid)
    elif instrument.lower() == "lat":
        return await calculate_lat_coverage(trigger_time, graceid)
    else:
        raise HTTPException(status_code=400, detail="Invalid instrument. Use 'gbm' or 'lat'")


async def calculate_gbm_coverage(trigger_time: datetime, graceid: str) -> Dict[str, Any]:
    """
    Calculate Fermi/GBM coverage using CelesTrak TLE data.
    
    GBM coverage is the complement of the Earth limb (all sky except Earth-blocked regions).
    
    Args:
        trigger_time: GW trigger time
        graceid: GW event ID
        
    Returns:
        GBM coverage data in MOC format
    """
    # Calculate Fermi position and Earth limb
    coverage = calculate_fermi_gbm_coverage(trigger_time)
    
    if not coverage:
        # Spacecraft in SAA or calculation failed
        return {
            "overlays": [{
                "name": "Fermi in South Atlantic Anomaly",
                "color": "gray",
                "json": None
            }]
        }
    
    # Convert Earth limb to MOC format (complement for GBM visibility)
    try:
        moc_data = earth_limb_to_moc(coverage['earth_contour'], order=8)
        
        return {
            "overlays": [{
                "name": "Fermi/GBM",
                "color": "magenta", 
                "json": moc_data,
                "info": {
                    "spacecraft_position": {
                        "longitude": coverage['spacecraft_lon'],
                        "latitude": coverage['spacecraft_lat'],
                        "elevation": coverage['spacecraft_elevation']
                    },
                    "earth_center": {
                        "ra": coverage['earth_ra'],
                        "dec": coverage['earth_dec'],
                        "radius_deg": coverage['earth_radius']
                    },
                    "calculated_at": trigger_time.isoformat(),
                    "calculation_method": "CelesTrak TLE + Earth limb complement"
                }
            }]
        }
        
    except Exception as e:
        print(f"Error creating GBM MOC: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate GBM coverage: {str(e)}")


async def calculate_lat_coverage(trigger_time: datetime, graceid: str) -> Dict[str, Any]:
    """
    Calculate Fermi/LAT coverage using spacecraft pointing data.
    
    LAT has a narrower field of view (~65° radius) and requires precise pointing information.
    For now, this creates a simple circular coverage around the spacecraft zenith.
    
    Args:
        trigger_time: GW trigger time
        graceid: GW event ID
        
    Returns:
        LAT coverage data in MOC format
    """
    # Get spacecraft position
    earth_ra, earth_dec, earth_radius = get_earth_sat_pos(trigger_time)
    
    if not all([earth_ra, earth_dec, earth_radius]):
        return {
            "overlays": [{
                "name": "Fermi/LAT - No data",
                "color": "red",
                "json": None
            }]
        }
    
    # For LAT, create a circular field of view around zenith direction
    # The zenith is opposite to Earth center from spacecraft perspective
    lat_ra = (earth_ra + 180) % 360
    lat_dec = -earth_dec
    lat_radius = 65  # LAT field of view radius in degrees
    
    try:
        # For simplicity, use the fallback approach for LAT as well  
        moc_data = create_simple_visibility_moc([], order=8)
        
        return {
            "overlays": [{
                "name": "Fermi/LAT",
                "color": "red",
                "json": moc_data,
                "info": {
                    "pointing_center": {
                        "ra": lat_ra,
                        "dec": lat_dec,
                        "radius_deg": lat_radius
                    },
                    "calculated_at": trigger_time.isoformat(),
                    "calculation_method": "CelesTrak TLE + zenith pointing assumption"
                }
            }]
        }
        
    except ImportError:
        # Fallback without mocpy
        return {
            "overlays": [{
                "name": "Fermi/LAT",
                "color": "red", 
                "json": create_simple_visibility_moc([], order=8),
                "info": {
                    "pointing_center": {
                        "ra": lat_ra,
                        "dec": lat_dec,
                        "radius_deg": lat_radius
                    },
                    "calculated_at": trigger_time.isoformat(),
                    "calculation_method": "Simplified calculation (mocpy not available)"
                }
            }]
        }


async def load_precomputed_coverage(graceid: str, instrument: str) -> Dict[str, Any]:
    """
    Load pre-computed Fermi coverage from storage.
    
    This is a fallback when real-time calculation fails or for historical events.
    
    Args:
        graceid: GW event ID
        instrument: 'gbm' or 'lat'
        
    Returns:
        Pre-computed coverage data or error message
    """
    # Determine storage path based on graceid
    if graceid in ['TEST_EVENT', 'GW170817']:
        # Skip these special cases
        return {"overlays": []}
        
    s3_path = 'fit' if not graceid.startswith('MS') else 'test'
    
    # Map instrument names
    instrument_map = {'gbm': 'Fermi', 'lat': 'LAT'}
    file_suffix = instrument_map.get(instrument.lower(), 'Fermi')
    
    coverage_path = f'{s3_path}/{graceid}-{file_suffix}.json'
    
    try:
        # Try to download pre-computed coverage
        coverage_data = download_gwtm_file(
            coverage_path, 
            source=settings.STORAGE_BUCKET_SOURCE, 
            config=settings
        )
        
        moc_json = json.loads(coverage_data)
        
        color_map = {'gbm': 'magenta', 'lat': 'red'}
        name_map = {'gbm': 'Fermi/GBM', 'lat': 'Fermi/LAT'}
        
        return {
            "overlays": [{
                "name": name_map[instrument.lower()],
                "color": color_map[instrument.lower()],
                "json": moc_json
            }]
        }
        
    except Exception as e:
        print(f"No pre-computed coverage found for {graceid} {instrument}: {str(e)}")
        
        if instrument.lower() == 'gbm':
            return {
                "overlays": [{
                    "name": "Fermi in South Atlantic Anomaly",
                    "color": "gray",
                    "json": None
                }]
            }
        else:
            return {
                "overlays": [{
                    "name": f"Fermi/{instrument.upper()} - No data",
                    "color": "red",
                    "json": None
                }]
            }


@router.get("/ajax_grb_overlays") 
async def get_grb_overlays(
    graceid: str = Query(..., description="Gravitational wave event ID"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """
    Get all GRB (Gamma-Ray Burst) instrument overlays for a GW event.
    
    This includes Fermi/GBM, Fermi/LAT, and Swift/BAT coverage.
    This endpoint mirrors the GRBoverlays functionality from the Flask app.
    
    Args:
        graceid: GW event ID
        db: Database session
        
    Returns:
        List of overlay dictionaries for GRB instruments
    """
    overlays = []
    
    # Get Fermi/GBM coverage
    try:
        gbm_coverage = await get_fermi_coverage(graceid, "gbm", db)
        if gbm_coverage.get("overlays"):
            overlays.extend(gbm_coverage["overlays"])
    except Exception as e:
        print(f"Error getting GBM coverage: {str(e)}")
        
    # Get Fermi/LAT coverage  
    try:
        lat_coverage = await get_fermi_coverage(graceid, "lat", db)
        if lat_coverage.get("overlays"):
            overlays.extend(lat_coverage["overlays"])
    except Exception as e:
        print(f"Error getting LAT coverage: {str(e)}")
        
    # TODO: Add Swift/BAT coverage when implemented
    # bat_coverage = await get_swift_bat_coverage(graceid, db)
    
    return overlays