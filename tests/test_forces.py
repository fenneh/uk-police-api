"""Tests for the forces resource."""

import respx
from httpx import Response

from uk_police_api import PoliceAPI
from uk_police_api.models import Force, ForceLink, ForceOfficer

BASE = "https://data.police.uk/api"

FORCE_FIXTURE = {
    "id": "metropolitan",
    "name": "Metropolitan Police Service",
    "description": "Policing London.",
    "url": "http://www.met.police.uk/",
    "telephone": "101",
    "engagement_methods": [
        {"url": "http://twitter.com/metpoliceuk", "description": "Follow us", "title": "Twitter"}
    ],
}

FORCE_LINK_FIXTURE = {"id": "metropolitan", "name": "Metropolitan Police Service"}

OFFICER_FIXTURE = {
    "name": "Jane Smith",
    "rank": "Commissioner",
    "bio": "Joined in 2005.",
    "contact_details": {"email": "jane.smith@met.police.uk"},
}


class TestForcesList:
    def test_list(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/forces").mock(return_value=Response(200, json=[FORCE_LINK_FIXTURE]))
            with PoliceAPI(cache_ttl=None) as api:
                forces = api.forces.list()
        assert len(forces) == 1
        assert isinstance(forces[0], ForceLink)
        assert forces[0].id == "metropolitan"


class TestForcesGet:
    def test_get(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/forces/metropolitan").mock(
                return_value=Response(200, json=FORCE_FIXTURE)
            )
            with PoliceAPI(cache_ttl=None) as api:
                force = api.forces.get("metropolitan")
        assert isinstance(force, Force)
        assert force.id == "metropolitan"
        assert force.telephone == "101"
        assert len(force.engagement_methods) == 1


class TestForcesPeople:
    def test_people(self):
        with respx.mock(base_url=BASE, assert_all_called=False) as router:
            router.get("/forces/metropolitan/people").mock(
                return_value=Response(200, json=[OFFICER_FIXTURE])
            )
            with PoliceAPI(cache_ttl=None) as api:
                officers = api.forces.people("metropolitan")
        assert len(officers) == 1
        assert isinstance(officers[0], ForceOfficer)
        assert officers[0].name == "Jane Smith"
        assert officers[0].rank == "Commissioner"
