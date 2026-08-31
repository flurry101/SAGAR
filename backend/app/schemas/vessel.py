# attr: m1
# [vessel profile and management schemas]
from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field


class VesselProfile(BaseModel):
    # [vessel physical parameters and constraints]
    vessel_id: Optional[str] = Field(default=None, description="unique vessel identifier")
    vessel_type: str = Field(
        default="mechanized_trawler",
        description="type of fishing vessel e.g. mechanized_trawler, motorized_fibre_boat",
    )
    beam_width_m: float = Field(
        ...,
        gt=0.0,
        description="vessel beam width in meters (critical for svas safety formula)",
    )
    length_m: Optional[float] = Field(default=None, gt=0.0, description="overall length in meters")
    cruising_speed_kmh: float = Field(
        default=15.0,
        gt=0.0,
        description="cruising speed in km/h for eta calculations",
    )
    has_ais: bool = Field(default=False, description="ais transponder presence")


class VesselCreate(BaseModel):
    # [request schema to register a new vessel]
    vessel_type: str = Field(default="mechanized_trawler", description="vessel type")
    beam_width_m: float = Field(..., gt=0.0, description="beam width in meters")
    length_m: Optional[float] = Field(default=None, gt=0.0, description="length in meters")
    cruising_speed_kmh: float = Field(default=15.0, gt=0.0, description="cruising speed in km/h")
    has_ais: bool = Field(default=False, description="ais equipped flag")


class VesselUpdate(BaseModel):
    # [request schema to update an existing vessel profile]
    vessel_type: Optional[str] = Field(default=None, description="vessel type")
    beam_width_m: Optional[float] = Field(default=None, gt=0.0, description="beam width in meters")
    length_m: Optional[float] = Field(default=None, gt=0.0, description="length in meters")
    cruising_speed_kmh: Optional[float] = Field(default=None, gt=0.0, description="cruising speed in km/h")
    has_ais: Optional[bool] = Field(default=None, description="ais equipped flag")
# attr: m1

