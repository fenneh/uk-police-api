"""Tests for core client behaviour: caching, retry, errors."""

import pytest
import respx
from httpx import Response

from uk_police_api import PoliceAPI, AsyncPoliceAPI
from uk_police_api.exceptions import (
    PoliceAPINotFoundError,
    PoliceAPIRateLimitError,
    PoliceAPIResponseError,
    PoliceAPIServerError,
)

BASE = "https://data.police.uk/api"


class TestCache:
    def test_caches_get_response(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI(cache_ttl=60) as api:
                r1 = api.crimes.last_updated()
                r2 = api.crimes.last_updated()
            assert r1.date == "2024-10"
            assert r2.date == "2024-10"
            assert route.call_count == 1  # second call served from cache

    def test_no_cache_when_disabled(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.last_updated()
                api.crimes.last_updated()
            assert route.call_count == 2

    def test_clear_cache(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI(cache_ttl=60) as api:
                api.crimes.last_updated()
                api.clear_cache()
                api.crimes.last_updated()
            assert route.call_count == 2


class TestErrorHandling:
    def test_404_raises_not_found(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/forces/fake-force").mock(return_value=Response(404))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPINotFoundError):
                    api.forces.get("fake-force")

    def test_server_error_raises_after_retries(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(return_value=Response(500))
            with PoliceAPI(max_retries=1) as api:
                with pytest.raises(PoliceAPIServerError):
                    api.crimes.last_updated()

    def test_429_raises_rate_limit_after_retries(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(return_value=Response(429))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIRateLimitError):
                    api.crimes.last_updated()

    def test_invalid_json_raises_response_error(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, content=b"not json")
            )
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIResponseError):
                    api.crimes.last_updated()


class TestContextManager:
    def test_sync_context_manager(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI() as api:
                result = api.crimes.last_updated()
            assert result.date == "2024-10"

    async def test_async_context_manager(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            async with AsyncPoliceAPI() as api:
                result = await api.crimes.last_updated()
            assert result.date == "2024-10"
