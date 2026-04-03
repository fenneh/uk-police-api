"""Utility functions for the UK Police API client."""

from __future__ import annotations

import math
import re
from datetime import date, timedelta

LatLng = tuple[float, float]
Polygon = list[LatLng]

_POLY_GET_THRESHOLD = 1800
_EARTH_RADIUS_KM = 6371.0


def encode_polygon(poly: Polygon) -> str:
    """Encode a polygon to the API's colon-separated lat,lng format.

    Example: [(51.5, -0.1), (51.6, -0.1)] -> "51.5,-0.1:51.6,-0.1"
    """
    return ":".join(f"{lat},{lng}" for lat, lng in poly)


def polygon_use_post(poly: Polygon, extra_params: dict[str, str] | None = None) -> bool:
    """Return True if the encoded polygon + params would exceed a safe GET URL length."""
    encoded = encode_polygon(poly)
    params = {"poly": encoded, **(extra_params or {})}
    length = sum(len(k) + len(str(v)) + 2 for k, v in params.items())
    return length > _POLY_GET_THRESHOLD


def validate_date(date_str: str) -> str:
    """Validate and return a YYYY-MM formatted date string.

    Raises:
        ValueError: If the date is not in YYYY-MM format.
    """
    if not re.fullmatch(r"\d{4}-(?:0[1-9]|1[0-2])", date_str):
        raise ValueError(f"date must be 'YYYY-MM', got {date_str!r}")
    return date_str


def circle_polygon(lat: float, lng: float, radius_km: float, num_points: int = 32) -> Polygon:
    """Generate a polygon approximating a circle around a point.

    The UK Police API has no native radius parameter — it accepts polygons.
    This function converts a radius into a polygon so you can query crimes
    within a given distance of a location.

    Uses the haversine formula for accurate geodesic distances.

    Args:
        lat: Centre latitude in decimal degrees.
        lng: Centre longitude in decimal degrees.
        radius_km: Radius in kilometres.
        num_points: Number of vertices in the polygon (default 32, higher = smoother).

    Returns:
        List of (latitude, longitude) tuples forming a closed polygon.

    Example::

        from uk_police_api.utils import circle_polygon

        poly = circle_polygon(51.5074, -0.1278, radius_km=2)
        crimes = api.crimes.street("possession-of-weapons", poly=poly)
    """
    if radius_km <= 0:
        raise ValueError(f"radius_km must be positive, got {radius_km}")
    if num_points < 3:
        raise ValueError(f"num_points must be at least 3, got {num_points}")

    lat_r = math.radians(lat)
    lng_r = math.radians(lng)
    d = radius_km / _EARTH_RADIUS_KM  # angular distance in radians

    points: Polygon = []
    for i in range(num_points):
        bearing = 2 * math.pi * i / num_points
        lat2 = math.asin(
            math.sin(lat_r) * math.cos(d) + math.cos(lat_r) * math.sin(d) * math.cos(bearing)
        )
        lng2 = lng_r + math.atan2(
            math.sin(bearing) * math.sin(d) * math.cos(lat_r),
            math.cos(d) - math.sin(lat_r) * math.sin(lat2),
        )
        points.append((math.degrees(lat2), math.degrees(lng2)))

    return points


def recent_months(n: int) -> list[str]:
    """Return the last N calendar months as 'YYYY-MM' strings, most recent first.

    Useful for querying the last N months of crime data. Note that crime data
    is typically 2-3 months behind — use api.availability.dates() to see exactly
    which months have published data.

    Args:
        n: Number of months to return.

    Returns:
        List of 'YYYY-MM' strings, e.g. ['2024-10', '2024-09', '2024-08'].

    Example::

        from uk_police_api.utils import recent_months

        for month in recent_months(5):
            crimes = api.crimes.street("possession-of-weapons", lat=51.5, lng=-0.1, date=month)
    """
    if n < 1:
        raise ValueError(f"n must be at least 1, got {n}")

    months: list[str] = []
    # Start from first day of current month, step back one month at a time
    today = date.today()
    current = date(today.year, today.month, 1)
    for _ in range(n):
        months.append(current.strftime("%Y-%m"))
        # Step back one month
        current = (current - timedelta(days=1)).replace(day=1)

    return months
