# server/routes/pointing.py
from fastapi import APIRouter, Depends, Query, Body, HTTPException
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
    PointingUpdate
)
from server.auth.auth import get_current_user
from server.utils.function import pointing_crossmatch, create_pointing_doi
from server.core.enums.pointing_status import pointing_status as pointing_status_enum
from server.core.enums.depth_unit import depth_unit as depth_unit_enum
from server.core.enums.bandpass import bandpass as bandpass_enum


router = APIRouter(tags=["pointings"])


@router.post("/pointings", response_model=PointingResponse)
async def add_pointings(
        graceid: str = Body(..., description="Grace ID of the GW event"),
        pointing: Optional[Dict[str, Any]] = Body(None, description="Single pointing object"),
        pointings: Optional[List[Dict[str, Any]]] = Body(None, description="List of pointing objects"),
        request_doi: Optional[bool] = Body(False, description="Whether to request a DOI"),
        creators: Optional[List[Dict[str, str]]] = Body(None, description="List of creators for the DOI"),
        doi_group_id: Optional[str] = Body(None, description="DOI author group ID"),
        doi_url: Optional[str] = Body(None, description="Optional DOI URL if already exists"),
        db: Session = Depends(get_db),
        user=Depends(get_current_user)
):
    """
    Add new pointings to the database.

    Parameters:
    - graceid: Grace ID of the GW event
    - pointing: Single pointing object
    - pointings: List of pointing objects
    - request_doi: Whether to request a DOI
    - creators: List of creators for the DOI
    - doi_group_id: DOI author group ID
    - doi_url: Optional DOI URL if already exists

    Returns pointing IDs, errors, and warnings
    """
    # Initialize variables
    points = []
    errors = []
    warnings = []
    post_doi = request_doi

    # Validate graceid
    # First check if the graceid exists
    valid_alerts = db.query(GWAlert).filter(GWAlert.graceid == graceid).all()
    if len(valid_alerts) == 0:
        raise validation_exception(
            message="Invalid graceid",
            errors=[f"The graceid '{graceid}' does not exist in the database"]
        )

    # Handle DOI creators
    if post_doi:
        if creators:
            for c in creators:
                if 'name' not in c or 'affiliation' not in c:
                    raise validation_exception(
                        message="Invalid DOI creator information",
                        errors=["name and affiliation are required for each creator in the list"]
                    )
        elif doi_group_id:
            # Import here to avoid circular imports
            from server.db.models.doi_author import DOIAuthor
            valid, creators_list = DOIAuthor.construct_creators(doi_group_id, user.id, db)
            if not valid:
                raise validation_exception(
                    message="Invalid DOI group ID",
                    errors=["Make sure you are the User associated with the DOI group"]
                )
            creators = creators_list
        else:
            creators = [{'name': f"{user.firstname} {user.lastname}", 'affiliation': ''}]

    # Get instrument list
    dbinsts = db.query(Instrument.instrument_name, Instrument.id).all()

    # Get other pointings for this event to check for duplicates
    otherpointings = db.query(Pointing).filter(
        Pointing.id == PointingEvent.pointingid,
        PointingEvent.graceid == graceid
    ).all()

    # Process a single pointing
    if pointing:
        # Handle pointing validation
        validation_result = validate_pointing(pointing, dbinsts, user.id, db, otherpointings)

        if validation_result.valid:
            points.append(validation_result.pointing)
            if validation_result.warnings:
                warnings.append(["Object: " + str(pointing), validation_result.warnings])
            db.add(validation_result.pointing)
        else:
            errors.append(["Errors validating pointing: ", validation_result.errors])

    # Process multiple pointings
    elif pointings:
        for p in pointings:
            validation_result = validate_pointing(p, dbinsts, user.id, db, otherpointings)

            if validation_result.valid:
                points.append(validation_result.pointing)
                if validation_result.warnings:
                    warnings.append(["Object: " + str(p), validation_result.warnings])
                db.add(validation_result.pointing)
            else:
                errors.append(["Object: " + str(p), validation_result.errors])

    else:
        raise HTTPException(
            status_code=500,
            detail="Invalid request: json pointing or json list of pointings are required"
        )

    # Flush to get pointing IDs
    db.flush()

    # Create pointing events
    for p in points:
        pointing_event = PointingEvent(
            pointingid=p.id,
            graceid=graceid
        )
        db.add(pointing_event)

    db.flush()
    db.commit()

    # Handle DOI creation if requested
    if post_doi and points:
        insts = db.query(Instrument).filter(
            Instrument.id.in_([p.instrumentid for p in points])
        )
        inst_set = list(set([i.instrument_name for i in insts]))

        if doi_url:
            doi_id, doi_url = 0, doi_url
        else:
            normalized_gid = GWAlert.alternatefromgraceid(graceid)
            doi_id, doi_url = create_pointing_doi(points, normalized_gid, creators, inst_set)

        if doi_id is not None:
            for p in points:
                p.doi_url = doi_url
                p.doi_id = doi_id

            db.flush()
            db.commit()

            return PointingResponse(
                pointing_ids=[p.id for p in points],
                ERRORS=errors,
                WARNINGS=warnings,
                DOI=doi_url
            )

    # Return response without DOI
    return PointingResponse(
        pointing_ids=[p.id for p in points],
        ERRORS=errors,
        WARNINGS=warnings
    )


class ValidationResult:
    """Helper class for validation results."""

    def __init__(self):
        self.valid = False
        self.pointing = None
        self.errors = []
        self.warnings = []


def validate_pointing(data, dbinsts, user_id, db, otherpointings):
    """
    Validate pointing data.
    This is a helper function to separate validation logic from model methods.
    """
    # Create validation result
    result = ValidationResult()

    # Create a new pointing
    pointing = Pointing()

    # Check for planned pointing (update case)
    PLANNED = False
    if 'id' in data and data['id'] is not None and isinstance(data['id'], int):
        PLANNED = True
        pointing_id = int(data['id'])

        # Find the planned pointing
        planned_pointing = db.query(Pointing).filter(
            Pointing.id == pointing_id,
            Pointing.submitterid == user_id
        ).first()

        if not planned_pointing:
            result.errors.append(f"Pointing with ID {pointing_id} not found or not owned by you")
            return result

        if planned_pointing.status in [pointing_status_enum.completed, pointing_status_enum.cancelled]:
            result.errors.append(f"This pointing has already been {planned_pointing.status.name}")
            return result

        # Copy data from planned pointing
        pointing.position = planned_pointing.position
        pointing.depth = planned_pointing.depth
        pointing.depth_err = planned_pointing.depth_err
        pointing.depth_unit = planned_pointing.depth_unit
        pointing.status = pointing_status_enum.completed  # Set to completed
        pointing.band = planned_pointing.band
        pointing.central_wave = planned_pointing.central_wave
        pointing.bandwidth = planned_pointing.bandwidth
        pointing.instrumentid = planned_pointing.instrumentid
        pointing.pos_angle = planned_pointing.pos_angle

        # Update fields if provided
        if 'time' in data and data['time']:
            pointing.time = data['time']
        else:
            pointing.time = planned_pointing.time

        if 'pos_angle' in data and data['pos_angle'] is not None:
            pointing.pos_angle = data['pos_angle']

        pointing.submitterid = user_id
        pointing.datecreated = datetime.now()
        pointing.dateupdated = datetime.now()

        # Mark as valid
        result.valid = True
        result.pointing = pointing
        return result

    # Validate status
    if 'status' in data and data['status']:
        status_value = data['status']
        if isinstance(status_value, str):
            try:
                status_value = pointing_status_enum[status_value]  # Convert string to enum
            except KeyError:
                result.errors.append("Invalid status value")
                return result
        if status_value in [pointing_status_enum.planned, pointing_status_enum.completed, pointing_status_enum.cancelled]:
            pointing.status = status_value
        else:
            result.errors.append("Invalid status value")
            return result
    else:
        pointing.status = pointing_status_enum.completed

    # Validate position (ra/dec)
    if 'position' in data and data['position']:
        pos = data['position']
        if pos and all(x in pos for x in ["POINT", "(", ")", " "]) and "," not in pos:
            pointing.position = data['position']
        else:
            result.errors.append(
                "Invalid position argument. Must be decimal format ra/RA, dec/DEC, or geometry type \"POINT(RA DEC)\"")
            return result
    elif 'ra' in data and 'dec' in data and data['ra'] is not None and data['dec'] is not None:
        ra, dec = data['ra'], data['dec']

        if not isinstance(ra, (int, float)) or not isinstance(dec, (int, float)):
            result.errors.append(
                "Invalid position argument. Must be decimal format ra/RA, dec/DEC, or geometry type \"POINT(RA DEC)\"")
            return result
        else:
            pointing.position = f"POINT({ra} {dec})"
    else:
        result.errors.append("Position information required (either position string or ra/dec coordinates)")
        return result

    # Validate instrument
    if 'instrumentid' in data and data['instrumentid']:
        inst = data['instrumentid']
        valid_inst = False

        if isinstance(inst, int):
            insts = [x for x in dbinsts if x.id == int(inst)]
            if insts:
                pointing.instrumentid = inst
                valid_inst = True
        else:
            insts = [x for x in dbinsts if x.instrument_name == inst]
            if insts:
                pointing.instrumentid = insts[0].id
                valid_inst = True

        if not valid_inst:
            result.errors.append("Invalid instrumentid. Can be id or name of instrument")
            return result
    else:
        result.errors.append("Field instrumentid is required")
        return result

    # Validate depth
    if 'depth' in data and data['depth'] is not None:
        if isinstance(data['depth'], (int, float)):
            pointing.depth = float(data['depth'])
        else:
            result.errors.append("Invalid depth. Must be decimal")
            return result
    elif pointing.status == pointing_status_enum.completed:
        result.errors.append("depth is required for completed observations")
        return result

    # Validate depth unit
    if 'depth_unit' in data and data['depth_unit']:
        unit_value = data['depth_unit']
        if isinstance(unit_value, str):
            try:
                unit_value = depth_unit_enum[unit_value]  # Convert string to enum
            except KeyError:
                result.errors.append(f"Invalid depth_unit value: {unit_value}")
                return result
        pointing.depth_unit = unit_value
    elif pointing.status == pointing_status_enum.completed:
        result.errors.append("depth_unit is required for completed observations")
        return result

    # Validate depth error
    if 'depth_err' in data and data['depth_err'] is not None:
        if isinstance(data['depth_err'], (int, float)):
            pointing.depth_err = float(data['depth_err'])
        else:
            result.errors.append("Invalid depth_err. Must be decimal")
            return result

    # Validate position angle
    if 'pos_angle' in data and data['pos_angle'] is not None:
        if isinstance(data['pos_angle'], (int, float)):
            pointing.pos_angle = float(data['pos_angle'])
        else:
            result.errors.append("Invalid pos_angle. Must be decimal")
            return result
    elif pointing.status == pointing_status_enum.completed and pointing.pos_angle is None:
        result.errors.append("pos_angle is required for completed observations")
        return result

    # Validate time
    if 'time' in data and data['time']:
        pointing.time = data['time']
    elif pointing.status == pointing_status_enum.planned:
        result.errors.append("Field \"time\" is required for when the pointing is planned to be observed")
        return result
    elif pointing.status == pointing_status_enum.completed:
        result.errors.append('Field \"time\" is required for the observed pointing')
        return result

    # Validate band/spectral information
    if 'band' in data and data['band']:
        band_value = data['band']
        if isinstance(band_value, str):
            try:
                band_value = bandpass_enum[band_value]  # Convert string to enum
            except KeyError:
                result.errors.append(f"Invalid band value: {band_value}")
                return result
        pointing.band = band_value
    elif pointing.status == pointing_status_enum.completed:
        result.errors.append("band is required for completed observations")
        return result

    # Set basic fields
    pointing.submitterid = user_id
    pointing.datecreated = datetime.now()

    # Set central_wave and bandwidth if provided
    if 'central_wave' in data and data['central_wave'] is not None:
        pointing.central_wave = data['central_wave']
    if 'bandwidth' in data and data['bandwidth'] is not None:
        pointing.bandwidth = data['bandwidth']

    # Check for duplicate pointing
    if pointing_crossmatch(pointing, otherpointings):
        result.errors.append("Pointing already submitted")
        return result

    # Set validation result
    result.valid = True
    result.pointing = pointing
    return result


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
            graceid: str = Body(..., description="Grace ID of the GW event"),
            instrumentid: int = Body(..., description="Instrument ID to cancel pointings for"),
            db: Session = Depends(get_db),
            user=Depends(get_current_user)
    ):
        """
        Cancel all planned pointings for a specific GW event and instrument.

        Parameters:
        - graceid: Grace ID of the GW event
        - instrumentid: Instrument ID to cancel pointings for

        Returns:
        - Message with the number of cancelled pointings
        """
        # Validate instrumentid
        instrument = db.query(Instrument).filter(Instrument.id == instrumentid).first()
        if not instrument:
            raise not_found_exception(f"Instrument with ID {instrumentid} not found")

        # Build the filter
        filter_conditions = [
            Pointing.status == pointing_status_enum.planned,
            Pointing.submitterid == user.id,
            Pointing.instrumentid == instrumentid
        ]

        # Add GW event filter using pointing_event relation
        if graceid:
            # Normalize the graceid
            graceid = GWAlert.graceidfromalternate(graceid)
            # Add the join condition
            filter_conditions.append(Pointing.id == PointingEvent.pointingid)
            filter_conditions.append(PointingEvent.graceid == graceid)

        # Query the pointings
        pointings = db.query(Pointing).filter(*filter_conditions)
        pointing_count = pointings.count()

        # Update the status
        for pointing in pointings:
            pointing.status = pointing_status_enum.cancelled
            pointing.dateupdated = datetime.now()

        db.commit()

        return {"message": f"Updated {pointing_count} Pointings successfully"}

    @router.post("/request_doi")
    async def request_doi(
            graceid: Optional[str] = Body(None, description="Grace ID of the GW event"),
            id: Optional[int] = Body(None, description="Pointing ID"),
            ids: Optional[List[int]] = Body(None, description="List of pointing IDs"),
            doi_group_id: Optional[int] = Body(None, description="DOI author group ID"),
            creators: Optional[List[Dict[str, str]]] = Body(None, description="List of creators for the DOI"),
            doi_url: Optional[str] = Body(None, description="Optional DOI URL if already exists"),
            db: Session = Depends(get_db),
            user=Depends(get_current_user)
    ):
        """
        Request a DOI for completed pointings.

        Parameters:
        - graceid: Grace ID of the GW event
        - id: Single pointing ID
        - ids: List of pointing IDs
        - doi_group_id: DOI author group ID
        - creators: List of creators for the DOI
        - doi_url: Optional DOI URL if already exists

        Returns:
        - DOI URL and warnings
        """
        # Build the filter for pointings
        filter_conditions = [Pointing.submitterid == user.id]

        # Handle graceid
        if graceid:
            # Normalize the graceid
            graceid = GWAlert.graceidfromalternate(graceid)
            # Add the join condition
            filter_conditions.append(Pointing.id == PointingEvent.pointingid)
            filter_conditions.append(PointingEvent.graceid == graceid)

        # Handle id or ids
        if id:
            filter_conditions.append(Pointing.id == id)
        elif ids:
            filter_conditions.append(Pointing.id.in_(ids))

        if len(filter_conditions) == 1:  # Only the user filter
            raise validation_exception(
                message="Insufficient filter parameters",
                errors=["Please provide either graceid, id, or ids parameter"]
            )

        # Query the pointings
        points = db.query(Pointing).filter(*filter_conditions).all()

        # Validate and prepare for DOI request
        warnings = []
        doi_points = []

        for p in points:
            if p.status == pointing_status_enum.completed and p.submitterid == user.id and p.doi_id is None:
                doi_points.append(p)
            else:
                warnings.append(f"Invalid doi request for pointing: {p.id}")

        if len(doi_points) == 0:
            raise validation_exception(
                message="No valid pointings found for DOI request",
                errors=["All pointings must be completed, owned by you, and not already have a DOI"]
            )

        # Get the instruments
        insts = db.query(Instrument).filter(Instrument.id.in_([x.instrumentid for x in doi_points]))
        inst_set = list(set([x.instrument_name for x in insts]))

        # Get the GW event IDs
        gids = list(set([x.graceid for x in db.query(PointingEvent).filter(
            PointingEvent.pointingid.in_([x.id for x in doi_points])
        )]))

        if len(gids) > 1:
            raise validation_exception(
                message="Multiple events detected",
                errors=["Pointings must be only for a single GW event for a DOI request"]
            )

        gid = gids[0]

        # Handle DOI creators
        if not creators:
            if doi_group_id:
                # Using the construct_creators function from the DOIAuthor model
                from server.db.models.doi_author import DOIAuthor
                valid, creators = DOIAuthor.construct_creators(doi_group_id, user.id, db)
                if not valid:
                    raise validation_exception(
                        message="Invalid DOI group ID",
                        errors=["Make sure you are the User associated with the DOI group"]
                    )
            else:
                # Default to user as creator
                creators = [{"name": f"{user.firstname} {user.lastname}", "affiliation": ""}]
        else:
            # Validate creators
            for c in creators:
                if "name" not in c or "affiliation" not in c:
                    raise validation_exception(
                        message="Invalid DOI creator information",
                        errors=["name and affiliation are required for each creator in the list"]
                    )

        # Create or use provided DOI
        if doi_url:
            doi_id, doi_url = 0, doi_url
        else:
            # Get the alternate form of the graceid
            gid = GWAlert.alternatefromgraceid(gid)
            # Create the DOI
            doi_id, doi_url = create_pointing_doi(doi_points, gid, creators, inst_set)

        # Update pointing records with DOI information
        if doi_id is not None:
            for p in doi_points:
                p.doi_url = doi_url
                p.doi_id = doi_id

            db.commit()

        return {"DOI_URL": doi_url, "WARNINGS": warnings}

