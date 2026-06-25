"""Tests for core client behaviour: caching, retry, errors, disk cache."""

import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx
from httpx import Response

from uk_police_api import AsyncPoliceAPI, PoliceAPI
from uk_police_api.exceptions import (
    PoliceAPIError,
    PoliceAPINotFoundError,
    PoliceAPIRateLimitError,
    PoliceAPIResponseError,
    PoliceAPIServerError,
    PoliceAPITimeoutError,
)

BASE = "https://data.police.uk/api"


class TestMemoryCache:
    def test_caches_get_response(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI(cache_ttl=60) as api:
                r1 = api.crimes.last_updated()
                api.crimes.last_updated()
            assert r1.date == "2024-10"
            assert route.call_count == 1

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

    def test_expired_cache_refetches(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI(cache_ttl=1) as api:
                api.crimes.last_updated()
                time.sleep(1.1)
                api.crimes.last_updated()
            assert route.call_count == 2

    def test_post_requests_not_cached(self):
        """POST responses (polygon queries) must never be cached."""
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            # Polygon long enough to trigger POST
            from uk_police_api.utils import circle_polygon

            poly = circle_polygon(51.5, -0.1, radius_km=50, num_points=200)
            route = router.post("/crimes-street/all-crime").mock(
                return_value=Response(200, json=[])
            )
            with PoliceAPI(cache_ttl=60) as api:
                api.crimes.street(poly=poly)
                api.crimes.street(poly=poly)
            assert route.call_count == 2


class TestDiskCache:
    def test_disk_cache_persists_between_instances(self, tmp_path):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            cache_dir = tmp_path / "cache"

            with PoliceAPI(cache_ttl=60, cache_dir=cache_dir) as api:
                api.crimes.last_updated()

            # Second instance reads from disk
            with PoliceAPI(cache_ttl=60, cache_dir=cache_dir) as api:
                result = api.crimes.last_updated()

        assert result.date == "2024-10"
        assert route.call_count == 1

    def test_disk_cache_dir_created(self, tmp_path):
        cache_dir = tmp_path / "nested" / "cache"
        assert not cache_dir.exists()
        with PoliceAPI(cache_ttl=60, cache_dir=cache_dir):
            pass
        assert cache_dir.exists()

    def test_disk_cache_clear_removes_files(self, tmp_path):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            cache_dir = tmp_path / "cache"
            with PoliceAPI(cache_ttl=60, cache_dir=cache_dir) as api:
                api.crimes.last_updated()
                assert any(cache_dir.glob("*.json"))
                api.clear_cache()
                assert not any(cache_dir.glob("*.json"))

    def test_disk_cache_expired_refetches(self, tmp_path):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            cache_dir = tmp_path / "cache"
            with PoliceAPI(cache_ttl=1, cache_dir=cache_dir) as api:
                api.crimes.last_updated()
            time.sleep(1.1)
            with PoliceAPI(cache_ttl=60, cache_dir=cache_dir) as api:
                api.crimes.last_updated()
        assert route.call_count == 2

    def test_disk_cache_corrupt_file_handled(self, tmp_path):
        cache_dir = tmp_path / "cache"
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI(cache_ttl=60, cache_dir=cache_dir) as api:
                api.crimes.last_updated()
            for f in cache_dir.glob("*.json"):
                f.write_text("{bad json")
            with PoliceAPI(cache_ttl=60, cache_dir=cache_dir) as api:
                result = api.crimes.last_updated()
        assert result.date == "2024-10"
        assert route.call_count == 2


class TestErrorHandling:
    def test_404_raises_not_found(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/forces/fake-force").mock(return_value=Response(404))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPINotFoundError):
                    api.forces.get("fake-force")

    def test_404_not_retried(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/forces/fake-force").mock(return_value=Response(404))
            with PoliceAPI(max_retries=3) as api:
                with pytest.raises(PoliceAPINotFoundError):
                    api.forces.get("fake-force")
            assert route.call_count == 1  # not retried

    def test_server_error_retried_then_raises(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(return_value=Response(500))
            with PoliceAPI(max_retries=1) as api:
                with pytest.raises(PoliceAPIServerError):
                    api.crimes.last_updated()
            assert route.call_count == 2  # initial + 1 retry

    def test_429_raises_rate_limit_after_retries(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(return_value=Response(429))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIRateLimitError):
                    api.crimes.last_updated()

    def test_server_error_has_status_code(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(return_value=Response(503))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIServerError) as exc_info:
                    api.crimes.last_updated()
            assert exc_info.value.status_code == 503

    def test_invalid_json_raises_response_error(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, content=b"not json{{{")
            )
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIResponseError):
                    api.crimes.last_updated()

    def test_not_found_error_has_404_status(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/forces/bad").mock(return_value=Response(404))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPINotFoundError) as exc_info:
                    api.forces.get("bad")
            assert exc_info.value.status_code == 404

    def test_unknown_http_status_raises_police_api_error(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(return_value=Response(401))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIError) as exc_info:
                    api.crimes.last_updated()
        assert type(exc_info.value) is PoliceAPIError
        assert exc_info.value.status_code == 401

    def test_timeout_raises_timeout_error(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(side_effect=httpx.TimeoutException("timeout"))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPITimeoutError):
                    api.crimes.last_updated()

    def test_http_error_raises_police_api_error(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(side_effect=httpx.HTTPError("connection failed"))
            with PoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIError):
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


class TestResourceLazyInit:
    def test_resources_are_cached_property(self):
        with PoliceAPI(cache_ttl=None) as api:
            r1 = api.crimes
            r2 = api.crimes
            assert r1 is r2  # same instance

    def test_all_resources_accessible(self):
        with PoliceAPI(cache_ttl=None) as api:
            assert api.crimes is not None
            assert api.stop_search is not None
            assert api.forces is not None
            assert api.neighbourhoods is not None
            assert api.availability is not None


class TestAsyncClient:
    async def test_cache_hit(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            async with AsyncPoliceAPI(cache_ttl=60) as api:
                await api.crimes.last_updated()
                await api.crimes.last_updated()
        assert route.call_count == 1

    async def test_timeout_raises(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(side_effect=httpx.TimeoutException("timeout"))
            async with AsyncPoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPITimeoutError):
                    await api.crimes.last_updated()

    async def test_http_error_raises(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(side_effect=httpx.HTTPError("connection failed"))
            async with AsyncPoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIError):
                    await api.crimes.last_updated()

    async def test_invalid_json_raises(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, content=b"not json{{{")
            )
            async with AsyncPoliceAPI(max_retries=0) as api:
                with pytest.raises(PoliceAPIResponseError):
                    await api.crimes.last_updated()

    async def test_server_error_retried(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(return_value=Response(500))
            with patch("asyncio.sleep", new_callable=AsyncMock):
                async with AsyncPoliceAPI(max_retries=1) as api:
                    with pytest.raises(PoliceAPIServerError):
                        await api.crimes.last_updated()
        assert route.call_count == 2

    async def test_retry_uses_retry_after_header(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(429, headers={"Retry-After": "1"})
            )
            with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
                async with AsyncPoliceAPI(max_retries=1) as api:
                    with pytest.raises(PoliceAPIRateLimitError):
                        await api.crimes.last_updated()
        mock_sleep.assert_called_once_with(1.0)

    async def test_clear_cache(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            async with AsyncPoliceAPI(cache_ttl=60) as api:
                await api.crimes.last_updated()
                api.clear_cache()
                await api.crimes.last_updated()
        assert route.call_count == 2
