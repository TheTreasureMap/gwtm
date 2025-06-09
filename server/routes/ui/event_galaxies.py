"""Event galaxies endpoint."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.db.database import get_db
from server.db.models.gw_galaxy import GWGalaxyList, GWGalaxyEntry

router = APIRouter(tags=["UI"])


@router.get("/ajax_event_galaxies")
async def ajax_event_galaxies(
    alertid: str,
    db: Session = Depends(get_db)
):
    """Get galaxies associated with an event."""
    from server.utils.function import sanatize_pointing, sanatize_gal_info
    
    event_galaxies = []
    
    # Get galaxy lists for this alert
    gal_lists = db.query(GWGalaxyList).filter(
        GWGalaxyList.alertid == alertid
    ).all()
    
    if not gal_lists:
        return event_galaxies
    
    gal_list_ids = list(set([x.id for x in gal_lists]))
    
    # Get galaxy entries for these lists
    gal_entries = db.query(
        GWGalaxyEntry.name,
        func.ST_AsText(GWGalaxyEntry.position).label('position'),
        GWGalaxyEntry.score,
        GWGalaxyEntry.info,
        GWGalaxyEntry.listid,
        GWGalaxyEntry.rank
    ).filter(
        GWGalaxyEntry.listid.in_(gal_list_ids)
    ).all()
    
    # Process each list
    for glist in gal_lists:
        markers = []
        entries = [x for x in gal_entries if x.listid == glist.id]
        
        for e in entries:
            ra, dec = sanatize_pointing(e.position)
            markers.append({
                "name": e.name,
                "ra": ra,
                "dec": dec,
                "info": sanatize_gal_info(e, glist)
            })
        
        event_galaxies.append({
            "name": glist.groupname,
            "color": "",
            "markers": markers
        })
    
    return event_galaxies