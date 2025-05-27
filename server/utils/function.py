import io
import json

import re

import ephem
import geoalchemy2
import numpy as np
import math
from typing import List, Dict, Any, Tuple, Optional

import requests

from server import config
from server.core.enums import pointing_status
from server.db.models.pointing import Pointing
from server.schemas.pointing import PointingSchema

def isInt(s) -> bool:
    """Check if a value can be converted to an integer."""
    try:
        int(s)
        return True
    except (ValueError, TypeError):
        return False


def isFloat(s) -> bool:
    """Check if a value can be converted to a float."""
    try:
        float(s)
        return True
    except (ValueError, TypeError):
        return False


def get_farrate_farunit(far: float) -> Tuple[float, str]:
    """
    Convert FAR (False Alarm Rate) to human readable format.
    
    Args:
        far: False Alarm Rate in Hz
    
    Returns:
        Tuple of (rate, unit) where unit is a time unit (years, days, hours, etc.)
    """
    far_rate_dict = {
        'second': 1 / far,
        'minute': 1 / far / 60,
        'hour': 1 / far / 3600,
        'day': 1 / far / 3600 / 24,
        'month': 1 / far / 3600 / 24 / 30,
        'year': 1 / far / 3600 / 24 / 365,
        'decade': 1 / far / 3600 / 24 / 365 / 10,
        'century': 1 / far / 3600 / 24 / 365 / 100,
        'millennium': 1 / far / 3600 / 24 / 365 / 1000,
    }

    if far_rate_dict['second'] < 60:
        return far_rate_dict['second'], 'seconds'
    if far_rate_dict['minute'] < 60:
        return far_rate_dict['minute'], 'minutes'
    if far_rate_dict['hour'] < 24:
        return far_rate_dict['hour'], 'hours'
    if far_rate_dict['day'] < 30:
        return far_rate_dict['day'], 'days'
    if far_rate_dict['month'] < 12:
        return far_rate_dict['month'], 'months'
    if far_rate_dict['year'] < 10:
        return far_rate_dict['year'], 'years'
    if far_rate_dict['decade'] < 10:
        return far_rate_dict['decade'], 'decades'
    if far_rate_dict['century'] < 10:
        return far_rate_dict['century'], 'centuries'

    return far_rate_dict['millennium'], 'millennia'


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
        return ra, dec
    except (IndexError, ValueError):
        return 0.0, 0.0


def sanatize_footprint_ccds(footprint_ccds: List[str]) -> List[List[Tuple[float, float]]]:
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


def project_footprint(
        footprint: List[Tuple[float, float]],
        ra: float,
        dec: float,
        pos_angle: Optional[float] = None
) -> List[Tuple[float, float]]:
    """
    Project a footprint to a new position with optional rotation.
    
    Args:
        footprint: List of (ra, dec) tuples defining the footprint
        ra: Right ascension of the center
        dec: Declination of the center
        pos_angle: Position angle for rotation (degrees)
    
    Returns:
        Projected footprint as a list of (ra, dec) tuples
    """
    # Calculate center of the footprint
    ra_vals = [p[0] for p in footprint]
    dec_vals = [p[1] for p in footprint]
    center_ra = np.mean(ra_vals)
    center_dec = np.mean(dec_vals)

    # Calculate offsets from center
    ra_offsets = [p[0] - center_ra for p in footprint]
    dec_offsets = [p[1] - center_dec for p in footprint]

    # Apply rotation if needed
    if pos_angle is not None and pos_angle != 0:
        angle_rad = math.radians(pos_angle)
        rotated_offsets = []
        for i in range(len(ra_offsets)):
            new_ra_offset = ra_offsets[i] * math.cos(angle_rad) - dec_offsets[i] * math.sin(angle_rad)
            new_dec_offset = ra_offsets[i] * math.sin(angle_rad) + dec_offsets[i] * math.cos(angle_rad)
            rotated_offsets.append((new_ra_offset, new_dec_offset))
        ra_offsets = [offset[0] for offset in rotated_offsets]
        dec_offsets = [offset[1] for offset in rotated_offsets]

    # Apply offsets to new center
    projected_footprint = []
    for i in range(len(footprint)):
        projected_ra = ra + ra_offsets[i] / math.cos(math.radians(dec))
        projected_dec = dec + dec_offsets[i]
        projected_footprint.append((projected_ra, projected_dec))

    # Make sure the polygon is closed
    if projected_footprint[0] != projected_footprint[-1]:
        projected_footprint.append(projected_footprint[0])

    return projected_footprint


def polygons2footprints(polygons: List[List[List[float]]], time: float = 0) -> List[Dict[str, Any]]:
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
        footprints.append({
            "polygon": footprint,
            "time": time
        })
    return footprints


def sanatize_gal_info(galaxy_entry, galaxy_list) -> Dict[str, Any]:
    """
    Format galaxy information for display.
    
    Args:
        galaxy_entry: A galaxy entry object
        galaxy_list: The parent galaxy list object
    
    Returns:
        Formatted galaxy information as a dictionary
    """
    info_dict = {}

    if hasattr(galaxy_entry, 'info') and galaxy_entry.info:
        try:
            info_dict = json.loads(galaxy_entry.info)
        except json.JSONDecodeError:
            info_dict = {}

    # Add galaxy list information
    info_dict["Group"] = galaxy_list.groupname if hasattr(galaxy_list, 'groupname') else ""
    info_dict["Score"] = galaxy_entry.score if hasattr(galaxy_entry, 'score') else ""
    info_dict["Rank"] = galaxy_entry.rank if hasattr(galaxy_entry, 'rank') else ""

    return info_dict


def sanatize_icecube_event(event, notice) -> Dict[str, Any]:
    """
    Format IceCube event information for display.
    
    Args:
        event: An IceCube event object
        notice: The parent IceCube notice object
    
    Returns:
        Formatted IceCube event information as a dictionary
    """
    info_dict = {
        "Event ID": event.id if hasattr(event, 'id') else "",
        "Notice ID": notice.id if hasattr(notice, 'id') else "",
        "RA": event.ra if hasattr(event, 'ra') else "",
        "Dec": event.dec if hasattr(event, 'dec') else "",
        "Uncertainty": event.ra_uncertainty if hasattr(event, 'ra_uncertainty') else "",
        "Event p-value (generic)": event.event_pval_generic if hasattr(event, 'event_pval_generic') else "",
        "Event p-value (Bayesian)": event.event_pval_bayesian if hasattr(event, 'event_pval_bayesian') else "",
        "Event DT": event.event_dt if hasattr(event, 'event_dt') else "",
    }

    return info_dict


def sanatize_candidate_info(candidate, ra, dec) -> Dict[str, Any]:
    """
    Format candidate information for display.
    
    Args:
        candidate: A candidate object
        ra: Right ascension
        dec: Declination
    
    Returns:
        Formatted candidate information as a dictionary
    """
    info_dict = {
        "Candidate Name": candidate.candidate_name if hasattr(candidate, 'candidate_name') else "",
        "TNS Name": candidate.tns_name if hasattr(candidate, 'tns_name') else "",
        "TNS URL": candidate.tns_url if hasattr(candidate, 'tns_url') else "",
        "RA": ra,
        "Dec": dec,
        "Discovery Date": candidate.discovery_date.isoformat() if hasattr(candidate,
                                                                          'discovery_date') and candidate.discovery_date else "",
        "Discovery Magnitude": candidate.discovery_magnitude if hasattr(candidate, 'discovery_magnitude') else "",
        "Associated Galaxy": candidate.associated_galaxy if hasattr(candidate, 'associated_galaxy') else "",
        "Associated Galaxy Redshift": candidate.associated_galaxy_redshift if hasattr(candidate,
                                                                                      'associated_galaxy_redshift') else "",
        "Associated Galaxy Distance": candidate.associated_galaxy_distance if hasattr(candidate,
                                                                                      'associated_galaxy_distance') else "",
    }

    return info_dict


def sanatize_XRT_source_info(source) -> Dict[str, Any]:
    """
    Format XRT source information for display.
    
    Args:
        source: An XRT source object
    
    Returns:
        Formatted XRT source information as a dictionary
    """
    info_dict = {
        "Alert Identifier": source.get('alert_identifier', ''),
        "RA": source.get('right_ascension', ''),
        "Dec": source.get('declination', ''),
        "Significance": source.get('significance', ''),
        "URL": source.get('url', ''),
    }

    return info_dict


def by_chunk(items: List[Any], n: int) -> List[List[Any]]:
    """
    Split a list into chunks of size n.
    
    Args:
        items: The list to split
        n: The size of each chunk
    
    Returns:
        List of chunks
    """
    chunks = []
    for i in range(0, len(items), n):
        chunks.append(items[i:i + n])
    return chunks


def floatNone(i):
    if i is not None:
        try:
            return float(i)
        except:  # noqa: E722
            return 0.0
    else:
        return None


def pointing_crossmatch(pointing, otherpointings, dist_thresh=None):
    if dist_thresh is None:

        filtered_pointings = [x for x in otherpointings if (
                x.status.name == pointing.status and \
                x.instrumentid == int(pointing.instrumentid) and \
                x.band.name == pointing.band and \
                x.time == pointing.time and \
                x.pos_angle == floatNone(pointing.pos_angle)
        )]

        for p in filtered_pointings:
            p_pos = str(geoalchemy2.shape.to_shape(p.position))
            if sanatize_pointing(p_pos) == sanatize_pointing(pointing.position):
                return True

    else:

        p_ra, p_dec = sanatize_pointing(pointing.position)

        filtered_pointings = [x for x in otherpointings if (
                x.status.name == pointing.status and \
                x.instrumentid == int(pointing.instrumentid) and \
                x.band.name == pointing.band
        )]

        for p in filtered_pointings:
            ra, dec = sanatize_pointing(str(geoalchemy2.shape.to_shape(p.position)))
            sep = 206264.806 * (float(ephem.separation((ra, dec), (p_ra, p_dec))))
            if sep < dist_thresh:
                return True

    return False


def create_doi(payload):
    ACCESS_TOKEN = config.settings.ZENODO_ACCESS_KEY
    data = payload['data']
    data_file = payload['data_file']
    files = payload['files']
    headers = payload['headers']

    r = requests.post('https://zenodo.org/api/deposit/depositions', params={'access_token': ACCESS_TOKEN}, json={},
                      headers=headers)

    if r.status_code == 403:
        return None, None

    d_id = r.json()['id']
    r = requests.post('https://zenodo.org/api/deposit/depositions/%s/files' % d_id,
                      params={'access_token': ACCESS_TOKEN}, data=data_file, files=files)
    r = requests.put('https://zenodo.org/api/deposit/depositions/%s' % d_id, data=json.dumps(data),
                     params={'access_token': ACCESS_TOKEN}, headers=headers)
    r = requests.post('https://zenodo.org/api/deposit/depositions/%s/actions/publish' % d_id,
                      params={'access_token': ACCESS_TOKEN})

    return_json = r.json()
    try:
        doi_url = return_json['doi_url']
    except:  # noqa: E722
        doi_url = None
    return int(d_id), doi_url


def create_pointing_doi(
        points: List[Pointing],
        graceid: str,
        creators: List[Dict[str, str]],
        instrument_names: List[str]
) -> Tuple[int, Optional[str]]:
    """
    Create a DOI for pointings.
    
    Args:
        points: List of pointing objects
        graceid: Grace ID of the event
        creators: List of creator dictionaries
        instrument_names: List of instrument names
    
    Returns:
        Tuple of (doi_id, doi_url)
    """

    points_json = []

    for p in points:
        if p.status == pointing_status.completed:
            points_json.append(PointingSchema.from_orm(p))

    if len(instrument_names) > 1:
        inst_str = "These observations were taken on the"
        for i in instrument_names:
            if i == instrument_names[len(instrument_names) - 1]:
                inst_str += " and " + i
            else:
                inst_str += " " + i + ","

        inst_str += " instruments."
    else:
        inst_str = "These observations were taken on the " + instrument_names[0] + " instrument."

    if len(points_json):
        payload = {
            'data': {
                "metadata": {
                    "title": "Submitted Completed pointings to the Gravitational Wave Treasure Map for event " + graceid,
                    "upload_type": "dataset",
                    "creators": creators,
                    "description": "Attached in a .json file is the completed pointing information for " + str(
                        len(points_json)) + " observation(s) for the EM counterpart search associated with the gravitational wave event " + graceid + ". " + inst_str
                }
            },
            'data_file': {'name': 'completed_pointings_' + graceid + '.json'},
            'files': {'file': json.dumps([p.model_dump(mode="json") for p in points_json])},
            'headers': {"Content-Type": "application/json"},
        }

        d_id, url = create_doi(payload)
        return d_id, url

    return None, None


def create_galaxy_score_doi(
        galaxies: List[Any],
        creators: List[Dict[str, str]],
        reference: Optional[str],
        graceid: str,
        alert_type: str
) -> Tuple[int, Optional[str]]:
    """
    Create a DOI for galaxy scores.
    
    Args:
        galaxies: List of galaxy objects
        creators: List of creator dictionaries
        reference: Reference information
        graceid: Grace ID of the event
        alert_type: Type of the alert
    
    Returns:
        Tuple of (doi_id, doi_url)
    """
    import uuid
    from datetime import datetime

    # Create a unique identifier
    doi_suffix = str(uuid.uuid4())[:8]
    doi_prefix = "10.5072"  # Test DOI prefix
    doi = f"{doi_prefix}/gwtm.galaxy.{doi_suffix}"

    # Format the current date
    date = datetime.now().strftime("%Y-%m-%d")

    # Create a title
    title = f"Galaxy candidates for {graceid} - {alert_type}"

    # Prepare metadata for DOI service
    metadata = {
        "doi": doi,
        "creators": creators,
        "titles": [{"title": title}],
        "publisher": "Gravitational-Wave Treasure Map",
        "publicationYear": date[:4],
        "resourceType": {"resourceTypeGeneral": "Dataset"},
        "descriptions": [{
            "description": f"Galaxy candidates for gravitational-wave event {graceid}",
            "descriptionType": "Abstract"
        }]
    }

    # Add reference if provided
    if reference:
        metadata["relatedIdentifiers"] = [{
            "relatedIdentifier": reference,
            "relatedIdentifierType": "DOI",
            "relationType": "References"
        }]

    # In a real implementation, we would make an API call to the DOI service
    # e.g., DataCite, with the metadata
    # Here we're simulating that

    # This would be the DOI URL from the service
    doi_url = f"https://doi.org/{doi}"

    # This would be the ID returned from the DOI service
    # Here we're generating a random number based on the UUID
    doi_id = int(doi_suffix, 16) % 1000000

    return doi_id, doi_url
