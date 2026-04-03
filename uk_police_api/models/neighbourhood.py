"""Neighbourhood data models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .common import Coordinates


class ContactDetails(BaseModel):
    model_config = ConfigDict(extra="allow")

    email: str | None = None
    telephone: str | None = None
    mobile: str | None = None
    web: str | None = None
    address: str | None = None
    facebook: str | None = None
    twitter: str | None = None
    youtube: str | None = None


class NeighbourhoodLink(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str


class Neighbourhood(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: str | None = None
    url_force: str | None = None
    contact_details: ContactDetails = ContactDetails()
    centre: Coordinates | None = None
    links: list[dict[str, str]] = []
    locations: list[dict[str, str]] = []
    population: str | int | None = None


class NeighbourhoodEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str
    description: str | None = None
    address: str | None = None
    type: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    contact_details: ContactDetails = ContactDetails()


class NeighbourhoodPriority(BaseModel):
    model_config = ConfigDict(extra="ignore")

    issue: str
    issue_date: str | None = None
    action: str | None = None
    action_date: str | None = None


class LocatedNeighbourhood(BaseModel):
    model_config = ConfigDict(extra="ignore")

    force: str
    neighbourhood: str
