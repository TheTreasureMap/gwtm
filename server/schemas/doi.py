# server/schemas/doi.py

from pydantic import BaseModel, ConfigDict, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class DOIAuthorBase(BaseModel):
    """Base schema for DOI author data."""

    name: str
    affiliation: str
    orcid: Optional[str] = None
    gnd: Optional[str] = None
    pos_order: Optional[int] = None


class DOIAuthorCreate(DOIAuthorBase):
    """Schema for creating a new DOI author."""

    author_groupid: int


class DOIAuthorSchema(DOIAuthorBase):
    """Schema for returning a DOI author."""

    id: int
    author_groupid: int

    model_config = ConfigDict(from_attributes=True)


class DOIAuthorGroupBase(BaseModel):
    """Base schema for DOI author group data."""

    name: str
    userid: Optional[int] = None


class DOIAuthorGroupCreate(DOIAuthorGroupBase):
    """Schema for creating a new DOI author group."""

    pass


class DOIAuthorGroupSchema(DOIAuthorGroupBase):
    """Schema for returning a DOI author group."""

    id: int

    model_config = ConfigDict(from_attributes=True)


class DOICreator(BaseModel):
    """Schema for a DOI creator."""

    name: str
    affiliation: str
    orcid: Optional[str] = None
    gnd: Optional[str] = None


class DOIPointingInfo(BaseModel):
    """Schema for DOI pointing information."""

    id: int
    graceid: str
    instrument_name: str
    status: str
    doi_url: Optional[str] = None
    doi_id: Optional[int] = None


class DOIPointingsResponse(BaseModel):
    """Schema for DOI pointings response."""

    pointings: List[DOIPointingInfo]


class DOIRequestResponse(BaseModel):
    """Schema for DOI request response."""

    DOI_URL: Optional[str] = None
    WARNINGS: List[Any] = []


class DOIMetadata(BaseModel):
    """Schema for DOI metadata."""

    doi: str
    creators: List[DOICreator]
    titles: List[Dict[str, str]]
    publisher: str
    publicationYear: str
    resourceType: Dict[str, str]
    descriptions: List[Dict[str, str]]
    relatedIdentifiers: Optional[List[Dict[str, str]]] = None


class DOICreate(BaseModel):
    """Schema for creating a new DOI."""

    points: List[int]
    graceid: str
    creators: List[DOICreator]
    reference: Optional[str] = None
