"""Get a full overview of the neighbourhood at a given location.

Shows the neighbourhood name, contact details, current priorities, and upcoming events.

Usage:
    uv run examples/neighbourhood_overview.py
    uv run examples/neighbourhood_overview.py --lat 51.5074 --lng -0.1278
"""

import argparse

from uk_police_api import PoliceAPI


def main() -> None:
    parser = argparse.ArgumentParser(description="Neighbourhood overview for a location")
    parser.add_argument("--lat", type=float, default=51.5074, help="Latitude")
    parser.add_argument("--lng", type=float, default=-0.1278, help="Longitude")
    args = parser.parse_args()

    with PoliceAPI() as api:
        located = api.neighbourhoods.locate(lat=args.lat, lng=args.lng)
        print(f"Force: {located.force}")
        print(f"Neighbourhood ID: {located.neighbourhood}\n")

        n = api.neighbourhoods.get(located.force, located.neighbourhood)
        print(f"Name: {n.name}")
        if n.description:
            print(f"Description: {n.description}")
        if n.contact_details.email:
            print(f"Email: {n.contact_details.email}")
        if n.contact_details.telephone:
            print(f"Phone: {n.contact_details.telephone}")

        priorities = api.neighbourhoods.priorities(located.force, located.neighbourhood)
        if priorities:
            print(f"\nCurrent priorities ({len(priorities)}):")
            for p in priorities:
                print(f"  - {p.issue}")
                if p.action:
                    print(f"    Action: {p.action}")

        events = api.neighbourhoods.events(located.force, located.neighbourhood)
        if events:
            print(f"\nUpcoming events ({len(events)}):")
            for e in events:
                print(f"  - {e.title}")
                if e.start_date:
                    print(f"    Date: {e.start_date}")
                if e.address:
                    print(f"    Location: {e.address}")
        else:
            print("\nNo upcoming events.")


if __name__ == "__main__":
    main()
