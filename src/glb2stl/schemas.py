from typing import Literal

from pydantic import BaseModel, Field


class PreflightInfo(BaseModel):
    filename: str
    has_draco: bool
    vertices: int
    triangles: int
    bounds_m_min: list[float]
    bounds_m_max: list[float]
    watertight: bool
    notes: list[str] = []


class ConvertParams(BaseModel):
    z_up: bool = Field(default=True, description="Rotate Y-up → Z-up")
    to_mm: bool = Field(default=True, description="Scale meters → millimeters")
    repair: bool = Field(default=True, description="Light mesh repairs")
    decimate: float = Field(default=0.0, ge=0.0, le=0.99, description="Fraction to reduce faces")


class ErrorResponse(BaseModel):
    error: str


FormatLiteral = Literal["stl"]
