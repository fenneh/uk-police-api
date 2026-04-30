"""Tests for the stop and search resource."""

import respx
from httpx import Response

from uk_police_api import AsyncPoliceAPI, PoliceAPI
from uk_police_api.models import StopSearch

BASE = "https://data.police.uk/api"

STOP_FIXTURE = {
    "type": "Person search",
    "involved_person": True,
    "datetime": "2024-10-15T14:00:00+00:00",
    "operation": None,
    "operation_name": None,
    "location": {
        "latitude": "51.507",
        "longitude": "-0.127",
        "street": {"id": 999, "name": "On or near High Street"},
    },
    "gender": "Male",
    "age_range": "18-24",
    "self_defined_ethnicity": "White - English/Welsh/Scottish/Northern Irish/British",
    "officer_defined_ethnicity": "White",
    "legislation": "Misuse of Drugs Act 1971 (section 23)",
    "object_of_search": "Controlled drugs",
    "outcome": "A no further action disposal",
    "outcome_linked_to_object_of_search": False,
    "removal_of_more_than_outer_clothing": False,
}


class TestStopSearchStreet:
    def test_by_point(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/stops-street").mock(return_value=Response(200, json=[STOP_FIXTURE]))
            with PoliceAPI(cache_ttl=None) as api:
                stops = api.stop_search.street(lat=51.5074, lng=-0.1278)
        assert len(stops) == 1
        s = stops[0]
        assert isinstance(s, StopSearch)
        assert s.type == "Person search"
        assert s.gender == "Male"
        assert s.object_of_search == "Controlled drugs"
        assert s.location is not None
        assert s.location.latitude == 51.507

    def test_by_polygon(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/stops-street").mock(return_value=Response(200, json=[STOP_FIXTURE]))
            poly = [(51.515, -0.141), (51.515, -0.131), (51.507, -0.131), (51.507, -0.141)]
            with PoliceAPI(cache_ttl=None) as api:
                stops = api.stop_search.street(poly=poly)
        assert len(stops) == 1


class TestStopSearchAtLocation:
    def test_at_location(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/stops-at-location").mock(
                return_value=Response(200, json=[STOP_FIXTURE])
            )
            with PoliceAPI(cache_ttl=None) as api:
                stops = api.stop_search.at_location(location_id=12345, date="2024-10")
        assert route.calls[0].request.url.params["location_id"] == "12345"
        assert len(stops) == 1


class TestStopSearchNoLocation:
    def test_no_location(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/stops-no-location").mock(
                return_value=Response(200, json=[STOP_FIXTURE])
            )
            with PoliceAPI(cache_ttl=None) as api:
                stops = api.stop_search.no_location("metropolitan", date="2024-10")
        assert route.calls[0].request.url.params["force"] == "metropolitan"
        assert len(stops) == 1


class TestStopSearchByForce:
    def test_by_force(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/stops-force").mock(return_value=Response(200, json=[STOP_FIXTURE]))
            with PoliceAPI(cache_ttl=None) as api:
                stops = api.stop_search.by_force("metropolitan", date="2024-10")
        assert route.calls[0].request.url.params["force"] == "metropolitan"
        assert len(stops) == 1


class TestAsyncStopSearch:
    async def test_street_by_point(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/stops-street").mock(return_value=Response(200, json=[STOP_FIXTURE]))
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                stops = await api.stop_search.street(lat=51.5074, lng=-0.1278)
        assert len(stops) == 1
        assert isinstance(stops[0], StopSearch)

    async def test_at_location(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/stops-at-location").mock(
                return_value=Response(200, json=[STOP_FIXTURE])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                stops = await api.stop_search.at_location(location_id=12345)
        assert route.calls[0].request.url.params["location_id"] == "12345"
        assert len(stops) == 1

    async def test_no_location(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/stops-no-location").mock(
                return_value=Response(200, json=[STOP_FIXTURE])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                stops = await api.stop_search.no_location("metropolitan", date="2024-10")
        assert route.calls[0].request.url.params["force"] == "metropolitan"
        assert len(stops) == 1

    async def test_by_force(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/stops-force").mock(return_value=Response(200, json=[STOP_FIXTURE]))
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                stops = await api.stop_search.by_force("metropolitan", date="2024-10")
        assert route.calls[0].request.url.params["force"] == "metropolitan"
        assert len(stops) == 1

    async def test_street_by_polygon(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/stops-street").mock(return_value=Response(200, json=[STOP_FIXTURE]))
            poly = [(51.515, -0.141), (51.515, -0.131), (51.507, -0.131), (51.507, -0.141)]
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                stops = await api.stop_search.street(poly=poly)
        assert len(stops) == 1
