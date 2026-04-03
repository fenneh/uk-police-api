"""Data availability API resource."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.availability import AvailabilityDate

if TYPE_CHECKING:
    from .._client import AsyncPoliceAPI, PoliceAPI


class AvailabilityResource:
    """Synchronous data availability resource."""

    def __init__(self, client: PoliceAPI) -> None:
        self._client = client

    def dates(self) -> list[AvailabilityDate]:
        """List all available months of crime and stop-and-search data.

        Each entry shows the month and which forces have stop-and-search data available.
        """
        raw: list[Any] = self._client._get("crimes-street-dates")
        return [AvailabilityDate.model_validate(d) for d in raw]


class AsyncAvailabilityResource(AvailabilityResource):
    """Asynchronous data availability resource."""

    def __init__(self, client: AsyncPoliceAPI) -> None:  # type: ignore[override]
        self._client = client  # type: ignore[assignment]

    async def dates(self) -> list[AvailabilityDate]:  # type: ignore[override]
        raw = await self._client._get("crimes-street-dates")  # type: ignore[union-attr]
        return [AvailabilityDate.model_validate(d) for d in raw]
