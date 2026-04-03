"""Core HTTP clients for the UK Police Data API."""

from __future__ import annotations

import hashlib
import json
import logging
import random
import time
from functools import cached_property
from typing import TYPE_CHECKING, Any

import httpx

from .exceptions import (
    PoliceAPIError,
    PoliceAPINotFoundError,
    PoliceAPIRateLimitError,
    PoliceAPIResponseError,
    PoliceAPIServerError,
    PoliceAPITimeoutError,
)

logger = logging.getLogger(__name__)

BASE_URL = "https://data.police.uk/api/"
_RETRYABLE = {429, 500, 502, 503, 504}


class Cache:
    """Simple in-memory TTL cache for GET responses."""

    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[float, Any]] = {}

    def _key(self, path: str, params: dict[str, str] | None) -> str:
        payload = json.dumps({"path": path, "params": params}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def get(self, path: str, params: dict[str, str] | None = None) -> Any | None:
        key = self._key(path, params)
        entry = self._store.get(key)
        if entry is None:
            return None
        expires_at, data = entry
        if time.time() < expires_at:
            logger.debug("Cache hit: %s", path)
            return data
        del self._store[key]
        return None

    def set(self, path: str, params: dict[str, str] | None, data: Any) -> None:
        key = self._key(path, params)
        self._store[key] = (time.time() + self._ttl, data)

    def clear(self) -> None:
        self._store.clear()


def _backoff(attempt: int) -> float:
    delay = min(0.5 * (2**attempt), 60.0)
    return delay * (0.5 + random.random() * 0.5)


def _raise_for_status(response: httpx.Response) -> None:
    code = response.status_code
    url = str(response.url)
    if code == 404:
        raise PoliceAPINotFoundError(f"Not found: {url}")
    if code == 429:
        raise PoliceAPIRateLimitError(f"Rate limit exceeded: {url}")
    if 500 <= code < 600:
        raise PoliceAPIServerError(f"Server error {code}: {url}", status_code=code)
    raise PoliceAPIError(f"HTTP {code}: {url}", status_code=code)


class PoliceAPI:
    """Synchronous client for the UK Police Data API."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 4,
        cache_ttl: int | None = 300,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._cache = Cache(cache_ttl) if cache_ttl is not None else None
        self._http = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"User-Agent": "uk-police-api/0.1.0", "Accept": "application/json"},
        )

    @cached_property
    def crimes(self) -> "CrimesResource":
        from .resources.crimes import CrimesResource

        return CrimesResource(self)

    @cached_property
    def stop_search(self) -> "StopSearchResource":
        from .resources.stop_search import StopSearchResource

        return StopSearchResource(self)

    @cached_property
    def forces(self) -> "ForcesResource":
        from .resources.forces import ForcesResource

        return ForcesResource(self)

    @cached_property
    def neighbourhoods(self) -> "NeighbourhoodsResource":
        from .resources.neighbourhoods import NeighbourhoodsResource

        return NeighbourhoodsResource(self)

    @cached_property
    def availability(self) -> "AvailabilityResource":
        from .resources.availability import AvailabilityResource

        return AvailabilityResource(self)

    def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Any:
        url = path.lstrip("/")

        if method == "GET" and self._cache:
            cached = self._cache.get(url, params)
            if cached is not None:
                return cached

        for attempt in range(self._max_retries + 1):
            try:
                if method == "GET":
                    logger.debug("GET %s params=%s", url, params)
                    response = self._http.get(url, params=params)
                else:
                    logger.debug("POST %s data=%s", url, data)
                    response = self._http.post(url, data=data)
            except httpx.TimeoutException as e:
                raise PoliceAPITimeoutError(f"Request timed out: {url}") from e
            except httpx.HTTPError as e:
                raise PoliceAPIError(f"HTTP error: {url}") from e

            if response.status_code == 200:
                try:
                    result = response.json()
                except Exception as e:
                    raise PoliceAPIResponseError(f"Invalid JSON from {url}") from e
                if method == "GET" and self._cache:
                    self._cache.set(url, params, result)
                return result

            if response.status_code not in _RETRYABLE or attempt == self._max_retries:
                _raise_for_status(response)

            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else _backoff(attempt)
            logger.warning(
                "HTTP %d on %s, retry %d/%d in %.2fs",
                response.status_code, url, attempt + 1, self._max_retries, wait,
            )
            time.sleep(wait)

        raise PoliceAPIError(f"Exhausted retries for {url}")  # pragma: no cover

    def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        return self._request("GET", path, params=params)

    def _post(self, path: str, data: dict[str, str] | None = None) -> Any:
        return self._request("POST", path, data=data)

    def clear_cache(self) -> None:
        if self._cache:
            self._cache.clear()

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "PoliceAPI":
        return self

    def __exit__(self, *args: object) -> None:
        self.close()


class AsyncPoliceAPI:
    """Asynchronous client for the UK Police Data API."""

    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 4,
        cache_ttl: int | None = 300,
    ) -> None:
        self._timeout = timeout
        self._max_retries = max_retries
        self._cache = Cache(cache_ttl) if cache_ttl is not None else None
        self._http = httpx.AsyncClient(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"User-Agent": "uk-police-api/0.1.0", "Accept": "application/json"},
        )

    @cached_property
    def crimes(self) -> "AsyncCrimesResource":
        from .resources.crimes import AsyncCrimesResource

        return AsyncCrimesResource(self)

    @cached_property
    def stop_search(self) -> "AsyncStopSearchResource":
        from .resources.stop_search import AsyncStopSearchResource

        return AsyncStopSearchResource(self)

    @cached_property
    def forces(self) -> "AsyncForcesResource":
        from .resources.forces import AsyncForcesResource

        return AsyncForcesResource(self)

    @cached_property
    def neighbourhoods(self) -> "AsyncNeighbourhoodsResource":
        from .resources.neighbourhoods import AsyncNeighbourhoodsResource

        return AsyncNeighbourhoodsResource(self)

    @cached_property
    def availability(self) -> "AsyncAvailabilityResource":
        from .resources.availability import AsyncAvailabilityResource

        return AsyncAvailabilityResource(self)

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, str] | None = None,
        data: dict[str, str] | None = None,
    ) -> Any:
        import asyncio

        url = path.lstrip("/")

        if method == "GET" and self._cache:
            cached = self._cache.get(url, params)
            if cached is not None:
                return cached

        for attempt in range(self._max_retries + 1):
            try:
                if method == "GET":
                    logger.debug("GET %s params=%s", url, params)
                    response = await self._http.get(url, params=params)
                else:
                    logger.debug("POST %s data=%s", url, data)
                    response = await self._http.post(url, data=data)
            except httpx.TimeoutException as e:
                raise PoliceAPITimeoutError(f"Request timed out: {url}") from e
            except httpx.HTTPError as e:
                raise PoliceAPIError(f"HTTP error: {url}") from e

            if response.status_code == 200:
                try:
                    result = response.json()
                except Exception as e:
                    raise PoliceAPIResponseError(f"Invalid JSON from {url}") from e
                if method == "GET" and self._cache:
                    self._cache.set(url, params, result)
                return result

            if response.status_code not in _RETRYABLE or attempt == self._max_retries:
                _raise_for_status(response)

            retry_after = response.headers.get("Retry-After")
            wait = float(retry_after) if retry_after else _backoff(attempt)
            logger.warning(
                "HTTP %d on %s, retry %d/%d in %.2fs",
                response.status_code, url, attempt + 1, self._max_retries, wait,
            )
            await asyncio.sleep(wait)

        raise PoliceAPIError(f"Exhausted retries for {url}")  # pragma: no cover

    async def _get(self, path: str, params: dict[str, str] | None = None) -> Any:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, data: dict[str, str] | None = None) -> Any:
        return await self._request("POST", path, data=data)

    def clear_cache(self) -> None:
        if self._cache:
            self._cache.clear()

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncPoliceAPI":
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()


if TYPE_CHECKING:
    from .resources.availability import AsyncAvailabilityResource, AvailabilityResource
    from .resources.crimes import AsyncCrimesResource, CrimesResource
    from .resources.forces import AsyncForcesResource, ForcesResource
    from .resources.neighbourhoods import AsyncNeighbourhoodsResource, NeighbourhoodsResource
    from .resources.stop_search import AsyncStopSearchResource, StopSearchResource
