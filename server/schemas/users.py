from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
from datetime import datetime

class UserSchema(BaseModel):
    id: int
    username: str
    firstname: Optional[str] = None
    lastname: Optional[str] = None
    email: Optional[str] = None
    datecreated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserGroupSchema(BaseModel):
    id: int
    userid: int
    groupid: int
    role: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)

class GroupSchema(BaseModel):
    id: int
    name: str
    datecreated: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserActionSchema(BaseModel):
    id: int
    userid: int
    ipaddress: Optional[str] = None
    url: Optional[str] = None
    time: Optional[datetime] = None
    jsonvals: Optional[Dict[str, Any]] = None
    method: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)