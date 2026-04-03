"""Data models for the UK Police API."""

from .availability import AvailabilityDate
from .common import Coordinates, EngagementMethod, Location, Street
from .crime import (
    Crime,
    CrimeCategory,
    CrimeLastUpdated,
    CrimeOutcome,
    CrimeWithOutcomes,
    OutcomeCategory,
    OutcomeStatus,
)
from .force import Force, ForceLink, ForceOfficer
from .neighbourhood import (
    ContactDetails,
    LocatedNeighbourhood,
    Neighbourhood,
    NeighbourhoodEvent,
    NeighbourhoodLink,
    NeighbourhoodPriority,
)
from .stop_search import StopSearch

__all__ = [
    "AvailabilityDate",
    "Coordinates",
    "ContactDetails",
    "Crime",
    "CrimeCategory",
    "CrimeLastUpdated",
    "CrimeOutcome",
    "CrimeWithOutcomes",
    "EngagementMethod",
    "Force",
    "ForceLink",
    "ForceOfficer",
    "Location",
    "LocatedNeighbourhood",
    "Neighbourhood",
    "NeighbourhoodEvent",
    "NeighbourhoodLink",
    "NeighbourhoodPriority",
    "OutcomeCategory",
    "OutcomeStatus",
    "StopSearch",
    "Street",
]
