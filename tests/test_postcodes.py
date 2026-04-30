"""Tests for the PostcodesIO geocoding client."""

import httpx
import pytest
import respx
from httpx import Response

from uk_police_api import AsyncPostcodesIO, GeocodedPostcode, PostcodesIO
from uk_police_api.exceptions import (
    PoliceAPIError,
    PoliceAPINotFoundError,
    PoliceAPIResponseError,
    PoliceAPITimeoutError,
)

POSTCODES_BASE = "https://api.postcodes.io"

POSTCODE_RESULT = {
    "postcode": "SE1 1BP",
    "latitude": 51.503541,
    "longitude": -0.083248,
    "region": "London",
    "admin_district": "Southwark",
    "admin_ward": "London Bridge & West Bermondsey",
    "parliamentary_constituency": "Bermondsey and Old Southwark",
    "country": "England",
    "pfa": "Metropolitan Police",
}


class TestPostcodesIOLookup:
    def test_lookup(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(
                return_value=Response(200, json={"status": 200, "result": POSTCODE_RESULT})
            )
            with PostcodesIO() as geo:
                loc = geo.lookup("SE1 1BP")

        assert isinstance(loc, GeocodedPostcode)
        assert loc.postcode == "SE1 1BP"
        assert loc.latitude == 51.503541
        assert loc.longitude == -0.083248
        assert loc.region == "London"
        assert loc.admin_district == "Southwark"
        assert loc.pfa == "Metropolitan Police"

    def test_lookup_normalises_spaces(self):
        """Spaces in postcodes are stripped before the request."""
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            route = router.get("/postcodes/SE11BP").mock(
                return_value=Response(200, json={"status": 200, "result": POSTCODE_RESULT})
            )
            with PostcodesIO() as geo:
                geo.lookup("se1 1bp")  # lowercase + space
        assert route.called

    def test_lookup_invalid_postcode(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/INVALID").mock(return_value=Response(404))
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPINotFoundError):
                    geo.lookup("INVALID")

    def test_bulk_lookup(self):
        payload = {
            "status": 200,
            "result": [
                {"query": "SE1 1BP", "result": POSTCODE_RESULT},
                {"query": "INVALID", "result": None},
            ],
        }
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(return_value=Response(200, json=payload))
            with PostcodesIO() as geo:
                results = geo.bulk_lookup(["SE1 1BP", "INVALID"])

        assert len(results) == 2
        assert isinstance(results[0], GeocodedPostcode)
        assert results[0].latitude == 51.503541
        assert results[1] is None

    def test_bulk_lookup_too_many_raises(self):
        with PostcodesIO() as geo:
            with pytest.raises(ValueError, match="100"):
                geo.bulk_lookup(["X"] * 101)

    def test_lookup_timeout(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(
                side_effect=httpx.TimeoutException("timed out")
            )
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPITimeoutError):
                    geo.lookup("SE1 1BP")

    def test_lookup_http_error(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(
                side_effect=httpx.ConnectError("connection refused")
            )
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPIError):
                    geo.lookup("SE1 1BP")

    def test_lookup_non_200(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(return_value=Response(503))
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPIError):
                    geo.lookup("SE1 1BP")

    def test_lookup_invalid_json(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(
                return_value=Response(200, content=b"not json")
            )
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPIResponseError):
                    geo.lookup("SE1 1BP")

    def test_bulk_lookup_empty(self):
        with PostcodesIO() as geo:
            assert geo.bulk_lookup([]) == []

    def test_bulk_lookup_timeout(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(side_effect=httpx.TimeoutException("timed out"))
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPITimeoutError):
                    geo.bulk_lookup(["SE1 1BP"])

    def test_bulk_lookup_http_error(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(
                side_effect=httpx.ConnectError("connection refused")
            )
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPIError):
                    geo.bulk_lookup(["SE1 1BP"])

    def test_bulk_lookup_non_200(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(return_value=Response(503))
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPIError):
                    geo.bulk_lookup(["SE1 1BP"])

    def test_bulk_lookup_invalid_json(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(return_value=Response(200, content=b"not json"))
            with PostcodesIO() as geo:
                with pytest.raises(PoliceAPIResponseError):
                    geo.bulk_lookup(["SE1 1BP"])

    def test_repr(self):
        loc = GeocodedPostcode(POSTCODE_RESULT)
        assert "SE1 1BP" in repr(loc)
        assert "51.503541" in repr(loc)


class TestAsyncPostcodesIO:
    async def test_async_lookup(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(
                return_value=Response(200, json={"status": 200, "result": POSTCODE_RESULT})
            )
            async with AsyncPostcodesIO() as geo:
                loc = await geo.lookup("SE1 1BP")
        assert loc.latitude == 51.503541

    async def test_async_lookup_not_found(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/INVALID").mock(return_value=Response(404))
            async with AsyncPostcodesIO() as geo:
                with pytest.raises(PoliceAPINotFoundError):
                    await geo.lookup("INVALID")

    async def test_async_lookup_non_200(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(return_value=Response(503))
            async with AsyncPostcodesIO() as geo:
                with pytest.raises(PoliceAPIError):
                    await geo.lookup("SE1 1BP")

    async def test_async_lookup_timeout(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(
                side_effect=httpx.TimeoutException("timed out")
            )
            async with AsyncPostcodesIO() as geo:
                with pytest.raises(PoliceAPITimeoutError):
                    await geo.lookup("SE1 1BP")

    async def test_async_lookup_invalid_json(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.get("/postcodes/SE11BP").mock(
                return_value=Response(200, content=b"not json")
            )
            async with AsyncPostcodesIO() as geo:
                with pytest.raises(PoliceAPIResponseError):
                    await geo.lookup("SE1 1BP")

    async def test_async_bulk_lookup(self):
        payload = {
            "status": 200,
            "result": [
                {"query": "SE1 1BP", "result": POSTCODE_RESULT},
                {"query": "INVALID", "result": None},
            ],
        }
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(return_value=Response(200, json=payload))
            async with AsyncPostcodesIO() as geo:
                results = await geo.bulk_lookup(["SE1 1BP", "INVALID"])
        assert len(results) == 2
        assert isinstance(results[0], GeocodedPostcode)
        assert results[0].latitude == 51.503541
        assert results[1] is None

    async def test_async_bulk_lookup_empty(self):
        async with AsyncPostcodesIO() as geo:
            assert await geo.bulk_lookup([]) == []

    async def test_async_bulk_lookup_too_many(self):
        async with AsyncPostcodesIO() as geo:
            with pytest.raises(ValueError, match="100"):
                await geo.bulk_lookup(["X"] * 101)

    async def test_async_bulk_lookup_non_200(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(return_value=Response(503))
            async with AsyncPostcodesIO() as geo:
                with pytest.raises(PoliceAPIError):
                    await geo.bulk_lookup(["SE1 1BP"])

    async def test_async_bulk_lookup_timeout(self):
        with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
            router.post("/postcodes").mock(side_effect=httpx.TimeoutException("timed out"))
            async with AsyncPostcodesIO() as geo:
                with pytest.raises(PoliceAPITimeoutError):
                    await geo.bulk_lookup(["SE1 1BP"])
