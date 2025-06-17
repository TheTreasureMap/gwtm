"""
Pointing business logic services.
Contains logic that requires database access and can't be moved to Pydantic validators.
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Tuple, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from server.schemas.pointing import PointingCreate

from server.db.models.pointing import Pointing
from server.db.models.instrument import Instrument
from server.db.models.pointing_event import PointingEvent
from server.db.models.gw_alert import GWAlert
from server.db.models.users import Users
from server.db.models.doi_author import DOIAuthor
from server.core.enums.pointingstatus import PointingStatus as pointing_status_enum
from server.utils.error_handling import validation_exception, not_found_exception
from server.utils.function import pointing_crossmatch, create_pointing_doi


class PointingService:
    """Service class for pointing business logic."""
    
    @staticmethod
    def validate_graceid(graceid: str, db: Session) -> str:
        """Validate that a graceid exists in the database."""
        valid_alerts = db.query(GWAlert).filter(GWAlert.graceid == graceid).all()
        if len(valid_alerts) == 0:
            raise validation_exception(
                message="Invalid graceid",
                errors=[f"The graceid '{graceid}' does not exist in the database"]
            )
        return graceid
    
    @staticmethod
    def validate_instrument(instrument_id: int, db: Session) -> Instrument:
        """Validate that an instrument exists."""
        instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
        if not instrument:
            raise not_found_exception(f"Instrument with ID {instrument_id} not found")
        return instrument
    
    @staticmethod
    def get_instruments_dict(db: Session) -> dict:
        """Get a dictionary of instruments for validation."""
        dbinsts = db.query(Instrument.instrument_name, Instrument.id).all()
        return {inst.id: inst.instrument_name for inst in dbinsts}
    
    @staticmethod
    def validate_instrument_reference(pointing_data: 'PointingCreate', instruments_dict: dict) -> int:
        """Validate and resolve instrument reference to ID."""
        if pointing_data.instrumentid is None:
            raise validation_exception(
                message="Field instrumentid is required",
                errors=["instrumentid must be provided"]
            )
        
        inst = pointing_data.instrumentid
        if isinstance(inst, int):
            if inst not in instruments_dict:
                raise validation_exception(
                    message="Invalid instrumentid",
                    errors=[f"Instrument with ID {inst} not found"]
                )
            return inst
        else:
            # Handle string instrument names
            for inst_id, inst_name in instruments_dict.items():
                if inst_name == inst:
                    return inst_id
            raise validation_exception(
                message="Invalid instrumentid",
                errors=[f"Instrument '{inst}' not found"]
            )
    
    @staticmethod
    def check_duplicate_pointing(pointing: Pointing, existing_pointings: List[Pointing]) -> bool:
        """Check if a pointing is a duplicate of existing pointings."""
        return pointing_crossmatch(pointing, existing_pointings)
    
    @staticmethod
    def create_pointing_from_schema(pointing_data: 'PointingCreate', user_id: int, instrument_id: int) -> Pointing:
        """Create a Pointing model instance from schema data."""
        pointing = Pointing()
        
        # Set basic fields
        pointing.position = pointing_data.position
        pointing.depth = pointing_data.depth
        pointing.depth_err = pointing_data.depth_err
        pointing.depth_unit = pointing_data.depth_unit
        pointing.status = pointing_data.status or pointing_status_enum.completed
        pointing.band = pointing_data.band
        pointing.central_wave = pointing_data.central_wave
        pointing.bandwidth = pointing_data.bandwidth
        pointing.instrumentid = instrument_id
        pointing.pos_angle = pointing_data.pos_angle
        pointing.time = pointing_data.time
        pointing.submitterid = user_id
        pointing.datecreated = datetime.now()
        
        return pointing
    
    @staticmethod
    def handle_planned_pointing_update(pointing_data, user_id: int, db: Session) -> Optional[Pointing]:
        """Handle updating a planned pointing to completed."""
        if not hasattr(pointing_data, 'id') or pointing_data.id is None:
            return None
            
        pointing_id = int(pointing_data.id)
        
        # Find the planned pointing
        planned_pointing = db.query(Pointing).filter(
            Pointing.id == pointing_id,
            Pointing.submitterid == user_id
        ).first()
        
        if not planned_pointing:
            raise validation_exception(
                message="Pointing validation error",
                errors=[f"Pointing with ID {pointing_id} not found or not owned by you"]
            )
        
        if planned_pointing.status in [pointing_status_enum.completed, pointing_status_enum.cancelled]:
            raise validation_exception(
                message="Pointing validation error",
                errors=[f"This pointing has already been {planned_pointing.status.name}"]
            )
        
        # Update planned pointing with new data
        if pointing_data.time:
            planned_pointing.time = pointing_data.time
        if pointing_data.pos_angle is not None:
            planned_pointing.pos_angle = pointing_data.pos_angle
        
        planned_pointing.status = pointing_status_enum.completed
        planned_pointing.dateupdated = datetime.now()
        
        return planned_pointing
    
    @staticmethod
    def prepare_doi_creators(creators: Optional[List[dict]], doi_group_id: Optional[int], user: Users, db: Session) -> List[dict]:
        """Prepare DOI creators list."""
        if creators:
            return creators
        elif doi_group_id:
            valid, creators_list = DOIAuthor.construct_creators(doi_group_id, user.id, db)
            if not valid:
                raise validation_exception(
                    message="Invalid DOI group ID",
                    errors=["Make sure you are the User associated with the DOI group"]
                )
            return creators_list
        else:
            return [{'name': f"{user.firstname} {user.lastname}", 'affiliation': ''}]
    
    @staticmethod
    def create_doi_for_pointings(pointings: List[Pointing], graceid: str, creators: List[dict], db: Session) -> Tuple[Optional[int], Optional[str]]:
        """Create a DOI for a list of pointings."""
        if not pointings:
            return None, None
            
        # Get instruments for the pointings
        insts = db.query(Instrument).filter(
            Instrument.id.in_([p.instrumentid for p in pointings])
        ).all()
        inst_set = list(set([i.instrument_name for i in insts]))
        
        # Get normalized graceid
        normalized_gid = GWAlert.alternatefromgraceid(graceid)
        
        # Create the DOI
        result = create_pointing_doi(pointings, normalized_gid, creators, inst_set)
        return result
