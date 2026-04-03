"""Crime-related data models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .common import Location


class OutcomeStatus(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: str
    date: str


class Crime(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: str
    persistent_id: str
    id: int
    month: str
    location_type: str | None = None
    location: Location | None = None
    context: str = ""
    outcome_status: OutcomeStatus | None = None


class CrimeCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    url: str
    name: str


class CrimeLastUpdated(BaseModel):
    model_config = ConfigDict(extra="ignore")

    date: str


class OutcomeCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    code: str
    name: str


class CrimeOutcome(BaseModel):
    model_config = ConfigDict(extra="ignore")

    category: OutcomeCategory
    date: str
    person_id: int | None = None


class CrimeWithOutcomes(BaseModel):
    model_config = ConfigDict(extra="ignore")

    crime: Crime
    outcomes: list[CrimeOutcome]
