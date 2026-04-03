# uk-police-api

[![PyPI](https://img.shields.io/pypi/v/uk-police-api)](https://pypi.org/project/uk-police-api/)
[![CI](https://github.com/fenneh/uk-police-api/actions/workflows/ci.yml/badge.svg)](https://github.com/fenneh/uk-police-api/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/uk-police-api)](https://pypi.org/project/uk-police-api/)
[![License](https://img.shields.io/pypi/l/uk-police-api)](https://github.com/fenneh/uk-police-api/blob/main/LICENSE)

Python client for the [UK Police Data API](https://data.police.uk/docs/). No authentication required.

## Installation

```bash
uv add uk-police-api
```

or with pip:

```bash
pip install uk-police-api
```

## Quick Start

```python
from uk_police_api import PoliceAPI

with PoliceAPI() as api:
    # Weapon possession crimes near a coordinate
    crimes = api.crimes.street("possession-of-weapons", lat=51.5074, lng=-0.1278)

    # All crime categories
    categories = api.crimes.categories()

    # Locate your neighbourhood
    area = api.neighbourhoods.locate(lat=51.5074, lng=-0.1278)
    neighbourhood = api.neighbourhoods.get(area.force, area.neighbourhood)
```

## Postcode Queries

Postcode-to-coordinate lookup is handled by [postcodes.io](https://postcodes.io) — a separate free API. Use `PostcodesIO` alongside `circle_polygon` to query by postcode and radius:

```python
from uk_police_api import PoliceAPI, PostcodesIO, circle_polygon

with PostcodesIO() as geo:          # calls postcodes.io
    loc = geo.lookup("SE1 7PB")
    print(loc.latitude, loc.longitude, loc.pfa)

with PoliceAPI() as api:
    poly = circle_polygon(loc.latitude, loc.longitude, radius_km=2)
    crimes = api.crimes.street("possession-of-weapons", poly=poly)
```

Or pass `postcode` and `radius_km` directly — the geocoding happens internally:

```python
with PoliceAPI() as api:
    crimes = api.crimes.street(
        "possession-of-weapons",
        postcode="SE1 7PB",
        radius_km=2,
    )
```

## Crimes

```python
with PoliceAPI() as api:
    # Street-level crimes — supply one of: lat+lng, poly, postcode+radius_km, location_id
    crimes = api.crimes.street("all-crime", lat=51.5074, lng=-0.1278)
    crimes = api.crimes.street("all-crime", lat=51.5074, lng=-0.1278, date="2024-10")
    crimes = api.crimes.street("possession-of-weapons", postcode="SW1A 1AA", radius_km=1)
    crimes = api.crimes.street("burglary", poly=[(51.5, -0.1), (51.5, -0.12), (51.49, -0.1)])

    # Multi-month query — deduplicates by persistent_id across months
    crimes = api.crimes.street_months("possession-of-weapons", months=5, postcode="SE1 7PB", radius_km=2)
    crimes = api.crimes.street_months("all-crime", months=3, lat=51.5074, lng=-0.1278)

    # Crimes at a specific mapped location
    crimes = api.crimes.at_location(lat=51.5074, lng=-0.1278)
    crimes = api.crimes.at_location(location_id=884227)

    # Crimes not mapped to a location
    crimes = api.crimes.no_location("all-crime", force="metropolitan")

    # Outcomes for crimes at a location
    outcomes = api.crimes.outcomes_at_location(lat=51.5074, lng=-0.1278)

    # Full case history for a specific crime
    result = api.crimes.outcomes_for_crime("590d68b69f872eb9683310b5...")
    print(result.crime.category, result.outcomes)

    # Metadata
    categories = api.crimes.categories()               # all crime categories
    categories = api.crimes.categories(date="2024-10") # categories for a specific month
    updated = api.crimes.last_updated()                # date of latest data
```

### Crime categories

| Slug | Name |
|---|---|
| `all-crime` | All crime |
| `anti-social-behaviour` | Anti-social behaviour |
| `bicycle-theft` | Bicycle theft |
| `burglary` | Burglary |
| `criminal-damage-arson` | Criminal damage and arson |
| `drugs` | Drugs |
| `other-theft` | Other theft |
| `possession-of-weapons` | Possession of weapons _(includes knife crime)_ |
| `public-order` | Public order |
| `robbery` | Robbery |
| `shoplifting` | Shoplifting |
| `theft-from-the-person` | Theft from the person |
| `vehicle-crime` | Vehicle crime |
| `violent-crime` | Violence and sexual offences |
| `other-crime` | Other crime |

## Stop and Search

```python
with PoliceAPI() as api:
    # Street-level stops — supply lat+lng, poly, or postcode+radius_km
    stops = api.stop_search.street(lat=51.5074, lng=-0.1278)
    stops = api.stop_search.street(postcode="SE1 7PB", radius_km=1, date="2024-10")
    stops = api.stop_search.street(poly=[(51.5, -0.1), ...])

    # At a specific location
    stops = api.stop_search.at_location(location_id=884227)

    # No fixed location
    stops = api.stop_search.no_location(force="metropolitan")

    # All stops by a force
    stops = api.stop_search.by_force("metropolitan", date="2024-10")
```

Each `StopSearch` includes: `type`, `datetime`, `location`, `gender`, `age_range`, `self_defined_ethnicity`, `officer_defined_ethnicity`, `legislation`, `object_of_search`, `outcome`.

## Forces

```python
with PoliceAPI() as api:
    forces = api.forces.list()                       # all 44 forces
    force = api.forces.get("metropolitan")           # force details
    officers = api.forces.people("metropolitan")     # senior officers
```

## Neighbourhoods

```python
with PoliceAPI() as api:
    # List neighbourhoods for a force
    hoods = api.neighbourhoods.list("metropolitan")

    # Neighbourhood details
    n = api.neighbourhoods.get("metropolitan", "00BK")
    print(n.name, n.population, n.contact_details.email)

    # Boundary polygon (list of Coordinates)
    boundary = api.neighbourhoods.boundary("metropolitan", "00BK")

    # Policing team, events, priorities
    team = api.neighbourhoods.people("metropolitan", "00BK")
    events = api.neighbourhoods.events("metropolitan", "00BK")
    priorities = api.neighbourhoods.priorities("metropolitan", "00BK")

    # Find neighbourhood by coordinate
    area = api.neighbourhoods.locate(lat=51.5074, lng=-0.1278)
    # area.force == "metropolitan", area.neighbourhood == "..."
```

## Data Availability

```python
with PoliceAPI() as api:
    dates = api.availability.dates()
    # dates[0].date == "2026-01"
    # dates[0].stop_and_search == ["metropolitan", "thames-valley", ...]
```

Crime data is typically 2–3 months behind the current date. Use `availability.dates()` to see exactly which months have published data.

## Postcode Geocoding

`PostcodesIO` and `AsyncPostcodesIO` wrap the [postcodes.io](https://postcodes.io) API. This is a **separate service** from data.police.uk — it requires internet access and calls `api.postcodes.io`.

```python
from uk_police_api import PostcodesIO

with PostcodesIO() as geo:
    loc = geo.lookup("SW1A 1AA")
    print(loc.postcode)       # "SW1A 1AA"
    print(loc.latitude)       # 51.50101
    print(loc.longitude)      # -0.141563
    print(loc.pfa)            # "Metropolitan Police"
    print(loc.admin_district) # "Westminster"
    print(loc.region)         # "London"

    # Bulk lookup (up to 100 postcodes, returns None for invalid)
    results = geo.bulk_lookup(["SW1A 1AA", "SE1 7PB", "INVALID"])
    # [GeocodedPostcode, GeocodedPostcode, None]
```

## Utilities

```python
from uk_police_api import circle_polygon, recent_months

# Generate a polygon approximating a circle (haversine-accurate)
poly = circle_polygon(lat=51.5074, lng=-0.1278, radius_km=2)
poly = circle_polygon(lat=51.5074, lng=-0.1278, radius_km=2, num_points=64)

# Last N calendar months as "YYYY-MM" strings, most recent first
months = recent_months(5)  # ["2026-04", "2026-03", "2026-02", "2026-01", "2025-12"]
```

## Async

Every resource has a fully async equivalent via `AsyncPoliceAPI` and `AsyncPostcodesIO`:

```python
import asyncio
from uk_police_api import AsyncPoliceAPI, AsyncPostcodesIO, circle_polygon

async def knife_crime(postcode: str, radius_km: float, months: int):
    async with AsyncPostcodesIO() as geo:
        loc = await geo.lookup(postcode)

    poly = circle_polygon(loc.latitude, loc.longitude, radius_km)

    async with AsyncPoliceAPI() as api:
        return await api.crimes.street_months(
            "possession-of-weapons",
            poly=poly,
            months=months,
        )

crimes = asyncio.run(knife_crime("SE1 7PB", radius_km=2, months=5))
```

## Caching

Responses are cached in memory by default (5-minute TTL). Disable or tune it:

```python
api = PoliceAPI(cache_ttl=600)   # 10-minute cache
api = PoliceAPI(cache_ttl=None)  # no cache
api.clear_cache()                # flush manually
```

## Error Handling

```python
from uk_police_api import (
    PoliceAPI,
    PoliceAPINotFoundError,
    PoliceAPIRateLimitError,
    PoliceAPITimeoutError,
)

with PoliceAPI() as api:
    try:
        force = api.forces.get("does-not-exist")
    except PoliceAPINotFoundError:
        print("Force not found")
    except PoliceAPIRateLimitError:
        print("Rate limited — retries exhausted")
    except PoliceAPITimeoutError:
        print("Request timed out")
```

Exception hierarchy: `PoliceAPIError` (base) → `PoliceAPINotFoundError`, `PoliceAPIRateLimitError`, `PoliceAPIServerError`, `PoliceAPITimeoutError`, `PoliceAPIResponseError`.

Retries (4x with exponential backoff) are enabled by default for 429 and 5xx responses. The `Retry-After` header is honoured on 429s.

## API Reference

The UK Police Data API is a free, open public API — no authentication or API key required.

- Base URL: `https://data.police.uk/api/`
- Rate limit: 15 requests/second sustained, 30/second burst (leaky bucket)
- Data updated monthly, typically 2–3 months behind current date
- Docs: [data.police.uk/docs](https://data.police.uk/docs/)

## License

MIT
