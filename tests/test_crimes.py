"""Tests for the crimes resource."""

import pytest
import respx
from httpx import Response

from uk_police_api import AsyncPoliceAPI, PoliceAPI
from uk_police_api.models import Crime, CrimeCategory, CrimeLastUpdated, CrimeWithOutcomes

BASE = "https://data.police.uk/api"
POSTCODES_BASE = "https://api.postcodes.io"


class TestCrimesStreetByPoint:
    def test_by_lat_lng(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-street/possession-of-weapons").mock(
                return_value=Response(200, json=[crime_data])
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
        assert route.calls[0].request.url.params["lat"] == "51.5074"
        assert route.calls[0].request.url.params["lng"] == "-0.1278"

    def test_by_location_id(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-street/all-crime").mock(
                return_value=Response(200, json=[crime_data])
            )
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.street(location_id=884227)
        assert route.calls[0].request.url.params["location_id"] == "884227"

    def test_with_date(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-street/all-crime").mock(return_value=Response(200, json=[]))
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.street(lat=51.5, lng=-0.1, date="2024-10")
        assert route.calls[0].request.url.params["date"] == "2024-10"

    def test_invalid_date_raises(self):
        with PoliceAPI(cache_ttl=None) as api:
            with pytest.raises(ValueError, match="YYYY-MM"):
                api.crimes.street(lat=51.5, lng=-0.1, date="2024-13")

    def test_default_category_is_all_crime(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-street/all-crime").mock(return_value=Response(200, json=[]))
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.street(lat=51.5, lng=-0.1)
        assert route.called

    def test_returns_empty_list_on_no_results(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/all-crime").mock(return_value=Response(200, json=[]))
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.street(lat=51.5, lng=-0.1)
        assert crimes == []


class TestCrimesStreetByPolygon:
    def test_by_polygon_get(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-street/all-crime").mock(return_value=Response(200, json=[]))
            poly = [(51.515, -0.141), (51.515, -0.131), (51.507, -0.131), (51.507, -0.141)]
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.street(poly=poly)
        assert "poly" in route.calls[0].request.url.params

    def test_by_polygon_post_for_large_polygon(self, crime_data):
        """Polygons exceeding URL length threshold must use POST."""
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            from uk_police_api.utils import circle_polygon

            poly = circle_polygon(51.5, -0.1, radius_km=50, num_points=200)
            route = router.post("/crimes-street/all-crime").mock(
                return_value=Response(200, json=[crime_data])
            )
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.street(poly=poly)
        assert route.called
        assert len(crimes) == 1

    def test_poly_and_postcode_mutually_exclusive(self):
        with PoliceAPI(cache_ttl=None) as api:
            with pytest.raises(ValueError, match="postcode or poly"):
                api.crimes.street(
                    poly=[(51.5, -0.1), (51.6, -0.1), (51.6, -0.2)],
                    postcode="SW1A 1AA",
                )


class TestCrimesStreetByPostcode:
    def test_postcode_geocoded_and_used_as_polygon(self, crime_data, postcode_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as police_router:
            with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as pc_router:
                pc_route = pc_router.get("/postcodes/SE17PB").mock(
                    return_value=Response(200, json={"status": 200, "result": postcode_data})
                )
                police_router.get("/crimes-street/possession-of-weapons").mock(
                    return_value=Response(200, json=[crime_data])
                )
                with PoliceAPI(cache_ttl=None) as api:
                    crimes = api.crimes.street(
                        "possession-of-weapons",
                        postcode="SE1 7PB",
                        radius_km=1,
                    )
        assert len(crimes) == 1
        assert pc_route.called

    def test_postcode_normalised_before_lookup(self, postcode_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as police_router:
            with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as pc_router:
                route = pc_router.get("/postcodes/SE17PB").mock(
                    return_value=Response(200, json={"status": 200, "result": postcode_data})
                )
                police_router.get("/crimes-street/all-crime").mock(
                    return_value=Response(200, json=[])
                )
                with PoliceAPI(cache_ttl=None) as api:
                    api.crimes.street(postcode="se1 7pb", radius_km=0.5)
        assert route.called  # lowercase + space normalised to SE17PB


class TestCrimesAtLocation:
    def test_at_location_by_coords(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-at-location").mock(
                return_value=Response(200, json=[crime_data])
            )
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.at_location(lat=51.5074, lng=-0.1278)
        assert len(crimes) == 1
        assert "lat" in route.calls[0].request.url.params

    def test_at_location_by_id(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-at-location").mock(
                return_value=Response(200, json=[crime_data])
            )
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.at_location(location_id=884227)
        assert route.calls[0].request.url.params["location_id"] == "884227"


class TestCrimesNoLocation:
    def test_no_location(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crimes-no-location").mock(
                return_value=Response(200, json=[crime_data])
            )
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.no_location("possession-of-weapons", "metropolitan")
        assert len(crimes) == 1
        assert route.calls[0].request.url.params["force"] == "metropolitan"
        assert route.calls[0].request.url.params["category"] == "possession-of-weapons"


class TestCrimesCategories:
    def test_all_categories(self):
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
        weapon_cats = [c for c in cats if "weapon" in c.name.lower()]
        assert len(weapon_cats) == 1

    def test_categories_with_date(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            route = router.get("/crime-categories").mock(return_value=Response(200, json=[]))
            with PoliceAPI(cache_ttl=None) as api:
                api.crimes.categories(date="2024-10")
        assert route.calls[0].request.url.params["date"] == "2024-10"


class TestCrimesLastUpdated:
    def test_last_updated(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-last-updated").mock(
                return_value=Response(200, json={"date": "2026-01-01"})
            )
            with PoliceAPI(cache_ttl=None) as api:
                result = api.crimes.last_updated()
        assert isinstance(result, CrimeLastUpdated)
        assert result.date == "2026-01-01"


class TestOutcomesForCrime:
    def test_outcomes_for_crime(self, crime_data):
        raw = {
            "crime": crime_data,
            "outcomes": [
                {
                    "category": {"code": "under-investigation", "name": "Under investigation"},
                    "date": "2024-11",
                    "person_id": None,
                }
            ],
        }
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/outcomes-for-crime/abc123").mock(return_value=Response(200, json=raw))
            with PoliceAPI(cache_ttl=None) as api:
                result = api.crimes.outcomes_for_crime("abc123")
        assert isinstance(result, CrimeWithOutcomes)
        assert len(result.outcomes) == 1
        assert result.outcomes[0].category.code == "under-investigation"
        assert result.outcomes[0].date == "2024-11"

    def test_outcomes_empty(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/outcomes-for-crime/abc").mock(
                return_value=Response(200, json={"crime": crime_data, "outcomes": []})
            )
            with PoliceAPI(cache_ttl=None) as api:
                result = api.crimes.outcomes_for_crime("abc")
        assert result.outcomes == []


class TestStreetMonths:
    def test_street_months_deduplicates(self, crime_data):
        """Same persistent_id appearing across months must not be duplicated."""
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/all-crime").mock(
                return_value=Response(200, json=[crime_data])
            )
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.street_months(months=3, lat=51.5, lng=-0.1)
        assert len(crimes) == 1  # same persistent_id → deduplicated

    def test_street_months_combines_months(self):
        crime_a = {
            "category": "drugs",
            "persistent_id": "aaa" + "x" * 61,
            "id": 1,
            "month": "2024-10",
            "context": "",
        }
        crime_b = {
            "category": "drugs",
            "persistent_id": "bbb" + "x" * 61,
            "id": 2,
            "month": "2024-09",
            "context": "",
        }
        call_count = 0

        def handler(request):
            nonlocal call_count
            result = [crime_a] if call_count == 0 else ([crime_b] if call_count == 1 else [])
            call_count += 1
            return Response(200, json=result)

        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/all-crime").mock(side_effect=handler)
            with PoliceAPI(cache_ttl=None) as api:
                crimes = api.crimes.street_months(months=3, lat=51.5, lng=-0.1)
        assert len(crimes) == 2

    def test_street_months_skips_failed_months(self):
        """Months with no data (e.g. 503) should be skipped, not crash."""
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/all-crime").mock(return_value=Response(503))
            with PoliceAPI(cache_ttl=None, max_retries=0) as api:
                crimes = api.crimes.street_months(months=2, lat=51.5, lng=-0.1)
        assert crimes == []


class TestAsyncCrimes:
    async def test_async_street(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/possession-of-weapons").mock(
                return_value=Response(200, json=[crime_data])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                crimes = await api.crimes.street("possession-of-weapons", lat=51.5074, lng=-0.1278)
        assert len(crimes) == 1
        assert crimes[0].category == "possession-of-weapons"

    async def test_async_categories(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crime-categories").mock(
                return_value=Response(200, json=[{"url": "all-crime", "name": "All crime"}])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                cats = await api.crimes.categories()
        assert len(cats) == 1

    async def test_async_street_months(self, crime_data):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street/all-crime").mock(
                return_value=Response(200, json=[crime_data])
            )
            async with AsyncPoliceAPI(cache_ttl=None) as api:
                crimes = await api.crimes.street_months(months=2, lat=51.5, lng=-0.1)
        assert len(crimes) == 1  # deduplicated across 2 months


class TestIntegration:
    @pytest.mark.integration
    def test_real_categories(self):
        with PoliceAPI() as api:
            cats = api.crimes.categories()
        assert len(cats) > 10
        slugs = [c.url for c in cats]
        assert "possession-of-weapons" in slugs
        assert "all-crime" in slugs

    @pytest.mark.integration
    def test_real_last_updated(self):
        with PoliceAPI() as api:
            result = api.crimes.last_updated()
        assert result.date is not None

    @pytest.mark.integration
    def test_real_street_crimes(self):
        with PoliceAPI() as api:
            updated = api.crimes.last_updated()
            month = updated.date[:7]
            crimes = api.crimes.street(
                "possession-of-weapons", lat=51.5074, lng=-0.1278, date=month
            )
        assert isinstance(crimes, list)
        if crimes:
            assert crimes[0].category == "possession-of-weapons"
