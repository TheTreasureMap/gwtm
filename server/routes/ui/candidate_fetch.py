"""Candidate fetch endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.candidate import GWCandidate
from server.db.models.gw_alert import GWAlert

router = APIRouter(tags=["UI"])


@router.get("/ajax_candidate")
async def ajax_candidate_fetch(
    graceid: str,
    db: Session = Depends(get_db)
):
    """Get candidates associated with a GW event."""
    from server.utils.function import sanatize_pointing, sanatize_candidate_info
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