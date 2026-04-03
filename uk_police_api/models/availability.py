"""Data availability models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityDate(BaseModel):
    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    date: str
    stop_and_search: list[str] = Field(default=[], alias="stop-and-search")
