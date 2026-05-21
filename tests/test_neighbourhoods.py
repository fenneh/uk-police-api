"""Tests for the neighbourhoods resource."""

import respx
from httpx import Response

from uk_police_api import AsyncPoliceAPI, PoliceAPI
from uk_police_api.models import (
    Coordinates,
    ForceOfficer,
    LocatedNeighbourhood,
    Neighbourhood,
    NeighbourhoodEvent,
    NeighbourhoodLink,
    NeighbourhoodPriority,
)

BASE = "https://data.police.uk/api"

NEIGHBOURHOOD_FIXTURE = {
    "id": "00BK",
    "name": "Burpham",
    "description": "Burpham ward.",
    "url_force": "http://www.surrey.police.uk/",
    "contact_details": {"email": "team@surrey.pnn.police.uk", "telephone": "101"},
    "centre": {"latitude": "51.25", "longitude": "-0.56"},
    "links": [],
    "locations": [],
    "population": "12340",
}


class TestNeighbourhoodsList:
    def test_list(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/neighbourhoods").mock(
                return_value=Response(200, json=[{"id": "00BK", "name": "Burpham"}])
            )
            with PoliceAPI(cache_ttl=None) as api:
                neighbourhoods = api.neighbourhoods.list("surrey")
        assert len(neighbourhoods) == 1
        assert isinstance(neighbourhoods[0], NeighbourhoodLink)
        assert neighbourhoods[0].id == "00BK"


class TestNeighbourhoodsGet:
    def test_get(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK").mock(return_value=Response(200, json=NEIGHBOURHOOD_FIXTURE))
            with PoliceAPI(cache_ttl=None) as api:
                n = api.neighbourhoods.get("surrey", "00BK")
        assert isinstance(n, Neighbourhood)
        assert n.name == "Burpham"
        assert n.centre is not None
        assert n.centre.latitude == 51.25
        assert n.contact_details.email == "team@surrey.pnn.police.uk"


class TestNeighbourhoodsBoundary:
    def test_boundary(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/boundary").mock(
                return_value=Response(
                    200,
                    json=[
                        {"latitude": "51.25", "longitude": "-0.56"},
                        {"latitude": "51.26", "longitude": "-0.55"},
                    ],
                )
            )
            with PoliceAPI(cache_ttl=None) as api:
                boundary = api.neighbourhoods.boundary("surrey", "00BK")
        assert len(boundary) == 2
        assert boundary[0].latitude == 51.25


class TestNeighbourhoodsEvents:
    def test_events(self):
        event = {
            "title": "Coffee morning",
            "description": "Monthly coffee morning.",
            "address": "Village Hall",
            "type": "meeting",
            "start_date": "2024-11-01T10:00:00",
            "end_date": "2024-11-01T11:00:00",
            "contact_details": {},
        }
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/events").mock(return_value=Response(200, json=[event]))
            with PoliceAPI(cache_ttl=None) as api:
                events = api.neighbourhoods.events("surrey", "00BK")
        assert len(events) == 1
        assert isinstance(events[0], NeighbourhoodEvent)
        assert events[0].title == "Coffee morning"


class TestNeighbourhoodsPriorities:
    def test_priorities(self):
        priority = {
            "issue": "Speeding on main road",
            "issue_date": "2024-01-15T00:00:00",
            "action": "Speed patrols increased.",
            "action_date": "2024-02-01T00:00:00",
        }
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/priorities").mock(return_value=Response(200, json=[priority]))
            with PoliceAPI(cache_ttl=None) as api:
                priorities = api.neighbourhoods.priorities("surrey", "00BK")
        assert len(priorities) == 1
        assert isinstance(priorities[0], NeighbourhoodPriority)
        assert priorities[0].issue == "Speeding on main road"


class TestNeighbourhoodsPeople:
    def test_people(self):
        officer = {
            "name": "PC Alice Green",
            "rank": "Constable",
            "bio": None,
            "contact_details": {},
        }
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/people").mock(return_value=Response(200, json=[officer]))
            with PoliceAPI(cache_ttl=None) as api:
                people = api.neighbourhoods.people("surrey", "00BK")
        assert len(people) == 1
        assert isinstance(people[0], ForceOfficer)
        assert people[0].name == "PC Alice Green"


class TestNeighbourhoodsLocate:
    def test_locate(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/locate-neighbourhood").mock(
                return_value=Response(200, json={"force": "surrey", "neighbourhood": "00BK"})
            )
            with PoliceAPI(cache_ttl=None) as api:
                result = api.neighbourhoods.locate(lat=51.25, lng=-0.56)
        assert isinstance(result, LocatedNeighbourhood)
        assert result.force == "surrey"
        assert result.neighbourhood == "00BK"


OFFICER_FIXTURE = {
    "name": "PC Alice Green",
    "rank": "Constable",
    "bio": None,
    "contact_details": {},
}

BOUNDARY_FIXTURE = [
    {"latitude": "51.25", "longitude": "-0.56"},
    {"latitude": "51.26", "longitude": "-0.55"},
]

EVENT_FIXTURE = {
    "title": "Coffee morning",
    "description": "Monthly coffee morning.",
    "address": "Village Hall",
    "type": "meeting",
    "start_date": "2024-11-01T10:00:00",
    "end_date": "2024-11-01T11:00:00",
    "contact_details": {},
}

PRIORITY_FIXTURE = {
    "issue": "Speeding on main road",
    "issue_date": "2024-01-15T00:00:00",
    "action": "Speed patrols increased.",
    "action_date": "2024-02-01T00:00:00",
}


class TestAsyncNeighbourhoods:
    async def test_list(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/neighbourhoods").mock(
                return_value=Response(200, json=[{"id": "00BK", "name": "Burpham"}])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                neighbourhoods = await api.neighbourhoods.list("surrey")
        assert len(neighbourhoods) == 1
        assert isinstance(neighbourhoods[0], NeighbourhoodLink)
        assert neighbourhoods[0].id == "00BK"

    async def test_get(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK").mock(return_value=Response(200, json=NEIGHBOURHOOD_FIXTURE))
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                n = await api.neighbourhoods.get("surrey", "00BK")
        assert isinstance(n, Neighbourhood)
        assert n.name == "Burpham"

    async def test_boundary(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/boundary").mock(
                return_value=Response(200, json=BOUNDARY_FIXTURE)
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                boundary = await api.neighbourhoods.boundary("surrey", "00BK")
        assert len(boundary) == 2
        assert isinstance(boundary[0], Coordinates)
        assert boundary[0].latitude == 51.25

    async def test_people(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/people").mock(
                return_value=Response(200, json=[OFFICER_FIXTURE])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                people = await api.neighbourhoods.people("surrey", "00BK")
        assert len(people) == 1
        assert isinstance(people[0], ForceOfficer)

    async def test_events(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/events").mock(
                return_value=Response(200, json=[EVENT_FIXTURE])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                events = await api.neighbourhoods.events("surrey", "00BK")
        assert len(events) == 1
        assert isinstance(events[0], NeighbourhoodEvent)
        assert events[0].title == "Coffee morning"

    async def test_priorities(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/surrey/00BK/priorities").mock(
                return_value=Response(200, json=[PRIORITY_FIXTURE])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                priorities = await api.neighbourhoods.priorities("surrey", "00BK")
        assert len(priorities) == 1
        assert isinstance(priorities[0], NeighbourhoodPriority)

    async def test_locate(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/locate-neighbourhood").mock(
                return_value=Response(200, json={"force": "surrey", "neighbourhood": "00BK"})
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                result = await api.neighbourhoods.locate(lat=51.25, lng=-0.56)
        assert isinstance(result, LocatedNeighbourhood)
        assert result.force == "surrey"
