"""Find knife crime (possession of weapons) near a location.

Usage:
    uv run examples/knife_crime.py
    uv run examples/knife_crime.py --postcode "SE1 7PB" --months 3
"""

import argparse

from uk_police_api import PoliceAPI


def main() -> None:
    parser = argparse.ArgumentParser(description="Look up knife crime near a location")
    parser.add_argument("--postcode", default="SE1 7PB", help="UK postcode")
    parser.add_argument("--radius", type=float, default=1.0, help="Radius in km")
    parser.add_argument("--months", type=int, default=3, help="Number of months to search")
    args = parser.parse_args()

    with PoliceAPI() as api:
        print(f"Searching for knife crime within {args.radius}km of {args.postcode}...")
        crimes = api.crimes.street_months(
            "possession-of-weapons",
            postcode=args.postcode,
            radius_km=args.radius,
            months=args.months,
        )

    print(f"\nFound {len(crimes)} knife crime incidents in the past {args.months} month(s):\n")
    for crime in crimes:
        location = "unknown location"
        if crime.location and crime.location.street:
            location = crime.location.street.name
        outcome = crime.outcome_status.category if crime.outcome_status else "No outcome recorded"
        print(f"  [{crime.month}] {location}")
        print(f"           Outcome: {outcome}")

    if not crimes:
        print("  No incidents found.")


if __name__ == "__main__":
    main()
