"""Police force API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.force import Force, ForceLink, ForceOfficer

if TYPE_CHECKING:
    from .._client import AsyncPoliceAPI, PoliceAPI


class ForcesResource:
    """Synchronous police force resource."""

    def __init__(self, client: PoliceAPI) -> None:
        self._client = client

    def list(self) -> list[ForceLink]:
        """List all UK police forces."""
        raw: list[Any] = self._client._get("forces")
        return [ForceLink.model_validate(f) for f in raw]

    def get(self, force_id: str) -> Force:
        """Get details for a specific police force.

        Args:
            force_id: Force identifier (e.g. "metropolitan", "thames-valley").
        """
        raw: dict[str, Any] = self._client._get(f"forces/{force_id}")
        return Force.model_validate(raw)

    def people(self, force_id: str) -> list[ForceOfficer]:
        """Senior officers for a police force.

        Args:
            force_id: Force identifier.
        """
        raw: list[Any] = self._client._get(f"forces/{force_id}/people")
        return [ForceOfficer.model_validate(o) for o in raw]


class AsyncForcesResource(ForcesResource):
    """Asynchronous police force resource."""

    def __init__(self, client: AsyncPoliceAPI) -> None:  # type: ignore[override]
        self._client = client  # type: ignore[assignment]

    async def list(self) -> list[ForceLink]:  # type: ignore[override]
        raw = await self._client._get("forces")  # type: ignore[union-attr]
        return [ForceLink.model_validate(f) for f in raw]

    async def get(self, force_id: str) -> Force:  # type: ignore[override]
        raw = await self._client._get(f"forces/{force_id}")  # type: ignore[union-attr]
        return Force.model_validate(raw)

    async def people(self, force_id: str) -> list[ForceOfficer]:  # type: ignore[override]
        raw = await self._client._get(f"forces/{force_id}/people")  # type: ignore[union-attr]
        return [ForceOfficer.model_validate(o) for o in raw]
