"""Stop and search data models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .common import Location


class StopSearch(BaseModel):
    model_config = ConfigDict(extra="ignore")

    type: str
    involved_person: bool | None = None
    datetime: str
    operation: bool | None = None
    operation_name: str | None = None
    location: Location | None = None
    gender: str | None = None
    age_range: str | None = None
    self_defined_ethnicity: str | None = None
    officer_defined_ethnicity: str | None = None
    legislation: str | None = None
    object_of_search: str | None = None
    outcome: str | None = None
    outcome_linked_to_object_of_search: bool | None = None
    removal_of_more_than_outer_clothing: bool | None = None
