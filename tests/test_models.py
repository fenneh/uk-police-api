"""Tests for Pydantic model validation, coercion, and edge cases."""


from uk_police_api.models.availability import AvailabilityDate
from uk_police_api.models.common import Coordinates, Location
from uk_police_api.models.crime import (
    Crime,
    CrimeCategory,
    CrimeOutcome,
    CrimeWithOutcomes,
)
from uk_police_api.models.force import Force, ForceLink, ForceOfficer
from uk_police_api.models.neighbourhood import (
    ContactDetails,
    LocatedNeighbourhood,
    Neighbourhood,
    NeighbourhoodPriority,
)
from uk_police_api.models.stop_search import StopSearch


class TestLocationCoercion:
    """The API sends lat/lng as strings — models must coerce them to float."""

    def test_string_coords_coerced_to_float(self):
        loc = Location.model_validate(
            {"latitude": "51.507", "longitude": "-0.127", "street": {"id": 1, "name": "High St"}}
        )
        assert loc.latitude == 51.507
        assert loc.longitude == -0.127
        assert isinstance(loc.latitude, float)

    def test_none_coords_allowed(self):
        loc = Location.model_validate({"latitude": None, "longitude": None})
        assert loc.latitude is None
        assert loc.longitude is None

    def test_empty_string_coords_become_none(self):
        loc = Location.model_validate({"latitude": "", "longitude": ""})
        assert loc.latitude is None
        assert loc.longitude is None

    def test_numeric_coords_pass_through(self):
        loc = Location.model_validate({"latitude": 51.5, "longitude": -0.1})
        assert loc.latitude == 51.5

    def test_coordinates_model_coerces(self):
        c = Coordinates.model_validate({"latitude": "51.25", "longitude": "-0.56"})
        assert c.latitude == 51.25
        assert c.longitude == -0.56


class TestExtraFieldsIgnored:
    """API may add new fields — models must not raise on unknown keys."""

    def test_crime_ignores_unknown_fields(self):
        data = {
            "category": "drugs",
            "persistent_id": "x" * 64,
            "id": 1,
            "month": "2024-10",
            "new_unknown_field": "some_value",
        }
        crime = Crime.model_validate(data)
        assert crime.category == "drugs"
        assert not hasattr(crime, "new_unknown_field")

    def test_stop_search_ignores_unknown_fields(self):
        data = {
            "type": "Person search",
            "datetime": "2024-10-01T12:00:00",
            "future_api_field": True,
        }
        stop = StopSearch.model_validate(data)
        assert stop.type == "Person search"

    def test_contact_details_allows_extra_social_fields(self):
        """ContactDetails uses extra='allow' for unpredictable social media fields."""
        cd = ContactDetails.model_validate(
            {"email": "test@example.com", "bluesky": "https://bsky.app/test"}
        )
        assert cd.email == "test@example.com"
        assert cd.model_extra is not None
        assert "bluesky" in cd.model_extra


class TestCrimeModel:
    def test_full_crime(self, crime_data):
        c = Crime.model_validate(crime_data)
        assert c.category == "possession-of-weapons"
        assert c.month == "2024-10"
        assert c.location is not None
        assert c.location.latitude == 51.507
        assert c.location.street is not None
        assert c.location.street.name == "On or near High Street"
        assert c.outcome_status is not None
        assert c.outcome_status.category == "Under investigation"

    def test_crime_no_location(self, crime_no_location_data):
        c = Crime.model_validate(crime_no_location_data)
        assert c.location is None
        assert c.outcome_status is None

    def test_crime_context_defaults_empty(self):
        data = {
            "category": "drugs",
            "persistent_id": "x" * 64,
            "id": 1,
            "month": "2024-10",
        }
        c = Crime.model_validate(data)
        assert c.context == ""

    def test_crime_with_outcomes(self, crime_data):
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
        result = CrimeWithOutcomes(
            crime=Crime.model_validate(raw["crime"]),
            outcomes=[CrimeOutcome.model_validate(o) for o in raw["outcomes"]],
        )
        assert len(result.outcomes) == 1
        assert result.outcomes[0].category.code == "under-investigation"

    def test_crime_category(self):
        cat = CrimeCategory.model_validate(
            {"url": "possession-of-weapons", "name": "Possession of weapons"}
        )
        assert cat.url == "possession-of-weapons"
        assert cat.name == "Possession of weapons"


class TestStopSearchModel:
    def test_full_stop(self, stop_data):
        s = StopSearch.model_validate(stop_data)
        assert s.type == "Person search"
        assert s.gender == "Male"
        assert s.object_of_search == "Controlled drugs"
        assert s.location is not None
        assert s.location.latitude == 51.507
        assert s.operation is False  # bool, not string

    def test_operation_is_bool(self):
        """The API returns operation as False (bool), not None or string."""
        s = StopSearch.model_validate(
            {"type": "Person search", "datetime": "2024-10-01", "operation": False}
        )
        assert s.operation is False

    def test_minimal_stop(self):
        s = StopSearch.model_validate({"type": "Vehicle search", "datetime": "2024-01-01"})
        assert s.type == "Vehicle search"
        assert s.gender is None
        assert s.outcome is None


class TestForceModel:
    def test_force(self, force_data):
        f = Force.model_validate(force_data)
        assert f.id == "metropolitan"
        assert f.telephone == "101"
        assert len(f.engagement_methods) == 1
        assert f.engagement_methods[0].title == "Twitter"

    def test_force_link(self):
        fl = ForceLink.model_validate({"id": "surrey", "name": "Surrey Police"})
        assert fl.id == "surrey"

    def test_force_officer_defaults(self):
        o = ForceOfficer.model_validate({"name": "Jane Smith", "rank": "Commissioner"})
        assert o.bio is None
        assert o.contact_details == {}

    def test_force_engagement_methods_default_empty(self):
        f = Force.model_validate({"id": "surrey", "name": "Surrey Police"})
        assert f.engagement_methods == []


class TestNeighbourhoodModel:
    def test_neighbourhood(self, neighbourhood_data):
        n = Neighbourhood.model_validate(neighbourhood_data)
        assert n.id == "00BK"
        assert n.name == "Burpham"
        assert n.centre is not None
        assert n.centre.latitude == 51.25
        assert n.contact_details.email == "team@surrey.pnn.police.uk"

    def test_neighbourhood_population_int(self):
        """API sometimes returns population as int."""
        n = Neighbourhood.model_validate({"id": "X", "name": "Test", "population": 0})
        assert n.population == 0

    def test_neighbourhood_population_string(self):
        n = Neighbourhood.model_validate({"id": "X", "name": "Test", "population": "12340"})
        assert n.population == "12340"

    def test_priority_defaults(self):
        p = NeighbourhoodPriority.model_validate({"issue": "Speeding on main road"})
        assert p.issue == "Speeding on main road"
        assert p.action is None
        assert p.issue_date is None

    def test_located_neighbourhood(self):
        loc = LocatedNeighbourhood.model_validate({"force": "surrey", "neighbourhood": "00BK"})
        assert loc.force == "surrey"
        assert loc.neighbourhood == "00BK"


class TestAvailabilityModel:
    def test_hyphenated_field_alias(self):
        """API returns 'stop-and-search' (hyphenated) — must map to stop_and_search."""
        d = AvailabilityDate.model_validate(
            {"date": "2024-10", "stop-and-search": ["metropolitan", "surrey"]}
        )
        assert d.date == "2024-10"
        assert "metropolitan" in d.stop_and_search

    def test_missing_stop_and_search_defaults_empty(self):
        d = AvailabilityDate.model_validate({"date": "2024-10"})
        assert d.stop_and_search == []
