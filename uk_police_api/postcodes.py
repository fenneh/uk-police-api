"""Client for the postcodes.io API.

postcodes.io is a free, open-source UK postcode lookup service — separate from
the UK Police Data API. Internet access is required. No authentication needed.

https://postcodes.io
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from .exceptions import (
    PoliceAPIError,
    PoliceAPINotFoundError,
    PoliceAPIResponseError,
    PoliceAPITimeoutError,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.postcodes.io/"


class GeocodedPostcode:
    """Result of a postcode lookup."""

    def __init__(self, data: dict[str, Any]) -> None:
        self.postcode: str = data["postcode"]
        self.latitude: float = data["latitude"]
        self.longitude: float = data["longitude"]
        self.region: str | None = data.get("region")
        self.admin_district: str | None = data.get("admin_district")
        self.admin_ward: str | None = data.get("admin_ward")
        self.parliamentary_constituency: str | None = data.get("parliamentary_constituency")
        self.country: str | None = data.get("country")
        self.pfa: str | None = data.get("pfa")  # Police force area

    def __repr__(self) -> str:
        return (
            f"GeocodedPostcode(postcode={self.postcode!r}, "
            f"latitude={self.latitude}, longitude={self.longitude})"
        )


class PostcodesIO:
    """Synchronous client for postcodes.io postcode geocoding.

    This is a separate API from data.police.uk — it requires internet access
    and calls https://api.postcodes.io.

    Usage::

        with PostcodesIO() as geo:
            loc = geo.lookup("SE1 1BP")
            print(loc.latitude, loc.longitude)
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._http = httpx.Client(
            base_url=_BASE_URL,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

    def lookup(self, postcode: str) -> GeocodedPostcode:
        """Geocode a single UK postcode to latitude/longitude.

        Args:
            postcode: UK postcode (e.g. "SE1 1BP" or "SE11BP").

        Raises:
            PoliceAPINotFoundError: If the postcode is not found or invalid.
        """
        slug = postcode.replace(" ", "").upper()
        try:
            response = self._http.get(f"postcodes/{slug}")
        except httpx.TimeoutException as e:
            raise PoliceAPITimeoutError(f"postcodes.io timed out for {postcode!r}") from e
        except httpx.HTTPError as e:
            raise PoliceAPIError(f"postcodes.io HTTP error for {postcode!r}") from e

        if response.status_code == 404:
            raise PoliceAPINotFoundError(f"Postcode not found: {postcode!r}")
        if response.status_code != 200:
            raise PoliceAPIError(f"postcodes.io returned HTTP {response.status_code}")

        try:
            body = response.json()
        except Exception as e:
            raise PoliceAPIResponseError("postcodes.io returned invalid JSON") from e

        return GeocodedPostcode(body["result"])

    def bulk_lookup(self, postcodes: list[str]) -> list[GeocodedPostcode | None]:
        """Geocode up to 100 postcodes in a single request.

        Args:
            postcodes: List of UK postcodes (max 100).

        Returns:
            List in the same order as input. Entries are None for invalid postcodes.
        """
        if not postcodes:
            return []
        if len(postcodes) > 100:
            raise ValueError("bulk_lookup supports a maximum of 100 postcodes per request")

        try:
            response = self._http.post("postcodes", json={"postcodes": postcodes})
        except httpx.TimeoutException as e:
            raise PoliceAPITimeoutError("postcodes.io bulk lookup timed out") from e
        except httpx.HTTPError as e:
            raise PoliceAPIError("postcodes.io bulk lookup HTTP error") from e

        if response.status_code != 200:
            raise PoliceAPIError(f"postcodes.io returned HTTP {response.status_code}")

        try:
            body = response.json()
        except Exception as e:
            raise PoliceAPIResponseError("postcodes.io returned invalid JSON") from e

        results: list[GeocodedPostcode | None] = []
        for item in body["result"]:
            if item["result"] is None:
                results.append(None)
            else:
                results.append(GeocodedPostcode(item["result"]))
        return results

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "PostcodesIO":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncPostcodesIO:
    """Asynchronous client for postcodes.io postcode geocoding.

    This is a separate API from data.police.uk — it requires internet access
    and calls https://api.postcodes.io.

    Usage::

        async with AsyncPostcodesIO() as geo:
            loc = await geo.lookup("SE1 1BP")
            print(loc.latitude, loc.longitude)
    """

    def __init__(self, timeout: float = 10.0) -> None:
        self._http = httpx.AsyncClient(
            base_url=_BASE_URL,
            timeout=timeout,
            headers={"Accept": "application/json"},
        )

    async def lookup(self, postcode: str) -> GeocodedPostcode:
        """Geocode a single UK postcode to latitude/longitude."""
        slug = postcode.replace(" ", "").upper()
        try:
            response = await self._http.get(f"postcodes/{slug}")
        except httpx.TimeoutException as e:
            raise PoliceAPITimeoutError(f"postcodes.io timed out for {postcode!r}") from e
        except httpx.HTTPError as e:
            raise PoliceAPIError(f"postcodes.io HTTP error for {postcode!r}") from e

        if response.status_code == 404:
            raise PoliceAPINotFoundError(f"Postcode not found: {postcode!r}")
        if response.status_code != 200:
            raise PoliceAPIError(f"postcodes.io returned HTTP {response.status_code}")

        try:
            body = response.json()
        except Exception as e:
            raise PoliceAPIResponseError("postcodes.io returned invalid JSON") from e

        return GeocodedPostcode(body["result"])

    async def bulk_lookup(self, postcodes: list[str]) -> list[GeocodedPostcode | None]:
        """Geocode up to 100 postcodes in a single request."""
        if not postcodes:
            return []
        if len(postcodes) > 100:
            raise ValueError("bulk_lookup supports a maximum of 100 postcodes per request")

        try:
            response = await self._http.post("postcodes", json={"postcodes": postcodes})
        except httpx.TimeoutException as e:
            raise PoliceAPITimeoutError("postcodes.io bulk lookup timed out") from e
        except httpx.HTTPError as e:
            raise PoliceAPIError("postcodes.io bulk lookup HTTP error") from e

        if response.status_code != 200:
            raise PoliceAPIError(f"postcodes.io returned HTTP {response.status_code}")

        try:
            body = response.json()
        except Exception as e:
            raise PoliceAPIResponseError("postcodes.io returned invalid JSON") from e

        results: list[GeocodedPostcode | None] = []
        for item in body["result"]:
            if item["result"] is None:
                results.append(None)
            else:
                results.append(GeocodedPostcode(item["result"]))
        return results

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncPostcodesIO":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
