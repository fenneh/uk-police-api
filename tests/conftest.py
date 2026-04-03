"""Shared fixtures for UK Police API tests."""

import pytest
import respx

BASE = "https://data.police.uk/api"
POSTCODES_BASE = "https://api.postcodes.io"

# --- Sample data fixtures ---


@pytest.fixture
def crime_data():
    return {
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


@pytest.fixture
def crime_no_location_data():
    return {
        "category": "drugs",
        "persistent_id": "yyy" + "z" * 61,
        "id": 1002,
        "month": "2024-10",
        "location_type": None,
        "location": None,
        "context": "",
        "outcome_status": None,
    }


@pytest.fixture
def stop_data():
    return {
        "type": "Person search",
        "involved_person": True,
        "datetime": "2024-10-15T14:00:00+00:00",
        "operation": False,
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


@pytest.fixture
def force_data():
    return {
        "id": "metropolitan",
        "name": "Metropolitan Police Service",
        "description": "Policing London.",
        "url": "http://www.met.police.uk/",
        "telephone": "101",
        "engagement_methods": [
            {
                "url": "http://twitter.com/metpoliceuk",
                "description": "Follow us",
                "title": "Twitter",
            }
        ],
    }


@pytest.fixture
def neighbourhood_data():
    return {
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


@pytest.fixture
def postcode_data():
    return {
        "postcode": "SE1 7PB",
        "latitude": 51.5025,
        "longitude": -0.119384,
        "region": "London",
        "admin_district": "Lambeth",
        "admin_ward": "Waterloo & South Bank",
        "parliamentary_constituency": "Bermondsey and Old Southwark",
        "country": "England",
        "pfa": "Metropolitan Police",
    }


@pytest.fixture
def mock_api():
    """Activate respx mock router for all tests that use it."""
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router


@pytest.fixture
def mock_postcodes():
    """Activate respx mock router for postcodes.io."""
    with respx.mock(base_url=POSTCODES_BASE, assert_all_called=False) as router:
        yield router
