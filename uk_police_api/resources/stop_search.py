"""Stop and search API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.stop_search import StopSearch
from ..utils import Polygon, encode_polygon, polygon_use_post, validate_date
from .crimes import _async_resolve_poly, _resolve_poly

if TYPE_CHECKING:
    from .._client import AsyncPoliceAPI, PoliceAPI


class StopSearchResource:
    """Synchronous stop and search resource."""

    def __init__(self, client: PoliceAPI) -> None:
        self._client = client

    def _do_poly_request(self, path: str, poly: Polygon, params: dict[str, str]) -> list[Any]:
        encoded = encode_polygon(poly)
        params["poly"] = encoded
        if polygon_use_post(poly, params):
            return self._client._post(path, data=params)
        return self._client._get(path, params=params)

    def street(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        poly: Polygon | None = None,
        postcode: str | None = None,
        radius_km: float = 1.0,
        date: str | None = None,
    ) -> list[StopSearch]:
        """Stop and searches within a radius of a point, or within a polygon.

        Supply one of: lat+lng, poly, or postcode+radius_km.

        Args:
            lat: Latitude of the centre point.
            lng: Longitude of the centre point.
            poly: Polygon boundary as a list of (lat, lng) tuples.
            postcode: UK postcode — geocoded via postcodes.io, then radius_km applied.
            radius_km: Radius in kilometres around the postcode (default 1.0).
            date: Month in "YYYY-MM" format. Defaults to latest available.
        """
        poly = _resolve_poly(postcode, radius_km, poly)
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)

        if poly is not None:
            raw: list[Any] = self._do_poly_request("stops-street", poly, params)
        else:
            if lat is not None:
                params["lat"] = str(lat)
            if lng is not None:
                params["lng"] = str(lng)
            raw = self._client._get("stops-street", params=params)

        return [StopSearch.model_validate(s) for s in raw]

    def at_location(
        self,
        location_id: int,
        date: str | None = None,
    ) -> list[StopSearch]:
        """Stop and searches at a specific location.

        Args:
            location_id: Location identifier.
            date: Month in "YYYY-MM" format.
        """
        params: dict[str, str] = {"location_id": str(location_id)}
        if date:
            params["date"] = validate_date(date)
        raw: list[Any] = self._client._get("stops-at-location", params=params)
        return [StopSearch.model_validate(s) for s in raw]

    def no_location(
        self,
        force: str,
        date: str | None = None,
    ) -> list[StopSearch]:
        """Stop and searches that could not be mapped to a location.

        Args:
            force: Police force identifier (e.g. "metropolitan").
            date: Month in "YYYY-MM" format.
        """
        params: dict[str, str] = {"force": force}
        if date:
            params["date"] = validate_date(date)
        raw: list[Any] = self._client._get("stops-no-location", params=params)
        return [StopSearch.model_validate(s) for s in raw]

    def by_force(
        self,
        force: str,
        date: str | None = None,
    ) -> list[StopSearch]:
        """All stop and searches carried out by a police force.

        Args:
            force: Police force identifier (e.g. "metropolitan").
            date: Month in "YYYY-MM" format.
        """
        params: dict[str, str] = {"force": force}
        if date:
            params["date"] = validate_date(date)
        raw: list[Any] = self._client._get("stops-force", params=params)
        return [StopSearch.model_validate(s) for s in raw]


class AsyncStopSearchResource(StopSearchResource):
    """Asynchronous stop and search resource."""

    def __init__(self, client: AsyncPoliceAPI) -> None:  # type: ignore[override]
        self._client = client  # type: ignore[assignment]

    async def _async_do_poly_request(
        self, path: str, poly: Polygon, params: dict[str, str]
    ) -> list[Any]:
        encoded = encode_polygon(poly)
        params["poly"] = encoded
        if polygon_use_post(poly, params):
            return await self._client._post(path, data=params)  # type: ignore[union-attr]
        return await self._client._get(path, params=params)  # type: ignore[union-attr]

    async def street(  # type: ignore[override]
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        poly: Polygon | None = None,
        postcode: str | None = None,
        radius_km: float = 1.0,
        date: str | None = None,
    ) -> list[StopSearch]:
        poly = await _async_resolve_poly(postcode, radius_km, poly)
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)

        if poly is not None:
            raw = await self._async_do_poly_request("stops-street", poly, params)
        else:
            if lat is not None:
                params["lat"] = str(lat)
            if lng is not None:
                params["lng"] = str(lng)
            raw = await self._client._get("stops-street", params=params)  # type: ignore[union-attr]

        return [StopSearch.model_validate(s) for s in raw]

    async def at_location(self, location_id: int, date: str | None = None) -> list[StopSearch]:  # type: ignore[override]
        params: dict[str, str] = {"location_id": str(location_id)}
        if date:
            params["date"] = validate_date(date)
        raw = await self._client._get("stops-at-location", params=params)  # type: ignore[union-attr]
        return [StopSearch.model_validate(s) for s in raw]

    async def no_location(self, force: str, date: str | None = None) -> list[StopSearch]:  # type: ignore[override]
        params: dict[str, str] = {"force": force}
        if date:
            params["date"] = validate_date(date)
        raw = await self._client._get("stops-no-location", params=params)  # type: ignore[union-attr]
        return [StopSearch.model_validate(s) for s in raw]

    async def by_force(self, force: str, date: str | None = None) -> list[StopSearch]:  # type: ignore[override]
        params: dict[str, str] = {"force": force}
        if date:
            params["date"] = validate_date(date)
        raw = await self._client._get("stops-force", params=params)  # type: ignore[union-attr]
        return [StopSearch.model_validate(s) for s in raw]
