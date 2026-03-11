"""Event galaxies endpoint."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from server.db.database import get_db
from server.db.models.gw_galaxy import GWGalaxyList, GWGalaxyEntry

logger = logging.getLogger(__name__)
router = APIRouter(tags=["UI"])


@router.get("/ajax_event_galaxies")
async def ajax_event_galaxies(alertid: str, db: Session = Depends(get_db)):
    """Get galaxies associated with an event."""
    from server.utils.function import sanatize_pointing, sanatize_gal_info

    event_galaxies = []

    logger.info("[Galaxy debug] ajax_event_galaxies called with alertid=%s", alertid)

    # Resolve alternate IDs to canonical graceid
    from server.db.models.gw_alert import GWAlert
    graceid = GWAlert.graceidfromalternate(alertid, db)
    if graceid != alertid:
        logger.info("[Galaxy debug] resolved alternateid %s -> graceid %s", alertid, graceid)

    # Get galaxy lists for this alert
    gal_lists = db.query(GWGalaxyList).filter(GWGalaxyList.graceid == graceid).all()

    logger.info("[Galaxy debug] found %d galaxy lists for graceid=%s", len(gal_lists), graceid)

    if not gal_lists:
        return event_galaxies

    gal_list_ids = list(set([x.id for x in gal_lists]))

    # Get galaxy entries for these lists
    gal_entries = (
        db.query(
            GWGalaxyEntry.name,
            func.ST_AsText(GWGalaxyEntry.position).label("position"),
            GWGalaxyEntry.score,
            GWGalaxyEntry.info,
            GWGalaxyEntry.listid,
            GWGalaxyEntry.rank,
        )
        .filter(GWGalaxyEntry.listid.in_(gal_list_ids))
        .all()
    )

    # Process each list
    for glist in gal_lists:
        markers = []
        entries = [x for x in gal_entries if x.listid == glist.id]

        for e in entries:
            ra, dec = sanatize_pointing(e.position)
            markers.append(
                {
                    "name": e.name,
                    "ra": ra,
                    "dec": dec,
                    "info": sanatize_gal_info(e, glist, ra, dec),
                }
            )

        event_galaxies.append(
            {"name": glist.groupname, "color": "", "markers": markers}
        )

    logger.info(
        "[Galaxy debug] returning %d galaxy groups, total markers: %d",
        len(event_galaxies),
        sum(len(g["markers"]) for g in event_galaxies),
    )
    return event_galaxies
