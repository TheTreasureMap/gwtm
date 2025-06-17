"""Post event galaxies endpoint."""

import datetime
from dateutil.parser import parse as date_parse
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.gw_galaxy import GWGalaxyList, GWGalaxyEntry
from server.auth.auth import get_current_user
from server.schemas.gw_galaxy import PostEventGalaxiesRequest, PostEventGalaxiesResponse
from server.utils.error_handling import validation_exception

router = APIRouter(tags=["galaxies"])


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