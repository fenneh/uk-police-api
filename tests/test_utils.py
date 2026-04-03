"""Tests for utility functions."""

import math

import pytest

from uk_police_api.utils import circle_polygon, encode_polygon, recent_months, validate_date


class TestCirclePolygon:
    def test_returns_correct_num_points(self):
        poly = circle_polygon(51.5, -0.1, radius_km=1)
        assert len(poly) == 32

    def test_custom_num_points(self):
        poly = circle_polygon(51.5, -0.1, radius_km=1, num_points=16)
        assert len(poly) == 16

    def test_all_points_are_lat_lng_tuples(self):
        poly = circle_polygon(51.5, -0.1, radius_km=1)
        for lat, lng in poly:
            assert isinstance(lat, float)
            assert isinstance(lng, float)

    def test_approximate_radius(self):
        """All points should be approximately the requested radius from centre."""
        centre_lat, centre_lng = 51.5074, -0.1278
        radius_km = 2.0
        poly = circle_polygon(centre_lat, centre_lng, radius_km)

        R = 6371.0
        for lat, lng in poly:
            # Haversine distance
            dlat = math.radians(lat - centre_lat)
            dlng = math.radians(lng - centre_lng)
            a = (
                math.sin(dlat / 2) ** 2
                + math.cos(math.radians(centre_lat))
                * math.cos(math.radians(lat))
                * math.sin(dlng / 2) ** 2
            )
            dist_km = 2 * R * math.asin(math.sqrt(a))
            assert abs(dist_km - radius_km) < 0.001  # within 1 metre

    def test_invalid_radius_raises(self):
        with pytest.raises(ValueError):
            circle_polygon(51.5, -0.1, radius_km=0)

    def test_invalid_num_points_raises(self):
        with pytest.raises(ValueError):
            circle_polygon(51.5, -0.1, radius_km=1, num_points=2)


class TestRecentMonths:
    def test_returns_correct_count(self):
        months = recent_months(5)
        assert len(months) == 5

    def test_format_is_yyyy_mm(self):
        for month in recent_months(3):
            assert len(month) == 7
            assert month[4] == "-"
            year, m = month.split("-")
            assert year.isdigit()
            assert 1 <= int(m) <= 12

    def test_most_recent_first(self):
        months = recent_months(3)
        assert months[0] >= months[1] >= months[2]

    def test_consecutive_months(self):
        months = recent_months(3)
        for i in range(len(months) - 1):
            y1, m1 = map(int, months[i].split("-"))
            y2, m2 = map(int, months[i + 1].split("-"))
            # m1 should be exactly one month after m2
            if m2 == 12:
                assert y1 == y2 + 1 and m1 == 1
            else:
                assert y1 == y2 and m1 == m2 + 1

    def test_invalid_n_raises(self):
        with pytest.raises(ValueError):
            recent_months(0)


class TestValidateDate:
    def test_valid_dates(self):
        assert validate_date("2024-01") == "2024-01"
        assert validate_date("2024-12") == "2024-12"

    def test_invalid_month(self):
        with pytest.raises(ValueError):
            validate_date("2024-13")

    def test_invalid_format(self):
        with pytest.raises(ValueError):
            validate_date("2024-1")
        with pytest.raises(ValueError):
            validate_date("2024/01")

    def test_full_date_rejected(self):
        with pytest.raises(ValueError):
            validate_date("2024-01-01")


class TestEncodePolygon:
    def test_encodes_correctly(self):
        poly = [(51.5, -0.1), (51.6, -0.2)]
        assert encode_polygon(poly) == "51.5,-0.1:51.6,-0.2"
