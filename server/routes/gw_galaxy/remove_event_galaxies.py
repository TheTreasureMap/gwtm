"""Remove event galaxies endpoint."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_galaxy import GWGalaxyList, GWGalaxyEntry
from server.auth.auth import get_current_user
from server.utils.error_handling import not_found_exception, permission_exception

router = APIRouter(tags=["galaxies"])


@router.delete("/remove_event_galaxies")
async def remove_event_galaxies(
        listid: int = Query(..., description="ID of the galaxy list to remove"),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Remove galaxies associated with a GW event.
    """
    # Find galaxy list
    galaxy_list = db.query(GWGalaxyList).filter(GWGalaxyList.id == listid).first()

    if not galaxy_list:
        raise not_found_exception("No galaxies found with that list ID")

    # Check permissions
    if user.id != galaxy_list.submitterid:
        raise permission_exception("You can only delete information related to your API token")

    # Find and delete galaxy entries
    galaxy_entries = db.query(GWGalaxyEntry).filter(GWGalaxyEntry.listid == listid).all()

    for entry in galaxy_entries:
        db.delete(entry)

    db.delete(galaxy_list)
    db.commit()

    return {"message": "Successfully deleted your galaxy list"}