from fastapi import APIRouter, Depends, Query, Body
from server.utils.error_handling import validation_exception, not_found_exception, permission_exception
from geoalchemy2.shape import to_shape
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import datetime
from dateutil.parser import parse as date_parse


from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.gw_galaxy import GWGalaxy, EventGalaxy, GWGalaxyScore, GWGalaxyList, GWGalaxyEntry
from server.auth.auth import get_current_user
from server.schemas.gw_galaxy import (
    GWGalaxySchema,
    EventGalaxySchema,
    GWGalaxyScoreSchema,
    GWGalaxyListSchema,
    GWGalaxyEntrySchema,
    PostEventGalaxiesRequest,
    PostEventGalaxiesResponse,
    GalaxyEntryCreate
)

router = APIRouter(tags=["galaxies"])


@router.get("/event_galaxies", response_model=List[GWGalaxyEntrySchema])
async def get_event_galaxies(
        graceid: str = Query(..., description="Grace ID of the GW event"),
        timesent_stamp: Optional[str] = None,
        listid: Optional[int] = None,
        groupname: Optional[str] = None,
        score_gt: Optional[float] = None,
        score_lt: Optional[float] = None,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Get galaxies associated with a GW event.
    """
    filter_conditions = [GWGalaxyEntry.listid == GWGalaxyList.id]

    # Normalize the graceid
    graceid = GWAlert.graceidfromalternate(graceid)
    filter_conditions.append(GWGalaxyList.graceid == graceid)

    if timesent_stamp:
        try:
            time = date_parse(timesent_stamp)
        except ValueError:
            raise validation_exception(
                message="Error parsing date",
                errors=[f"Timestamp should be in %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00"]
            )

        # Find the alert with the given time and graceid
        alert = db.query(GWAlert).filter(
            GWAlert.timesent < time + datetime.timedelta(seconds=15),
            GWAlert.timesent > time - datetime.timedelta(seconds=15),
            GWAlert.graceid == graceid
        ).first()

        if not alert:
            raise validation_exception(
                message=f"Invalid 'timesent_stamp' for event {graceid}",
                errors=[f"Please visit http://treasuremap.space/alerts?graceids={graceid} for valid timesent stamps for this event"]
            )

        filter_conditions.append(GWGalaxyList.alertid == str(alert.id))

    if listid:
        filter_conditions.append(GWGalaxyList.id == listid)
    if groupname:
        filter_conditions.append(GWGalaxyList.groupname == groupname)
    if score_gt is not None:
        filter_conditions.append(GWGalaxyEntry.score >= score_gt)
    if score_lt is not None:
        filter_conditions.append(GWGalaxyEntry.score <= score_lt)

    galaxy_entries = db.query(GWGalaxyEntry).join(
        GWGalaxyList, GWGalaxyList.id == GWGalaxyEntry.listid
    ).filter(*filter_conditions).all()

    # Convert GeoAlchemy2 Geography to a string for Pydantic
    result_entries = []
    for entry in galaxy_entries:
        entry_dict = {
            "id": entry.id,
            "listid": entry.listid,
            "name": entry.name,
            "score": entry.score,
            "rank": entry.rank,
            "info": entry.info
        }

        # Convert position to WKT string
        if entry.position:
            shape = to_shape(entry.position)
            entry_dict['position'] = str(shape)

        result_entries.append(GWGalaxyEntrySchema(**entry_dict))

    return result_entries


@router.post("/event_galaxies", response_model=PostEventGalaxiesResponse)
async def post_event_galaxies(
        request: PostEventGalaxiesRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Post galaxies associated with a GW event.
    """
    # Normalize the graceid
    graceid = GWAlert.graceidfromalternate(request.graceid)

    # Parse timesent_stamp
    try:
        print(f"Parsing timesent_stamp: {request.timesent_stamp}")
        time = date_parse(request.timesent_stamp)
    except ValueError:
        raise validation_exception(
            message="Error parsing date",
            errors=["Timestamp should be in %Y-%m-%dT%H:%M:%S.%f format. e.g. 2019-05-01T12:00:00.00"]
        )

    # Find the alert
    alert = db.query(GWAlert).filter(
        GWAlert.timesent < time + datetime.timedelta(seconds=15),
        GWAlert.timesent > time - datetime.timedelta(seconds=15),
        GWAlert.graceid == graceid
    ).first()

    if not alert:
        raise validation_exception(
            message=f"Invalid 'timesent_stamp' for event {graceid}",
            errors=[f"Please visit http://treasuremap.space/alerts?graceids={graceid} for valid timesent stamps for this event"]
        )

    # Handle groupname - default to username if not provided
    groupname = request.groupname or user.username

    # Handle DOI creators
    post_doi = request.request_doi
    doi_string = ". "
    creators = None

    if post_doi:
        if request.creators:
            creators = []
            for c in request.creators:
                # Since request.creators is List[DOICreator] from Pydantic,
                # c is a DOICreator object, not a dict
                if not c.name or not c.affiliation:
                    raise validation_exception(
                        message="Invalid DOI creator information",
                        errors=["name and affiliation are required for each creator in the list"]
                    )
                creator_dict = { 'name': c.name, 'affiliation': c.affiliation }
                if c.orcid:
                    creator_dict['orcid'] = c.orcid
                if c.gnd:
                    creator_dict['gnd'] = c.gnd
                creators.append(creator_dict)
        elif request.doi_group_id:
            from server.db.models.doi_author import DOIAuthor
            valid, creators_list = DOIAuthor.construct_creators(request.doi_group_id, user.id, db)
            if not valid:
                raise validation_exception(
                    message="Invalid DOI group ID",
                    errors=["Make sure you are the User associated with the DOI group"]
                )
            creators = creators_list
        else:
            creators = [{'name': f"{user.firstname} {user.lastname}", 'affiliation': ''}]

    # Create galaxy list
    gw_galaxy_list = GWGalaxyList(
        submitterid=user.id,
        graceid=graceid,
        alertid=str(alert.id),
        groupname=groupname,
        reference=request.reference,
    )
    db.add(gw_galaxy_list)
    db.flush()

    # Process galaxies
    valid_galaxies = []
    errors = []
    warnings = []

    for galaxy_entry in request.galaxies:
        try:
            # Create the galaxy entry from the Pydantic model
            gw_galaxy_entry = GWGalaxyEntry(
                listid=gw_galaxy_list.id,
                name=galaxy_entry.name,
                score=galaxy_entry.score,
                rank=galaxy_entry.rank,
                info=galaxy_entry.info
            )

            # Handle position data - use position string if provided, otherwise build from ra/dec
            if galaxy_entry.position:
                if all(x in galaxy_entry.position for x in
                       ["POINT", "(", ")", " "]) and "," not in galaxy_entry.position:
                    gw_galaxy_entry.position = galaxy_entry.position
                else:
                    errors.append([
                        f"Object: {galaxy_entry.dict()}",
                        ["Invalid position argument. Must be geometry type \"POINT(RA DEC)\""]
                    ])
                    continue
            elif galaxy_entry.ra is not None and galaxy_entry.dec is not None:
                gw_galaxy_entry.position = f"POINT({galaxy_entry.ra} {galaxy_entry.dec})"
            else:
                errors.append([
                    f"Object: {galaxy_entry.dict()}",
                    ["Position data is required. Provide either position or ra/dec coordinates."]
                ])
                continue

            # All validation passed, add to database
            db.add(gw_galaxy_entry)
            valid_galaxies.append(gw_galaxy_entry)

        except Exception as e:
            errors.append([f"Object: {galaxy_entry.dict()}", [str(e)]])

    db.flush()

    # Handle DOI if requested
    if post_doi and valid_galaxies:
        from server.utils.function import create_galaxy_score_doi

        doi_id, url = create_galaxy_score_doi(valid_galaxies, creators, request.reference, graceid,
                                              alert.alert_type)

        if url is None and doi_id is not None:
            errors.append(
                "There was an error with the DOI request. Please ensure that author group's ORIC/GND values are accurate")
        else:
            gw_galaxy_list.doi_id = doi_id
            gw_galaxy_list.doi_url = url
            doi_string = f". DOI url: {url}."

    db.commit()

    return PostEventGalaxiesResponse(
        message=f"Successful adding of {len(valid_galaxies)} galaxies for event {graceid}{doi_string} List ID: {gw_galaxy_list.id}",
        errors=errors,
        warnings=warnings
    )


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


@router.get("/glade")
async def get_galaxies(
        ra: Optional[float] = Query(None, description="Right ascension"),
        dec: Optional[float] = Query(None, description="Declination"),
        name: Optional[str] = Query(None, description="Galaxy name to search for"),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
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
        Glade2P3.distance < 100
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
            Glade2P3.sdssdr12_name.contains(name.strip())
        ]
        filter_conditions.append(or_(*or_conditions))

    # Execute query
    galaxies = query.filter(*filter_conditions).order_by(*orderby).limit(15).all()

    # Parse galaxies to dict format
    result = []
    for galaxy in galaxies:
        # Convert to dict
        galaxy_dict = {c.name: getattr(galaxy, c.name) for c in galaxy.__table__.columns}

        # Convert position to WKT string if it exists
        if galaxy.position:
            shape = to_shape(galaxy.position)
            galaxy_dict['position'] = str(shape)

        result.append(galaxy_dict)

    return result
