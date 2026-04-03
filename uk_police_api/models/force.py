"""Police force data models."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from .common import EngagementMethod


class ForceLink(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str


class Force(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    description: str | None = None
    url: str | None = None
    telephone: str | None = None
    engagement_methods: list[EngagementMethod] = []


class ForceOfficer(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    rank: str
    bio: str | None = None
    contact_details: dict[str, str] = {}
