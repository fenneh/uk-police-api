"""Shared fixtures for UK Police API tests."""

import pytest
import respx
from httpx import Response

BASE = "https://data.police.uk/api"


@pytest.fixture
def mock_api():
    """Activate respx mock router for all tests that use it."""
    with respx.mock(base_url=BASE, assert_all_called=False) as router:
        yield router
