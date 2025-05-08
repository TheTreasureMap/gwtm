from pydantic import BaseModel, Field
from typing import Optional

class Glade2P3Schema(BaseModel):
    pgc_number: int = Field(..., description="PGC number of the galaxy")
    distance: float = Field(..., description="Distance of the galaxy")
    position: Optional[dict] = Field(None, description="Geographical position as a dictionary with 'latitude' and 'longitude'")
    _2mass_name: Optional[str] = Field(None, description="2MASS name of the galaxy")
    gwgc_name: Optional[str] = Field(None, description="GWGC name of the galaxy")
    hyperleda_name: Optional[str] = Field(None, description="HyperLEDA name of the galaxy")
    sdssdr12_name: Optional[str] = Field(None, description="SDSS DR12 name of the galaxy")

    model_config = ConfigDict(from_attributes=True)
