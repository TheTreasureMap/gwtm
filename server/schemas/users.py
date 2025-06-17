from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Dict, Any
from datetime import datetime

class UserSchema(BaseModel):
    """Schema for returning a user."""
    id: int = Field(..., description="Unique identifier for the user")
    username: str = Field(..., description="Username of the user")
    firstname: Optional[str] = Field(None, description="First name of the user")
    lastname: Optional[str] = Field(None, description="Last name of the user")
    email: Optional[str] = Field(None, description="Email address of the user")
    datecreated: Optional[datetime] = Field(None, description="Date when the user account was created")

    model_config = ConfigDict(from_attributes=True)

class UserGroupSchema(BaseModel):
    """Schema for returning a user group association."""
    id: int = Field(..., description="Unique identifier for the user group association")
    userid: int = Field(..., description="ID of the user")
    groupid: int = Field(..., description="ID of the group")
    role: Optional[str] = Field(None, description="Role of the user within the group")

    model_config = ConfigDict(from_attributes=True)

class GroupSchema(BaseModel):
    """Schema for returning a group."""
    id: int = Field(..., description="Unique identifier for the group")
    name: str = Field(..., description="Name of the group")
    datecreated: Optional[datetime] = Field(None, description="Date when the group was created")

    model_config = ConfigDict(from_attributes=True)

class UserActionSchema(BaseModel):
    """Schema for returning a user action log entry."""
    id: int = Field(..., description="Unique identifier for the user action")
    userid: int = Field(..., description="ID of the user who performed the action")
    ipaddress: Optional[str] = Field(None, description="IP address from which the action was performed")
    url: Optional[str] = Field(None, description="URL that was accessed")
    time: Optional[datetime] = Field(None, description="Time when the action was performed")
    jsonvals: Optional[Dict[str, Any]] = Field(None, description="Additional JSON data for the action")
    method: Optional[str] = Field(None, description="HTTP method used for the action")

    model_config = ConfigDict(from_attributes=True)