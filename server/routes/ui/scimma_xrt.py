"""SCIMMA XRT endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert

router = APIRouter(tags=["UI"])


@router.get("/ajax_scimma_xrt")
async def ajax_scimma_xrt(
    graceid: str,
    db: Session = Depends(get_db)
):
    """Get SCIMMA XRT sources associated with a GW event."""
    import requests
    import urllib.parse
    from server.utils.function import sanatize_XRT_source_info
    
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
        if response.status_code == 200:
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