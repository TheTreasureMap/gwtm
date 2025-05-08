from fastapi import APIRouter, HTTPException, Depends, Query, Body
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
from dateutil.parser import parse as date_parse
import shapely.wkb
import json

from server.db.database import get_db
from server.db.models.gw_alert import GWAlert
from server.db.models.candidate import GWCandidate
from server.schemas.candidate import CandidateSchema, GetCandidateQueryParams
from server.auth.auth import get_current_user

router = APIRouter(tags=["candidates"])

@router.get("/candidate", response_model=List[CandidateSchema])
async def get_candidates(
    query_params: GetCandidateQueryParams = Depends(),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Get candidates with optional filters.
    """
    filter_conditions = []
    
    if query_params.id:
        filter_conditions.append(GWCandidate.id == query_params.id)
    
    if query_params.ids:
        try:
            ids_list = None
            if isinstance(query_params.ids, str):
                ids_list = query_params.ids.split('[')[1].split(']')[0].split(',')
            elif isinstance(query_params.ids, list):
                ids_list = query_params.ids
            if ids_list:
                filter_conditions.append(GWCandidate.id.in_(ids_list))
        except:
            pass
    
    if query_params.graceid:
        graceid = GWAlert.graceidfromalternate(query_params.graceid)
        filter_conditions.append(GWCandidate.graceid == graceid)
    
    if query_params.userid:
        filter_conditions.append(GWCandidate.submitterid == query_params.userid)
    
    if query_params.submitted_date_after:
        try:
            parsed_date_after = date_parse(query_params.submitted_date_after)
            filter_conditions.append(GWCandidate.datecreated >= parsed_date_after)
        except:
            pass
    
    if query_params.submitted_date_before:
        try:
            parsed_date_before = date_parse(query_params.submitted_date_before)
            filter_conditions.append(GWCandidate.datecreated <= parsed_date_before)
        except:
            pass
    
    if query_params.discovery_magnitude_gt is not None:
        filter_conditions.append(GWCandidate.discovery_magnitude >= query_params.discovery_magnitude_gt)
    
    if query_params.discovery_magnitude_lt is not None:
        filter_conditions.append(GWCandidate.discovery_magnitude <= query_params.discovery_magnitude_lt)
    
    if query_params.discovery_date_after:
        try:
            parsed_date_after = date_parse(query_params.discovery_date_after)
            filter_conditions.append(GWCandidate.discovery_date >= parsed_date_after)
        except:
            pass
    
    if query_params.discovery_date_before:
        try:
            parsed_date_before = date_parse(query_params.discovery_date_before)
            filter_conditions.append(GWCandidate.discovery_date <= parsed_date_before)
        except:
            pass
    
    if query_params.associated_galaxy_name:
        filter_conditions.append(GWCandidate.associated_galaxy.contains(query_params.associated_galaxy_name))
    
    if query_params.associated_galaxy_redshift_gt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_redshift >= query_params.associated_galaxy_redshift_gt)
    
    if query_params.associated_galaxy_redshift_lt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_redshift <= query_params.associated_galaxy_redshift_lt)
    
    if query_params.associated_galaxy_distance_gt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_distance >= query_params.associated_galaxy_distance_gt)
    
    if query_params.associated_galaxy_distance_lt is not None:
        filter_conditions.append(GWCandidate.associated_galaxy_distance <= query_params.associated_galaxy_distance_lt)
    
    candidates = db.query(GWCandidate).filter(*filter_conditions).all()

    for candidate in candidates:
        # Convert position from WKB to WKT
        if candidate.position:
            position = shapely.wkb.loads(bytes(candidate.position.data))
            candidate.position = str(position)

    return candidates

@router.post("/candidate", response_model=Dict[str, Any])
async def post_candidates(
    graceid: str = Body(...),
    candidate: Optional[Dict[str, Any]] = Body(None),
    candidates: Optional[List[Dict[str, Any]]] = Body(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Post new candidate(s) for a GW event.
    """
    # Validate graceid
    valid_alerts = db.query(GWAlert).filter(GWAlert.graceid == graceid).all()
    if len(valid_alerts) == 0:
        raise HTTPException(
            status_code=400, 
            detail="Invalid 'graceid'. Visit https://treasuremap.space/alert_select for valid alerts"
        )
    
    errors = []
    warnings = []
    valid_candidates = []
    
    if candidate:
        if not isinstance(candidate, dict):
            raise HTTPException(
                status_code=400,
                detail="Invalid 'candidate' format. Must be a dictionary or JSON object"
            )
        
        gwc = GWCandidate()
        validation_result = gwc.from_json(candidate, graceid, user.id)
        
        if validation_result.valid:
            valid_candidates.append(gwc)
            if len(validation_result.warnings) > 0:
                warnings.append(["Object: " + json.dumps(candidate), validation_result.warnings])
            db.add(gwc)
        else:
            errors.append(["Object: " + json.dumps(candidate), validation_result.errors])
    
    elif candidates:
        if not isinstance(candidates, list):
            raise HTTPException(
                status_code=400,
                detail="Invalid 'candidates' format. Must be a list of dictionaries or JSON objects"
            )
        
        for candidate_item in candidates:
            if not isinstance(candidate_item, dict):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid 'candidate' format. Must be a dictionary or JSON object"
                )
            
            gwc = GWCandidate()
            validation_result = gwc.from_json(candidate_item, graceid, user.id)
            
            if validation_result.valid:
                valid_candidates.append(gwc)
                if len(validation_result.warnings) > 0:
                    warnings.append(["Object: " + json.dumps(candidate_item), validation_result.warnings])
                db.add(gwc)
            else:
                errors.append(["Object: " + json.dumps(candidate_item), validation_result.errors])
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Error: Missing 'candidate' or 'candidates' information"
        )
    
    db.flush()
    db.commit()
    
    return {
        "candidate_ids": [x.id for x in valid_candidates],
        "ERRORS": errors,
        "WARNINGS": warnings
    }

@router.put("/candidate", response_model=Dict[str, Any])
async def update_candidates(
    id: int = Body(...),
    payload: Dict[str, Any] = Body(...),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Update an existing candidate.
    """
    # Find the candidate
    candidate = db.query(GWCandidate).filter(GWCandidate.id == id).first()
    
    if not candidate:
        raise HTTPException(
            status_code=404,
            detail=f"No candidate found with 'id': {id}"
        )
    
    # Check permissions
    if candidate.submitterid != user.id:
        raise HTTPException(
            status_code=403,
            detail="Error: Unauthorized. Unable to alter other user's records"
        )
    
    # Validate payload
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=400,
            detail=f"Put Candidate 'payload' is required to be object of type 'dict' or 'json'. Detected <{type(payload)}>"
        )
    
    # Define editable columns
    editable_columns = [
        "graceid", "candidate_name", "tns_name", "tns_url", "position", "ra", "dec", "discovery_date", 
        "discovery_magnitude", "magnitude_central_wave", "magnitude_bandwidth", "magnitude_bandwidth",
        "magnitude_bandpass", "associated_galaxy", "associated_galaxy_redshift", "associated_galaxy_distance",
        "wavelength_regime", "wavelength_unit", "frequency_regime", "frequency_unit",
        "energy_regime", "energy_unit"
    ]
    
    # Get current candidate data
    position = shapely.wkb.loads(bytes(candidate.position.data))
    candidate_dict = candidate.parse
    
    # Update candidate dict with payload
    candidate_dict.update(
        (str(key).lower(), value) for key, value in payload.items() if str(key).lower() in editable_columns
    )
    
    # Handle position update
    if any([x in payload.keys() for x in ["ra", "dec"]]):
        del candidate_dict["position"]
    elif "position" not in payload.keys():
        candidate_dict["position"] = str(position)
    
    # Validate the updated data
    errors = []
    gwc = GWCandidate()
    validation_result = gwc.from_json(candidate_dict, candidate_dict["graceid"], candidate.submitterid)
    
    if validation_result.valid:
        updated_model = gwc.__dict__
        for key, value in updated_model.items():
            if key in editable_columns:
                setattr(candidate, key, value)
        db.commit()
        return {"message": "success", "candidate": candidate}
    else:
        errors.append(validation_result.errors)
        return {"message": "failure", "errors": errors}

@router.delete("/candidate", response_model=Dict[str, Any])
async def delete_candidates(
    id: Optional[int] = Query(None),
    ids: Optional[List[int]] = Query(None),
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    """
    Delete candidate(s).
    """
    warnings = []
    candidates_to_delete = []
    
    # Handle single ID
    if id is not None:
        candidate = db.query(GWCandidate).filter(GWCandidate.id == id).first()
        if not candidate:
            raise HTTPException(
                status_code=404,
                detail=f"No candidate found with 'id': {id}"
            )
        
        if candidate.submitterid != user.id:
            raise HTTPException(
                status_code=403,
                detail="Error: Unauthorized. Unable to alter other user's records"
            )
        
        candidates_to_delete.append(candidate)
    
    # Handle multiple IDs
    elif ids is not None:
        query_ids = ids
        candidates = db.query(GWCandidate).filter(GWCandidate.id.in_(query_ids)).all()
        
        if len(candidates) == 0:
            raise HTTPException(
                status_code=404,
                detail="No candidates found with input 'ids'"
            )
        
        candidates_to_delete.extend([x for x in candidates if x.submitterid == user.id])
        if len(candidates_to_delete) < len(candidates):
            warnings.append("Some entries were not deleted. You cannot delete candidates you didn't submit")
    
    # Delete the candidates
    if len(candidates_to_delete):
        del_ids = []
        for ctd in candidates_to_delete:
            del_ids.append(ctd.id)
            db.delete(ctd)
        
        db.commit()
        
        return {
            "message": f"Successfully deleted {len(candidates_to_delete)} candidate(s)",
            "deleted_ids": del_ids,
            "warnings": warnings
        }
    else:
        return {
            "message": "No candidates found with input parameters",
            "warnings": warnings
        }
