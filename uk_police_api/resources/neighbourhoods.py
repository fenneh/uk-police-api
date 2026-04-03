"""Neighbourhood API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.common import Coordinates
from ..models.force import ForceOfficer
from ..models.neighbourhood import (
    LocatedNeighbourhood,
    Neighbourhood,
    NeighbourhoodEvent,
    NeighbourhoodLink,
    NeighbourhoodPriority,
)

if TYPE_CHECKING:
    from .._client import AsyncPoliceAPI, PoliceAPI


class NeighbourhoodsResource:
    """Synchronous neighbourhood resource."""

    def __init__(self, client: PoliceAPI) -> None:
        self._client = client

    def list(self, force: str) -> list[NeighbourhoodLink]:
        """List all neighbourhoods for a police force.

        Args:
            force: Force identifier (e.g. "metropolitan").
        """
        raw: list[Any] = self._client._get(f"{force}/neighbourhoods")
        return [NeighbourhoodLink.model_validate(n) for n in raw]

    def get(self, force: str, neighbourhood_id: str) -> Neighbourhood:
        """Get details for a specific neighbourhood.

        Args:
            force: Force identifier.
            neighbourhood_id: Neighbourhood identifier.
        """
        raw: dict[str, Any] = self._client._get(f"{force}/{neighbourhood_id}")
        return Neighbourhood.model_validate(raw)

    def boundary(self, force: str, neighbourhood_id: str) -> list[Coordinates]:
        """Boundary coordinates for a neighbourhood.

        Args:
            force: Force identifier.
            neighbourhood_id: Neighbourhood identifier.
        """
        raw: list[Any] = self._client._get(f"{force}/{neighbourhood_id}/boundary")
        return [Coordinates.model_validate(c) for c in raw]

    def people(self, force: str, neighbourhood_id: str) -> list[ForceOfficer]:
        """Neighbourhood policing team members.

        Args:
            force: Force identifier.
            neighbourhood_id: Neighbourhood identifier.
        """
        raw: list[Any] = self._client._get(f"{force}/{neighbourhood_id}/people")
        return [ForceOfficer.model_validate(o) for o in raw]

    def events(self, force: str, neighbourhood_id: str) -> list[NeighbourhoodEvent]:
        """Upcoming events for a neighbourhood.

        Args:
            force: Force identifier.
            neighbourhood_id: Neighbourhood identifier.
        """
        raw: list[Any] = self._client._get(f"{force}/{neighbourhood_id}/events")
        return [NeighbourhoodEvent.model_validate(e) for e in raw]

    def priorities(self, force: str, neighbourhood_id: str) -> list[NeighbourhoodPriority]:
        """Policing priorities for a neighbourhood.

        Args:
            force: Force identifier.
            neighbourhood_id: Neighbourhood identifier.
        """
        raw: list[Any] = self._client._get(f"{force}/{neighbourhood_id}/priorities")
        return [NeighbourhoodPriority.model_validate(p) for p in raw]

    def locate(self, lat: float, lng: float) -> LocatedNeighbourhood:
        """Find the neighbourhood containing a given coordinate.

        Args:
            lat: Latitude.
            lng: Longitude.
        """
        raw: dict[str, Any] = self._client._get(
            "locate-neighbourhood", params={"q": f"{lat},{lng}"}
        )
        return LocatedNeighbourhood.model_validate(raw)


class AsyncNeighbourhoodsResource(NeighbourhoodsResource):
    """Asynchronous neighbourhood resource."""

    def __init__(self, client: AsyncPoliceAPI) -> None:  # type: ignore[override]
        self._client = client  # type: ignore[assignment]

    async def list(self, force: str) -> list[NeighbourhoodLink]:  # type: ignore[override]
        raw = await self._client._get(f"{force}/neighbourhoods")  # type: ignore[union-attr]
        return [NeighbourhoodLink.model_validate(n) for n in raw]

    async def get(self, force: str, neighbourhood_id: str) -> Neighbourhood:  # type: ignore[override]
        raw = await self._client._get(f"{force}/{neighbourhood_id}")  # type: ignore[union-attr]
        return Neighbourhood.model_validate(raw)

    async def boundary(self, force: str, neighbourhood_id: str) -> list[Coordinates]:  # type: ignore[override]
        raw = await self._client._get(f"{force}/{neighbourhood_id}/boundary")  # type: ignore[union-attr]
        return [Coordinates.model_validate(c) for c in raw]

    async def people(self, force: str, neighbourhood_id: str) -> list[ForceOfficer]:  # type: ignore[override]
        raw = await self._client._get(f"{force}/{neighbourhood_id}/people")  # type: ignore[union-attr]
        return [ForceOfficer.model_validate(o) for o in raw]

    async def events(self, force: str, neighbourhood_id: str) -> list[NeighbourhoodEvent]:  # type: ignore[override]
        raw = await self._client._get(f"{force}/{neighbourhood_id}/events")  # type: ignore[union-attr]
        return [NeighbourhoodEvent.model_validate(e) for e in raw]

    async def priorities(self, force: str, neighbourhood_id: str) -> list[NeighbourhoodPriority]:  # type: ignore[override]
        raw = await self._client._get(f"{force}/{neighbourhood_id}/priorities")  # type: ignore[union-attr]
        return [NeighbourhoodPriority.model_validate(p) for p in raw]

    async def locate(self, lat: float, lng: float) -> LocatedNeighbourhood:  # type: ignore[override]
        raw = await self._client._get(  # type: ignore[union-attr]
            "locate-neighbourhood", params={"q": f"{lat},{lng}"}
        )
        return LocatedNeighbourhood.model_validate(raw)
