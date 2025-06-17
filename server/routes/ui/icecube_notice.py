"""IceCube notice endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.icecube import IceCubeNotice, IceCubeNoticeCoincEvent

router = APIRouter(tags=["UI"])


@router.get("/ajax_icecube_notice")
async def ajax_icecube_notice(
    graceid: str,
    db: Session = Depends(get_db)
):
    """Get IceCube notices associated with a GW event."""
    from server.utils.function import sanatize_icecube_event
    
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