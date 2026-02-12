"""DOI creation utilities for pointings and galaxy scores."""

import json
from typing import List, Dict, Any, Tuple, Optional

import requests

from server import config
from server.core.enums.pointingstatus import PointingStatus
from server.db.models.pointing import Pointing
from server.schemas.pointing import PointingSchema


def create_doi(payload):
    """Submit a dataset to Zenodo and publish it, returning the DOI."""
    ACCESS_TOKEN = config.settings.ZENODO_ACCESS_KEY
    data = payload["data"]
    data_file = payload["data_file"]
    files = payload["files"]
    headers = payload["headers"]

    r = requests.post(
        "https://zenodo.org/api/deposit/depositions",
        params={"access_token": ACCESS_TOKEN},
        json={},
        headers=headers,
    )

    if r.status_code == 403:
        return None, None

    d_id = r.json()["id"]
    requests.post(
        "https://zenodo.org/api/deposit/depositions/%s/files" % d_id,
        params={"access_token": ACCESS_TOKEN},
        data=data_file,
        files=files,
    )
    requests.put(
        "https://zenodo.org/api/deposit/depositions/%s" % d_id,
        data=json.dumps(data),
        params={"access_token": ACCESS_TOKEN},
        headers=headers,
    )
    r = requests.post(
        "https://zenodo.org/api/deposit/depositions/%s/actions/publish" % d_id,
        params={"access_token": ACCESS_TOKEN},
    )

    return_json = r.json()
    try:
        doi_url = return_json["doi_url"]
    except (KeyError, TypeError):
        doi_url = None

    return int(d_id), doi_url


def create_pointing_doi(
    points: List[Pointing],
    graceid: str,
    creators: List[Dict[str, str]],
    instrument_names: List[str],
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
        if p.status == PointingStatus.completed:
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
        inst_str = (
            "These observations were taken on the "
            + instrument_names[0]
            + " instrument."
        )

    if len(points_json):
        payload = {
            "data": {
                "metadata": {
                    "title": "Submitted Completed pointings to the Gravitational Wave Treasure Map for event "
                    + graceid,
                    "upload_type": "dataset",
                    "creators": creators,
                    "description": "Attached in a .json file is the completed pointing information for "
                    + str(len(points_json))
                    + " observation(s) for the EM counterpart search associated with the gravitational wave event "
                    + graceid
                    + ". "
                    + inst_str,
                }
            },
            "data_file": {"name": "completed_pointings_" + graceid + ".json"},
            "files": {
                "file": json.dumps([p.model_dump(mode="json") for p in points_json])
            },
            "headers": {"Content-Type": "application/json"},
        }

        d_id, url = create_doi(payload)
        return d_id, url

    return None, None


def create_galaxy_score_doi(
    galaxies: List[Any],
    creators: List[Dict[str, str]],
    reference: Optional[str],
    graceid: str,
    alert_type: str,
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
        "descriptions": [
            {
                "description": f"Galaxy candidates for gravitational-wave event {graceid}",
                "descriptionType": "Abstract",
            }
        ],
    }

    # Add reference if provided
    if reference:
        metadata["relatedIdentifiers"] = [
            {
                "relatedIdentifier": reference,
                "relatedIdentifierType": "DOI",
                "relationType": "References",
            }
        ]

    # In a real implementation, we would make an API call to the DOI service
    # e.g., DataCite, with the metadata
    # Here we're simulating that

    # This would be the DOI URL from the service
    doi_url = f"https://doi.org/{doi}"

    # This would be the ID returned from the DOI service
    # Here we're generating a random number based on the UUID
    doi_id = int(doi_suffix, 16) % 1000000

    return doi_id, doi_url
