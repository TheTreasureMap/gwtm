from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime

from server.db.database import get_db
from server.db.models.icecube import IceCubeNotice, IceCubeNoticeCoincEvent
from server.schemas.icecube import (
    IceCubeNoticeSchema, 
    IceCubeNoticeCoincEventSchema,
    IceCubeNoticeRequestSchema
)
from server.auth.auth import get_current_user, verify_admin

router = APIRouter(tags=["icecube"])

@router.post("/post_icecube_notice", response_model=Dict[str, Any])
async def post_icecube_notice(
    request: IceCubeNoticeRequestSchema,
    db: Session = Depends(get_db),
    user = Depends(verify_admin)  # Only admin can post IceCube notices
):
    """
    Post an IceCube neutrino notice (admin only).
    
    Parameters:
    - request: IceCube notice request containing notice_data and events_data
    
    Returns the created notice and events
    """
    # Extract data from request
    notice_data = request.notice_data
    events_data = request.events_data
    
    # Check if notice already exists
    existing_notice = db.query(IceCubeNotice).filter(IceCubeNotice.ref_id == notice_data.ref_id).first()
    
    if existing_notice:
        return {
            "icecube_notice": {"message": "event already exists"},
            "icecube_notice_events": []
        }
    
    # Set required fields that might not be in the input data
    notice_dict = notice_data.model_dump()
    notice_dict["datecreated"] = datetime.now()
    
    # Create the notice object
    notice = IceCubeNotice(**notice_dict)
    db.add(notice)
    db.flush()  # Flush to get the generated ID
    
    # Process events
    events = []
    for event_data in events_data:
        # Get the event data
        event_dict = event_data.model_dump()
        
        # Set the notice ID and creation date
        event_dict["icecube_notice_id"] = notice.id
        event_dict["datecreated"] = datetime.now()
        
        # Create the event object
        event = IceCubeNoticeCoincEvent(**event_dict)
        db.add(event)
        events.append(event)
    
    db.commit()
    
    # Convert SQLAlchemy models to Pydantic schemas for serialization
    notice_schema = IceCubeNoticeSchema.model_validate(notice)
    events_schemas = [IceCubeNoticeCoincEventSchema.model_validate(event) for event in events]
    
    return {
        "icecube_notice": notice_schema,
        "icecube_notice_events": events_schemas
    }
