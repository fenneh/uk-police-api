"""Shared model types used across multiple API resources."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


class Street(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    name: str


class Location(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float | None = None
    longitude: float | None = None
    street: Street | None = None

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def coerce_float(cls, v: object) -> float | None:
        if v is None or v == "":
            return None
        return float(str(v))


class Coordinates(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float
    longitude: float

    @field_validator("latitude", "longitude", mode="before")
    @classmethod
    def coerce_float(cls, v: object) -> float:
        return float(str(v))


class EngagementMethod(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str | None = None
    description: str | None = None
    title: str
