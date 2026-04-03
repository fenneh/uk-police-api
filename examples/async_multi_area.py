"""Async example: compare crime rates across multiple postcodes concurrently.

Usage:
    uv run examples/async_multi_area.py
"""

import asyncio

from uk_police_api import AsyncPoliceAPI


POSTCODES = [
    ("SE1 7PB", "Borough Market"),
    ("EC1A 1BB", "Barbican"),
    ("WC2N 5DU", "Trafalgar Square"),
    ("E1 6RF", "Whitechapel"),
]


async def fetch_crimes(api: AsyncPoliceAPI, postcode: str, label: str) -> tuple[str, int]:
    crimes = await api.crimes.street_months(
        "all-crime",
        postcode=postcode,
        radius_km=0.5,
        months=3,
    )
    return label, len(crimes)


async def main() -> None:
    async with AsyncPoliceAPI() as api:
        tasks = [fetch_crimes(api, postcode, label) for postcode, label in POSTCODES]
        results = await asyncio.gather(*tasks)

    print("Crime counts (all crime, 0.5km radius, last 3 months):\n")
    for label, count in sorted(results, key=lambda x: x[1], reverse=True):
        bar = "#" * (count // 5)
        print(f"  {label:<20} {count:>4}  {bar}")


if __name__ == "__main__":
    asyncio.run(main())
