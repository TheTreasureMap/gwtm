# server/routes/pointing.py
from fastapi import APIRouter, Depends, Query, Body, HTTPException

from server.db.models.doi_author import DOIAuthor
from server.utils.error_handling import validation_exception, not_found_exception, permission_exception
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
import json

from server.db.database import get_db
from server.db.models.pointing import Pointing
from server.db.models.instrument import Instrument
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_alert import GWAlert
from server.db.models.users import Users
from server.schemas.pointing import (
    PointingSchema,
    PointingResponse,
    PointingUpdate,
    PointingCreateRequest,
    CancelAllRequest,
    DOIRequest
)
from server.schemas.doi import DOIRequestResponse
from server.auth.auth import get_current_user
from server.utils.function import pointing_crossmatch, create_pointing_doi
from server.core.enums.pointing_status import pointing_status as pointing_status_enum
from server.core.enums.depth_unit import depth_unit as depth_unit_enum
from server.core.enums.bandpass import bandpass as bandpass_enum
from server.services.pointing_service import PointingService


router = APIRouter(tags=["pointings"])


@router.post("/pointings", response_model=PointingResponse)
async def add_pointings(
        request: PointingCreateRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Add new pointings to the database.
    """
    # Initialize variables
    points = []
    errors = []
    warnings = []

    # Validate graceid exists
    PointingService.validate_graceid(request.graceid, db)

    # Prepare DOI creators if DOI is requested
    creators = None
    if request.request_doi:
        creators = PointingService.prepare_doi_creators(
            request.creators, request.doi_group_id, user, db
        )

    # Get instruments for validation
    instruments_dict = PointingService.get_instruments_dict(db)

    # Get existing pointings for duplicate check
    existing_pointings = db.query(Pointing).filter(
        Pointing.id == PointingEvent.pointingid,
        PointingEvent.graceid == request.graceid
    ).all()

    # Process pointings (either single or multiple)
    pointings_to_process = []
    if request.pointing:
        pointings_to_process = [request.pointing]
    elif request.pointings:
        pointings_to_process = request.pointings

    for pointing_data in pointings_to_process:
        try:
            # Check if this is an update to a planned pointing
            if hasattr(pointing_data, 'id') and pointing_data.id:
                # Handle planned pointing update
                pointing_obj = PointingService.handle_planned_pointing_update(
                    pointing_data, user.id, db
                )
            else:
                # Validate and resolve instrument reference
                instrument_id = PointingService.validate_instrument_reference(
                    pointing_data, instruments_dict
                )
                
                # Create new pointing object
                pointing_obj = PointingService.create_pointing_from_schema(
                    pointing_data, user.id, instrument_id
                )
                
                # Check for duplicates
                if PointingService.check_duplicate_pointing(pointing_obj, existing_pointings):
                    errors.append([f"Object: {pointing_data.dict()}", ["Pointing already submitted"]])
                    continue

            points.append(pointing_obj)
            db.add(pointing_obj)

        except Exception as e:
            errors.append([f"Object: {pointing_data.model_dump()}", [str(e)]])

    # Flush to get pointing IDs
    db.flush()

    # Create pointing events (this should always happen when we have valid points and graceid)
    if points:  # Only create pointing events if we have valid points
        for p in points:
            pointing_event = PointingEvent(
                pointingid=p.id,
                graceid=request.graceid
            )
            db.add(pointing_event)

    db.flush()
    db.commit()

    # Handle DOI creation if requested
    doi_url = None
    if request.request_doi and points:
        if request.doi_url:
            doi_id, doi_url = 0, request.doi_url
        else:
            doi_id, doi_url = PointingService.create_doi_for_pointings(
                points, request.graceid, creators, db
            )

        if doi_id is not None:
            for p in points:
                p.doi_url = doi_url
                p.doi_id = doi_id

            db.flush()
            db.commit()

    # Return response
    return PointingResponse(
        pointing_ids=[p.id for p in points],
        ERRORS=errors,
        WARNINGS=warnings,
        DOI=doi_url
    )



@router.get("/pointings", response_model=List[PointingSchema])
def get_pointings(
        # Basic filters
        graceid: Optional[str] = Query(None, description="Grace ID of the GW event"),
        graceids: Optional[str] = Query(None, description="Comma-separated list or JSON array of Grace IDs"),
        id: Optional[int] = Query(None, description="Filter by pointing ID"),
        ids: Optional[str] = Query(None, description="Comma-separated list or JSON array of pointing IDs"),

        # Status filters
        status: Optional[str] = Query(None, description="Filter by status (planned, completed, cancelled)"),
        statuses: Optional[str] = Query(None, description="Comma-separated list or JSON array of statuses"),

        # Time filters
        completed_after: Optional[datetime] = Query(None,
                                                    description="Filter for pointings completed after this time (ISO format)"),
        completed_before: Optional[datetime] = Query(None,
                                                     description="Filter for pointings completed before this time (ISO format)"),
        planned_after: Optional[datetime] = Query(None,
                                                  description="Filter for pointings planned after this time (ISO format)"),
        planned_before: Optional[datetime] = Query(None,
                                                   description="Filter for pointings planned before this time (ISO format)"),

        # User filters
        user: Optional[str] = Query(None, description="Filter by username, first name, or last name"),
        users: Optional[str] = Query(None, description="Comma-separated list or JSON array of usernames"),

        # Instrument filters
        instrument: Optional[str] = Query(None, description="Filter by instrument ID or name"),
        instruments: Optional[str] = Query(None,
                                           description="Comma-separated list or JSON array of instrument IDs or names"),

        # Band filters
        band: Optional[str] = Query(None, description="Filter by band"),
        bands: Optional[str] = Query(None, description="Comma-separated list or JSON array of bands"),

        # Spectral filters
        wavelength_regime: Optional[str] = Query(None, description="Filter by wavelength regime [min, max]"),
        wavelength_unit: Optional[str] = Query(None, description="Wavelength unit (angstrom, nanometer, micron)"),
        frequency_regime: Optional[str] = Query(None, description="Filter by frequency regime [min, max]"),
        frequency_unit: Optional[str] = Query(None, description="Frequency unit (Hz, kHz, MHz, GHz, THz)"),
        energy_regime: Optional[str] = Query(None, description="Filter by energy regime [min, max]"),
        energy_unit: Optional[str] = Query(None, description="Energy unit (eV, keV, MeV, GeV, TeV)"),

        # Depth filters
        depth_gt: Optional[float] = Query(None, description="Filter by depth greater than this value"),
        depth_lt: Optional[float] = Query(None, description="Filter by depth less than this value"),
        depth_unit: Optional[str] = Query(None, description="Depth unit (ab_mag, vega_mag, flux_erg, flux_jy)"),

        # DB access
        db: Session = Depends(get_db),
        user_auth=Depends(get_current_user)
):
    """
    Retrieve pointings from the database with optional filters.
    """
    from server.utils.function import isInt, isFloat
    from server.core.enums.wavelength_units import wavelength_units
    from server.core.enums.frequency_units import frequency_units
    from server.core.enums.energy_units import energy_units
    from server.core.enums.bandpass import bandpass
    from server.core.enums.depth_unit import depth_unit as depth_unit_enum

    try:
        # Build the filter conditions
        filter_conditions = []

        # Handle graceid
        if graceid:
            # Normalize the graceid
            graceid = GWAlert.graceidfromalternate(graceid)
            filter_conditions.append(PointingEvent.graceid == graceid)
            filter_conditions.append(PointingEvent.pointingid == Pointing.id)

        # Handle graceids
        if graceids:
            gids = []
            try:
                if isinstance(graceids, str):
                    if '[' in graceids and ']' in graceids:
                        # Parse as JSON array
                        gids = json.loads(graceids)
                    else:
                        # Parse as comma-separated list
                        gids = [g.strip() for g in graceids.split(',')]
                else:
                    gids = graceids  # Already a list

                normalized_gids = [GWAlert.graceidfromalternate(gid) for gid in gids]
                filter_conditions.append(PointingEvent.graceid.in_(normalized_gids))
                filter_conditions.append(PointingEvent.pointingid == Pointing.id)
            except Exception as e:
                raise validation_exception(
                    message="Error parsing 'graceids'",
                    errors=[f"Required format is a list: '[graceid1, graceid2...]'", str(e)]
                )

        # Handle ID filters
        if id:
            if isInt(id):
                filter_conditions.append(Pointing.id == int(id))
            else:
                raise validation_exception(message="Invalid ID format", errors=["ID must be an integer"])

        if ids:
            try:
                id_list = []
                if isinstance(ids, str):
                    if '[' in ids and ']' in ids:
                        # Parse as JSON array
                        id_list = json.loads(ids)
                    else:
                        # Parse as comma-separated list
                        id_list = [int(i.strip()) for i in ids.split(',') if isInt(i.strip())]
                else:
                    id_list = ids  # Already a list

                filter_conditions.append(Pointing.id.in_(id_list))
            except Exception as e:
                raise validation_exception(
                    message="Error parsing 'ids'",
                    errors=[f"Required format is a list: '[id1, id2...]'", str(e)]
                )

        # Handle band filters
        if band:
            for b in bandpass:
                if b.name == band:
                    filter_conditions.append(Pointing.band == b)
                    break
            else:
                raise validation_exception(message="Invalid band", errors=[f"The band '{band}' is not valid"])

        if bands:
            try:
                band_list = []
                if isinstance(bands, str):
                    if '[' in bands and ']' in bands:
                        # Parse as JSON array
                        band_list = json.loads(bands)
                    else:
                        # Parse as comma-separated list
                        band_list = [b.strip() for b in bands.split(',')]
                else:
                    band_list = bands  # Already a list

                valid_bands = []
                for b in bandpass:
                    if b.name in band_list:
                        valid_bands.append(b)

                if valid_bands:
                    filter_conditions.append(Pointing.band.in_(valid_bands))
                else:
                    raise validation_exception(message="No valid bands", errors=["No valid bands were specified"])
            except Exception as e:
                raise validation_exception(
                    message="Error parsing bands",
                    errors=[f"Invalid format for 'bands' parameter. Required format is a list: '[band1, band2...]'",
                            str(e)]
                )

        # Handle status filters
        if status:
            if status == "planned":
                filter_conditions.append(Pointing.status == pointing_status_enum.planned)
            elif status == "completed":
                filter_conditions.append(Pointing.status == pointing_status_enum.completed)
            elif status == "cancelled":
                filter_conditions.append(Pointing.status == pointing_status_enum.cancelled)
            else:
                raise validation_exception(
                    message=f"Invalid status: {status}",
                    errors=["Only 'completed', 'planned', and 'cancelled' are valid."]
                )

        if statuses:
            try:
                status_list = []
                if isinstance(statuses, str):
                    if '[' in statuses and ']' in statuses:
                        # Parse as JSON array
                        status_list = json.loads(statuses)
                    else:
                        # Parse as comma-separated list
                        status_list = [s.strip() for s in statuses.split(',')]
                else:
                    status_list = statuses  # Already a list

                valid_statuses = []
                if "planned" in status_list:
                    valid_statuses.append(pointing_status_enum.planned)
                if "completed" in status_list:
                    valid_statuses.append(pointing_status_enum.completed)
                if "cancelled" in status_list:
                    valid_statuses.append(pointing_status_enum.cancelled)

                if valid_statuses:
                    filter_conditions.append(Pointing.status.in_(valid_statuses))
                else:
                    raise validation_exception(message="No valid statuses",
                                               errors=["No valid status values were specified"])
            except Exception as e:
                raise validation_exception(
                    message="Error parsing statuses",
                    errors=[
                        f"Invalid format for 'statuses' parameter. Required format is a list: '[status1, status2...]'",
                        str(e)]
                )

        # Handle time filters
        if completed_after:
            try:
                filter_conditions.append(Pointing.status == pointing_status_enum.completed)
                filter_conditions.append(Pointing.time >= completed_after)
            except ValueError:
                raise validation_exception(
                    message="Error parsing date",
                    errors=["Should be ISO format, e.g. 2019-05-01T12:00:00.00"]
                )

        if completed_before:
            try:
                filter_conditions.append(Pointing.status == pointing_status_enum.completed)
                filter_conditions.append(Pointing.time <= completed_before)
            except ValueError:
                raise validation_exception(
                    message="Error parsing date",
                    errors=["Should be ISO format, e.g. 2019-05-01T12:00:00.00"]
                )

        if planned_after:
            try:
                filter_conditions.append(Pointing.status == pointing_status_enum.planned)
                filter_conditions.append(Pointing.time >= planned_after)
            except ValueError:
                raise validation_exception(
                    message="Error parsing date",
                    errors=["Should be ISO format, e.g. 2019-05-01T12:00:00.00"]
                )

        if planned_before:
            try:
                filter_conditions.append(Pointing.status == pointing_status_enum.planned)
                filter_conditions.append(Pointing.time <= planned_before)
            except ValueError:
                raise validation_exception(
                    message="Error parsing date",
                    errors=["Should be ISO format, e.g. 2019-05-01T12:00:00.00"]
                )

            # Handle user filters
        if user:
            if isInt(user):
                filter_conditions.append(Pointing.submitterid == int(user))
            else:
                filter_conditions.append(or_(
                    Users.username.contains(user),
                    Users.firstname.contains(user),
                    Users.lastname.contains(user)
                ))
                filter_conditions.append(Users.id == Pointing.submitterid)

        if users:
            try:
                user_list = []
                if isinstance(users, str):
                    if '[' in users and ']' in users:
                        # Parse as JSON array
                        user_list = json.loads(users)
                    else:
                        # Parse as comma-separated list
                        user_list = [u.strip() for u in users.split(',')]
                else:
                    user_list = users  # Already a list

                or_conditions = []
                for u in user_list:
                    or_conditions.append(Users.username.contains(str(u).strip()))
                    or_conditions.append(Users.firstname.contains(str(u).strip()))
                    or_conditions.append(Users.lastname.contains(str(u).strip()))
                    if isInt(u):
                        or_conditions.append(Pointing.submitterid == int(u))

                filter_conditions.append(or_(*or_conditions))
                filter_conditions.append(Users.id == Pointing.submitterid)
            except Exception as e:
                raise validation_exception(
                    message="Error parsing 'users'",
                    errors=[f"Required format is a list: '[user1, user2...]'", str(e)]
                )

            # Handle instrument filters
        if instrument:
            if isInt(instrument):
                filter_conditions.append(Pointing.instrumentid == int(instrument))
            else:
                filter_conditions.append(Instrument.instrument_name.contains(instrument))
                filter_conditions.append(Pointing.instrumentid == Instrument.id)

        if instruments:
            try:
                inst_list = []
                if isinstance(instruments, str):
                    if '[' in instruments and ']' in instruments:
                        # Parse as JSON array
                        inst_list = json.loads(instruments)
                    else:
                        # Parse as comma-separated list
                        inst_list = [i.strip() for i in instruments.split(',')]
                else:
                    inst_list = instruments  # Already a list

                or_conditions = []
                for i in inst_list:
                    or_conditions.append(Instrument.instrument_name.contains(str(i).strip()))
                    or_conditions.append(Instrument.nickname.contains(str(i).strip()))
                    if isInt(i):
                        or_conditions.append(Pointing.instrumentid == int(i))

                filter_conditions.append(or_(*or_conditions))
                filter_conditions.append(Instrument.id == Pointing.instrumentid)
            except Exception as e:
                raise validation_exception(
                    message="Error parsing 'instruments'",
                    errors=[f"Required format is a list: '[inst1, inst2...]'", str(e)]
                )

            # Handle spectral filters
        if wavelength_regime and wavelength_unit:
            try:
                if isinstance(wavelength_regime, str):
                    if '[' in wavelength_regime and ']' in wavelength_regime:
                        # Parse range from string
                        wavelength_range = json.loads(wavelength_regime.replace('(', '[').replace(')', ']'))
                        specmin, specmax = float(wavelength_range[0]), float(wavelength_range[1])
                    else:
                        raise ValueError("Invalid wavelength_regime format")
                elif isinstance(wavelength_regime, list):
                    specmin, specmax = float(wavelength_regime[0]), float(wavelength_regime[1])
                else:
                    raise ValueError("Invalid wavelength_regime type")

                # Get unit and scale
                unit_value = wavelength_unit
                try:
                    unit = [w for w in wavelength_units if int(w) == unit_value or str(w.name) == unit_value][0]
                    scale = wavelength_units.get_scale(unit)
                    specmin = specmin * scale
                    specmax = specmax * scale

                    # Import the spectral handler
                    from server.db.models.pointing import SpectralRangeHandler
                    filter_conditions.append(Pointing.inSpectralRange(
                        specmin, specmax, SpectralRangeHandler.spectralrangetype.wavelength
                    ))
                except (IndexError, ValueError):
                    raise validation_exception(
                        message="Invalid wavelength_unit",
                        errors=["Valid units are 'angstrom', 'nanometer', and 'micron'"]
                    )
            except Exception as e:
                raise validation_exception(
                    message="Error parsing 'wavelength_regime'",
                    errors=[f"Required format is a list: '[low, high]'", str(e)]
                )

        if frequency_regime and frequency_unit:
            try:
                if isinstance(frequency_regime, str):
                    if '[' in frequency_regime and ']' in frequency_regime:
                        # Parse range from string
                        frequency_range = json.loads(frequency_regime.replace('(', '[').replace(')', ']'))
                        specmin, specmax = float(frequency_range[0]), float(frequency_range[1])
                    else:
                        raise ValueError("Invalid frequency_regime format")
                elif isinstance(frequency_regime, list):
                    specmin, specmax = float(frequency_regime[0]), float(frequency_regime[1])
                else:
                    raise ValueError("Invalid frequency_regime type")

                # Get unit and scale
                unit_value = frequency_unit
                try:
                    unit = [f for f in frequency_units if int(f) == unit_value or str(f.name) == unit_value][0]
                    scale = frequency_units.get_scale(unit)
                    specmin = specmin * scale
                    specmax = specmax * scale

                    # Import the spectral handler
                    from server.db.models.pointing import SpectralRangeHandler
                    filter_conditions.append(Pointing.inSpectralRange(
                        specmin, specmax, SpectralRangeHandler.spectralrangetype.frequency
                    ))
                except (IndexError, ValueError):
                    raise validation_exception(
                        message="Invalid frequency_unit",
                        errors=["Valid units are 'Hz', 'kHz', 'MHz', 'GHz', and 'THz'"]
                    )
            except Exception as e:
                raise validation_exception(
                    message="Error parsing 'frequency_regime'",
                    errors=[f"Required format is a list: '[low, high]'", str(e)]
                )

        if energy_regime and energy_unit:
            try:
                if isinstance(energy_regime, str):
                    if '[' in energy_regime and ']' in energy_regime:
                        # Parse range from string
                        energy_range = json.loads(energy_regime.replace('(', '[').replace(')', ']'))
                        specmin, specmax = float(energy_range[0]), float(energy_range[1])
                    else:
                        raise ValueError("Invalid energy_regime format")
                elif isinstance(energy_regime, list):
                    specmin, specmax = float(energy_regime[0]), float(energy_regime[1])
                else:
                    raise ValueError("Invalid energy_regime type")

                # Get unit and scale
                unit_value = energy_unit
                try:
                    unit = [e for e in energy_units if int(e) == unit_value or str(e.name) == unit_value][0]
                    scale = energy_units.get_scale(unit)
                    specmin = specmin * scale
                    specmax = specmax * scale

                    # Import the spectral handler
                    from server.db.models.pointing import SpectralRangeHandler
                    filter_conditions.append(Pointing.inSpectralRange(
                        specmin, specmax, SpectralRangeHandler.spectralrangetype.energy
                    ))
                except (IndexError, ValueError):
                    raise validation_exception(
                        message="Invalid energy_unit",
                        errors=["Valid units are 'eV', 'keV', 'MeV', 'GeV', and 'TeV'"]
                    )
            except Exception as e:
                raise validation_exception(
                    message="Error parsing 'energy_regime'",
                    errors=[f"Required format is a list: '[low, high]'", str(e)]
                )

            # Handle depth filters
        if depth_gt is not None or depth_lt is not None:
            # Determine depth unit
            depth_unit_value = depth_unit or "ab_mag"  # Default to ab_mag if not specified
            try:
                depth_unit_enum_val = [d for d in depth_unit_enum if str(d.name) == depth_unit_value][0]
            except (IndexError, ValueError):
                depth_unit_enum_val = depth_unit_enum.ab_mag  # Default

            # Handle depth_gt (query for brighter things)
            if depth_gt is not None and isFloat(depth_gt):
                if 'mag' in depth_unit_enum_val.name:
                    # For magnitudes, lower values are brighter
                    filter_conditions.append(Pointing.depth <= float(depth_gt))
                elif 'flux' in depth_unit_enum_val.name:
                    # For flux, higher values are brighter
                    filter_conditions.append(Pointing.depth >= float(depth_gt))

            # Handle depth_lt (query for dimmer things)
            if depth_lt is not None and isFloat(depth_lt):
                if 'mag' in depth_unit_enum_val.name:
                    # For magnitudes, higher values are dimmer
                    filter_conditions.append(Pointing.depth >= float(depth_lt))
                elif 'flux' in depth_unit_enum_val.name:
                    # For flux, lower values are dimmer
                    filter_conditions.append(Pointing.depth <= float(depth_lt))

            # Query the database
        pointings = db.query(Pointing).filter(*filter_conditions).all()

        # Let Pydantic handle the conversion of SQLAlchemy models to JSON
        # The field_serializer methods in PointingSchema will take care of enum translations
        return pointings
    except Exception as e:
        raise validation_exception(message="Invalid request", errors=[str(e)])


@router.post("/update_pointings")
async def update_pointings(
        update_pointing: PointingUpdate,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Update the status of planned pointings.

    Parameters:
    - status: The new status for the pointings (only "cancelled" is currently supported)
    - ids: List of pointing IDs to update

    Returns:
    - Message with the number of updated pointings
    """
    try:
        # Add a filter to ensure user can only update their own pointings
        pointings = db.query(Pointing).filter(
            Pointing.id.in_(update_pointing.ids),
            Pointing.submitterid == user.id,
            Pointing.status == pointing_status_enum.planned  # Only planned pointings can be cancelled
        ).all()

        for pointing in pointings:
            pointing.status = update_pointing.status
            pointing.dateupdated = datetime.now()

        db.commit()
        return {"message": f"Updated {len(pointings)} pointings successfully."}
    except Exception as e:
        db.rollback()
        raise validation_exception(message="Invalid request", errors=[str(e)])


@router.post("/cancel_all")
async def cancel_all(
        request: CancelAllRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Cancel all planned pointings for a specific GW event and instrument.
    """
    # Validate instrument exists
    PointingService.validate_instrument(request.instrumentid, db)

    # Validate graceid exists
    normalized_graceid = GWAlert.graceidfromalternate(request.graceid)

    # Build the filter
    filter_conditions = [
        Pointing.status == pointing_status_enum.planned,
        Pointing.submitterid == user.id,
        Pointing.instrumentid == request.instrumentid,
        Pointing.id == PointingEvent.pointingid,
        PointingEvent.graceid == normalized_graceid
    ]

    # Query the pointings
    pointings = db.query(Pointing).filter(*filter_conditions)
    pointing_count = pointings.count()

    # Update the status
    for pointing in pointings:
        pointing.status = pointing_status_enum.cancelled
        pointing.dateupdated = datetime.now()

    db.commit()

    return {"message": f"Updated {pointing_count} Pointings successfully"}


@router.post("/request_doi", response_model=DOIRequestResponse)
async def request_doi(
        request: DOIRequest,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Request a DOI for completed pointings.
    """
    # Build the filter for pointings
    filter_conditions = [
        Pointing.submitterid == user.id
    ]

    # Handle id or ids (these don't require PointingEvent join)
    if request.id:
        filter_conditions.append(Pointing.id == request.id)
    elif request.ids:
        filter_conditions.append(Pointing.id.in_(request.ids))

    # Only join with PointingEvent if graceid is specified
    if request.graceid:
        normalized_graceid = GWAlert.graceidfromalternate(request.graceid)
        # Query the pointings with explicit join
        points = db.query(Pointing).join(
            PointingEvent, Pointing.id == PointingEvent.pointingid
        ).filter(
            *filter_conditions,
            PointingEvent.graceid == normalized_graceid
        ).all()
    else:
        # Query without join when only using ID filters
        points = db.query(Pointing).filter(*filter_conditions).all()

    # Validate and prepare for DOI request
    warnings = []
    doi_points = []

    for p in points:
        # Check if pointing is completed and doesn't already have a DOI
        if p.status == pointing_status_enum.completed and p.doi_id is None:
            doi_points.append(p)
        else:
            warning_msg = f"Invalid doi request for pointing: {p.id}"
            if p.status != pointing_status_enum.completed:
                warning_msg += f" (status: {p.status})"
            if p.doi_id is not None:
                warning_msg += " (already has DOI)"
            warnings.append(warning_msg)

    if len(doi_points) == 0:
        raise validation_exception(
            message="No valid pointings found for DOI request",
            errors=["All pointings must be completed and not already have a DOI"]
        )

    # Get the GW event IDs from the pointings
    pointing_events = db.query(PointingEvent).filter(
        PointingEvent.pointingid.in_([x.id for x in doi_points])
    ).all()
    gids = list(set([pe.graceid for pe in pointing_events]))

    if len(gids) > 1:
        raise validation_exception(
            message="Multiple events detected",
            errors=["Pointings must be only for a single GW event for a DOI request"]
        )

    gid = gids[0]

    # Prepare DOI creators
    creators = PointingService.prepare_doi_creators(
        request.creators, request.doi_group_id, user, db
    )

    # Create or use provided DOI
    if request.doi_url:
        doi_id, doi_url = 0, request.doi_url
    else:
        doi_id, doi_url = PointingService.create_doi_for_pointings(
            doi_points, gid, creators, db
        )

    # Update pointing records with DOI information
    if doi_id is not None:
        for p in doi_points:
            p.doi_url = doi_url
            p.doi_id = doi_id

        db.commit()

    return DOIRequestResponse(DOI_URL=doi_url, WARNINGS=warnings)


@router.get("/test_refactoring")
async def test_refactoring():
    """Test endpoint to verify refactored code is active."""
    return {"message": "Refactored pointing routes are active"}
