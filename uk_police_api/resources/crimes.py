"""Crime-related API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from ..models.crime import (
    Crime,
    CrimeCategory,
    CrimeLastUpdated,
    CrimeOutcome,
    CrimeWithOutcomes,
)
from ..utils import (
    Polygon,
    circle_polygon,
    encode_polygon,
    polygon_use_post,
    recent_months,
    validate_date,
)

if TYPE_CHECKING:
    from .._client import AsyncPoliceAPI, PoliceAPI


def _resolve_poly(
    postcode: str | None,
    radius_km: float,
    poly: Polygon | None,
) -> Polygon | None:
    """Geocode a postcode + radius into a polygon, or pass through an existing polygon."""
    if postcode is not None and poly is not None:
        raise ValueError("Specify postcode or poly, not both")
    if postcode is not None:
        from ..postcodes import PostcodesIO
        with PostcodesIO() as geo:
            loc = geo.lookup(postcode)
        return circle_polygon(loc.latitude, loc.longitude, radius_km)
    return poly


async def _async_resolve_poly(
    postcode: str | None,
    radius_km: float,
    poly: Polygon | None,
) -> Polygon | None:
    """Async version of _resolve_poly."""
    if postcode is not None and poly is not None:
        raise ValueError("Specify postcode or poly, not both")
    if postcode is not None:
        from ..postcodes import AsyncPostcodesIO
        async with AsyncPostcodesIO() as geo:
            loc = await geo.lookup(postcode)
        return circle_polygon(loc.latitude, loc.longitude, radius_km)
    return poly


class CrimesResource:
    """Synchronous crime data resource."""

    def __init__(self, client: PoliceAPI) -> None:
        self._client = client

    def _build_location_params(
        self,
        lat: float | None,
        lng: float | None,
        location_id: int | None,
        date: str | None,
        extra: dict[str, str] | None = None,
    ) -> dict[str, str]:
        params: dict[str, str] = {}
        if lat is not None:
            params["lat"] = str(lat)
        if lng is not None:
            params["lng"] = str(lng)
        if location_id is not None:
            params["location_id"] = str(location_id)
        if date is not None:
            params["date"] = validate_date(date)
        if extra:
            params.update(extra)
        return params

    def _do_poly_request(self, path: str, poly: Polygon, params: dict[str, str]) -> list[Any]:
        encoded = encode_polygon(poly)
        params["poly"] = encoded
        if polygon_use_post(poly, params):
            return self._client._post(path, data=params)
        return self._client._get(path, params=params)

    def street(
        self,
        category: str = "all-crime",
        *,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        poly: Polygon | None = None,
        postcode: str | None = None,
        radius_km: float = 1.0,
        date: str | None = None,
    ) -> list[Crime]:
        """Street-level crimes within a radius of a point, or within a polygon.

        Supply one of: lat+lng, location_id, poly, or postcode+radius_km.

        Args:
            category: Crime category slug (e.g. "possession-of-weapons", "all-crime").
            lat: Latitude of the centre point.
            lng: Longitude of the centre point.
            location_id: Specific location ID (alternative to lat/lng).
            poly: Polygon boundary as a list of (lat, lng) tuples.
            postcode: UK postcode — geocoded via postcodes.io, then radius_km applied.
            radius_km: Radius in kilometres around the postcode (default 1.0).
            date: Month to query in "YYYY-MM" format. Defaults to latest available.
        """
        poly = _resolve_poly(postcode, radius_km, poly)
        path = f"crimes-street/{category}"
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)

        if poly is not None:
            raw: list[Any] = self._do_poly_request(path, poly, params)
        else:
            if lat is not None:
                params["lat"] = str(lat)
            if lng is not None:
                params["lng"] = str(lng)
            if location_id is not None:
                params["location_id"] = str(location_id)
            raw = self._client._get(path, params=params)

        return [Crime.model_validate(c) for c in raw]

    def at_location(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        date: str | None = None,
    ) -> list[Crime]:
        """Crimes at a specific mapped location.

        Supply either lat+lng (snaps to nearest location) or location_id.
        """
        params = self._build_location_params(lat, lng, location_id, date)
        raw: list[Any] = self._client._get("crimes-at-location", params=params)
        return [Crime.model_validate(c) for c in raw]

    def no_location(
        self,
        category: str,
        force: str,
        date: str | None = None,
    ) -> list[Crime]:
        """Crimes that could not be mapped to a location.

        Args:
            category: Crime category slug.
            force: Police force identifier (e.g. "metropolitan").
            date: Month in "YYYY-MM" format.
        """
        params: dict[str, str] = {"category": category, "force": force}
        if date:
            params["date"] = validate_date(date)
        raw: list[Any] = self._client._get("crimes-no-location", params=params)
        return [Crime.model_validate(c) for c in raw]

    def categories(self, date: str | None = None) -> list[CrimeCategory]:
        """List all crime categories.

        Args:
            date: Month in "YYYY-MM" format. Defaults to latest.
        """
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)
        raw: list[Any] = self._client._get("crime-categories", params=params or None)
        return [CrimeCategory.model_validate(c) for c in raw]

    def last_updated(self) -> CrimeLastUpdated:
        """Date when crime data was last updated."""
        raw: dict[str, Any] = self._client._get("crime-last-updated")
        return CrimeLastUpdated.model_validate(raw)

    def outcomes_at_location(
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        poly: Polygon | None = None,
        date: str | None = None,
    ) -> list[dict[str, Any]]:
        """Case outcomes for crimes at a location or within a polygon.

        Returns raw dicts as the response structure varies (crimes + outcomes interleaved).
        """
        path = "outcomes-at-location"
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)

        if poly is not None:
            return self._do_poly_request(path, poly, params)

        if lat is not None:
            params["lat"] = str(lat)
        if lng is not None:
            params["lng"] = str(lng)
        if location_id is not None:
            params["location_id"] = str(location_id)
        return self._client._get(path, params=params)

    def outcomes_for_crime(self, persistent_id: str) -> CrimeWithOutcomes:
        """Full case history (outcomes) for a specific crime.

        Args:
            persistent_id: The 64-character persistent crime identifier.
        """
        raw: dict[str, Any] = self._client._get(f"outcomes-for-crime/{persistent_id}")
        crime = Crime.model_validate(raw["crime"])
        outcomes = [CrimeOutcome.model_validate(o) for o in raw.get("outcomes", [])]
        return CrimeWithOutcomes(crime=crime, outcomes=outcomes)

    def street_months(
        self,
        category: str = "all-crime",
        *,
        months: int = 3,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        poly: Polygon | None = None,
        postcode: str | None = None,
        radius_km: float = 1.0,
    ) -> list[Crime]:
        """Street-level crimes across multiple months.

        Queries the last N calendar months and returns all results combined.
        Crimes are deduplicated by persistent_id across months.

        Supply one of: lat+lng, location_id, poly, or postcode+radius_km.

        Note: Crime data is typically 2-3 months behind the current date.
        Use api.availability.dates() to see exactly which months have data.

        Args:
            category: Crime category slug (e.g. "possession-of-weapons").
            months: Number of past calendar months to query (default 3).
            lat: Latitude of centre point.
            lng: Longitude of centre point.
            location_id: Specific location ID.
            poly: Polygon boundary as a list of (lat, lng) tuples.
            postcode: UK postcode — geocoded via postcodes.io, then radius_km applied.
            radius_km: Radius in kilometres around the postcode (default 1.0).
        """
        poly = _resolve_poly(postcode, radius_km, poly)
        seen: set[str] = set()
        results: list[Crime] = []
        for month in recent_months(months):
            try:
                crimes = self.street(
                    category,
                    lat=lat,
                    lng=lng,
                    location_id=location_id,
                    poly=poly,
                    date=month,
                )
            except Exception:
                continue
            for c in crimes:
                if c.persistent_id not in seen:
                    seen.add(c.persistent_id)
                    results.append(c)
        return results


class AsyncCrimesResource(CrimesResource):
    """Asynchronous crime data resource."""

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
        category: str = "all-crime",
        *,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        poly: Polygon | None = None,
        postcode: str | None = None,
        radius_km: float = 1.0,
        date: str | None = None,
    ) -> list[Crime]:
        poly = await _async_resolve_poly(postcode, radius_km, poly)
        path = f"crimes-street/{category}"
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)

        if poly is not None:
            raw = await self._async_do_poly_request(path, poly, params)
        else:
            if lat is not None:
                params["lat"] = str(lat)
            if lng is not None:
                params["lng"] = str(lng)
            if location_id is not None:
                params["location_id"] = str(location_id)
            raw = await self._client._get(path, params=params)  # type: ignore[union-attr]

        return [Crime.model_validate(c) for c in raw]

    async def at_location(  # type: ignore[override]
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        date: str | None = None,
    ) -> list[Crime]:
        params = self._build_location_params(lat, lng, location_id, date)
        raw = await self._client._get("crimes-at-location", params=params)  # type: ignore[union-attr]
        return [Crime.model_validate(c) for c in raw]

    async def no_location(  # type: ignore[override]
        self,
        category: str,
        force: str,
        date: str | None = None,
    ) -> list[Crime]:
        params: dict[str, str] = {"category": category, "force": force}
        if date:
            params["date"] = validate_date(date)
        raw = await self._client._get("crimes-no-location", params=params)  # type: ignore[union-attr]
        return [Crime.model_validate(c) for c in raw]

    async def categories(self, date: str | None = None) -> list[CrimeCategory]:  # type: ignore[override]
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)
        raw = await self._client._get("crime-categories", params=params or None)  # type: ignore[union-attr]
        return [CrimeCategory.model_validate(c) for c in raw]

    async def last_updated(self) -> CrimeLastUpdated:  # type: ignore[override]
        raw = await self._client._get("crime-last-updated")  # type: ignore[union-attr]
        return CrimeLastUpdated.model_validate(raw)

    async def outcomes_at_location(  # type: ignore[override]
        self,
        *,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        poly: Polygon | None = None,
        date: str | None = None,
    ) -> list[dict[str, Any]]:
        path = "outcomes-at-location"
        params: dict[str, str] = {}
        if date:
            params["date"] = validate_date(date)

        if poly is not None:
            return await self._async_do_poly_request(path, poly, params)

        if lat is not None:
            params["lat"] = str(lat)
        if lng is not None:
            params["lng"] = str(lng)
        if location_id is not None:
            params["location_id"] = str(location_id)
        return await self._client._get(path, params=params)  # type: ignore[union-attr]

    async def outcomes_for_crime(self, persistent_id: str) -> CrimeWithOutcomes:  # type: ignore[override]
        raw = await self._client._get(f"outcomes-for-crime/{persistent_id}")  # type: ignore[union-attr]
        crime = Crime.model_validate(raw["crime"])
        outcomes = [CrimeOutcome.model_validate(o) for o in raw.get("outcomes", [])]
        return CrimeWithOutcomes(crime=crime, outcomes=outcomes)

    async def street_months(  # type: ignore[override]
        self,
        category: str = "all-crime",
        *,
        months: int = 3,
        lat: float | None = None,
        lng: float | None = None,
        location_id: int | None = None,
        poly: Polygon | None = None,
        postcode: str | None = None,
        radius_km: float = 1.0,
    ) -> list[Crime]:
        """Street-level crimes across multiple months (async version)."""
        poly = await _async_resolve_poly(postcode, radius_km, poly)
        seen: set[str] = set()
        results: list[Crime] = []
        for month in recent_months(months):
            try:
                crimes = await self.street(
                    category,
                    lat=lat,
                    lng=lng,
                    location_id=location_id,
                    poly=poly,
                    date=month,
                )
            except Exception:
                continue
            for c in crimes:
                if c.persistent_id not in seen:
                    seen.add(c.persistent_id)
                    results.append(c)
        return results
