"""Tests for the crimes resource."""

import pytest
import respx
from httpx import Response

from uk_police_api import AsyncPoliceAPI, PoliceAPI
from uk_police_api.models import Crime, CrimeCategory, CrimeLastUpdated, CrimeWithOutcomes

BASE = "https://data.police.uk/api"

CRIME_FIXTURE = {
    "category": "possession-of-weapons",
    "persistent_id": "abc123" + "x" * 58,
    "id": 1001,
    "month": "2024-10",
    "location_type": "Force",
    "location": {
        "latitude": "51.507",
        "longitude": "-0.127",
        "street": {"id": 999, "name": "On or near High Street"},
    },
    "context": "",
    "outcome_status": {"category": "Under investigation", "date": "2024-11"},
}


class TestCrimesStreet:
    def test_by_point(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/possession-of-weapons").mock(
                return_value=Response(200, json=[CRIME_FIXTURE])
            )
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.street("possession-of-weapons", lat=51.5074, lng=-0.1278)

        assert len(crimes) == 1
        c = crimes[0]
        assert isinstance(c, Crime)
        assert c.category == "possession-of-weapons"
        assert c.month == "2024-10"
        assert c.location is not None
        assert c.location.latitude == 51.507
        assert c.location.street is not None
        assert c.location.street.name == "On or near High Street"
        assert c.outcome_status is not None
        assert c.outcome_status.category == "Under investigation"

    def test_by_polygon(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/all-crime").mock(
                return_value=Response(200, json=[CRIME_FIXTURE])
            )
            poly = [(51.515, -0.141), (51.515, -0.131), (51.507, -0.131), (51.507, -0.141)]
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.street(poly=poly)
        assert len(crimes) == 1

    def test_with_date(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-street/all-crime").mock(
                return_value=Response(200, json=[])
            )
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.street(lat=51.5, lng=-0.1, date="2024-10")
        assert route.calls[0].request.url.params["date"] == "2024-10"

    def test_invalid_date_raises(self):
        with PoliceAPI(cache_ttl=None) as api:
            with pytest.raises(ValueError):
                api.crimes.street(lat=51.5, lng=-0.1, date="2024-13")


class TestCrimesCategories:
    def test_categories(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-categories").mock(
                return_value=Response(
                    200,
                    json=[
                        {"url": "possession-of-weapons", "name": "Possession of weapons"},
                        {"url": "all-crime", "name": "All crime"},
                    ],
                )
            )
            with PoliceAPI(cache_ttl=None) as api:
                cats = api.crimes.categories()
        assert len(cats) == 2
        assert isinstance(cats[0], CrimeCategory)
        assert cats[0].url == "possession-of-weapons"


class TestCrimesLastUpdated:
    def test_last_updated(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2024-10"})
            )
            with PoliceAPI(cache_ttl=None) as api:
                result = api.crimes.last_updated()
        assert isinstance(result, CrimeLastUpdated)
        assert result.date == "2024-10"


class TestCrimesNoLocation:
    def test_no_location(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-no-location").mock(
                return_value=Response(200, json=[CRIME_FIXTURE])
            )
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.no_location("possession-of-weapons", "metropolitan")
        assert len(crimes) == 1


class TestOutcomesForCrime:
    def test_outcomes_for_crime(self):
        raw = {
            "crime": CRIME_FIXTURE,
            "outcomes": [
                {
                    "category": {"code": "under-investigation", "name": "Under investigation"},
                    "date": "2024-11",
                    "person_id": None,
                }
            ],
        }
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/outcomes-for-crime/abc123").mock(
                return_value=Response(200, json=raw)
            )
            with PoliceAPI(cache_ttl=None) as api:
                result = api.crimes.outcomes_for_crime("abc123")
        assert isinstance(result, CrimeWithOutcomes)
        assert len(result.outcomes) == 1
        assert result.outcomes[0].category.code == "under-investigation"


class TestAsyncCrimes:
    async def test_async_street(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/possession-of-weapons").mock(
                return_value=Response(200, json=[CRIME_FIXTURE])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                crimes = await api.crimes.street(
                    "possession-of-weapons", lat=51.5074, lng=-0.1278
                )
        assert len(crimes) == 1
        assert crimes[0].category == "possession-of-weapons"
