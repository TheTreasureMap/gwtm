"""Get GLADE galaxies endpoint."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.auth.auth import get_current_user

router = APIRouter(tags=["galaxies"])


@router.get("/glade")
async def get_galaxies(
    ra: Optional[float] = Query(None, description="Right ascension"),
    dec: Optional[float] = Query(None, description="Declination"),
    name: Optional[str] = Query(None, description="Galaxy name to search for"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Get galaxies from the GLADE catalog.
    """
    from server.utils.function import isFloat
    from server.db.models.glade import Glade2P3

    filter_conditions = []
    base_filter = [
        Glade2P3.pgc_number != -1,
        Glade2P3.distance > 0,
        Glade2P3.distance < 100,
    ]

    # Create base query
    query = db.query(Glade2P3).filter(*base_filter)

    # Handle orderby for positioning
    orderby = []

    # Handle ra and dec
    if ra is not None and dec is not None and isFloat(ra) and isFloat(dec):
        from sqlalchemy import func

        geom = f"SRID=4326;POINT({ra} {dec})"
        orderby.append(func.ST_Distance(Glade2P3.position, geom))

    # Handle name search
    if name:
        from sqlalchemy import or_

        or_conditions = [
            Glade2P3._2mass_name.contains(name.strip()),
            Glade2P3.gwgc_name.contains(name.strip()),
            Glade2P3.hyperleda_name.contains(name.strip()),
            Glade2P3.sdssdr12_name.contains(name.strip()),
        ]
        filter_conditions.append(or_(*or_conditions))

    # Execute query
    galaxies = query.filter(*filter_conditions).order_by(*orderby).limit(15).all()

    # Parse galaxies to dict format
    result = []
    for galaxy in galaxies:
        # Convert to dict
        galaxy_dict = {
            c.name: getattr(galaxy, c.name) for c in galaxy.__table__.columns
        }

        # Convert position to WKT string if it exists
        if galaxy.position:
            shape = to_shape(galaxy.position)
            galaxy_dict["position"] = str(shape)

        result.append(galaxy_dict)

    return result
