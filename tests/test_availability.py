"""Tests for the availability resource."""

import respx
from httpx import Response

from uk_police_api import PoliceAPI
from uk_police_api.models import AvailabilityDate

BASE = "https://data.police.uk/api"


class TestAvailabilityDates:
    def test_dates(self):
        payload = [
            {"date": "2024-10", "stop-and-search": ["metropolitan", "thames-valley"]},
            {"date": "2024-09", "stop-and-search": ["metropolitan"]},
        ]
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/crimes-street-dates").mock(return_value=Response(200, json=payload))
            with PoliceAPI(cache_ttl=None) as api:
                dates = api.availability.dates()
        assert len(dates) == 2
        assert isinstance(dates[0], AvailabilityDate)
        assert dates[0].date == "2024-10"
        assert "metropolitan" in dates[0].stop_and_search
