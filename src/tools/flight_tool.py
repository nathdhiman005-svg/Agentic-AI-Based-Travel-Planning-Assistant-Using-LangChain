"""
Flight search and ranking tool for the Agentic Travel Assistant.
Interfaces with Neon Tech PostgreSQL (and local data loader) to find,
filter, and rank flights based on traveler budget and duration preferences.
"""

from typing import Optional, List
from langchain_core.tools import tool
from src.database.db_service import db_service
from src.database.schemas import FlightModel


def find_flights(
    origin: str,
    destination: str,
    max_price: Optional[float] = None,
    sort_by: str = "price",
) -> List[FlightModel]:
    """Finds flights using database service and applies duration ranking if requested."""
    flights = db_service.get_flights(
        source=origin,
        destination=destination,
        max_price=max_price,
        sort_by=sort_by,
    )
    if sort_by == "duration":
        flights.sort(key=lambda x: (x.duration_hours or 999.0, x.price))
    return flights


@tool
def search_flights(
    origin: str,
    destination: str,
    max_price: Optional[float] = None,
    sort_by: str = "price",
) -> str:
    """
    Search and rank available flights between two cities.
    Use this tool whenever the user needs flight options, ticket prices, or airline recommendations.

    Args:
        origin: The departure city (e.g. 'Delhi', 'Hyderabad', 'Mumbai', 'Bangalore').
        destination: The arrival city (e.g. 'Goa', 'Kolkata', 'Delhi', 'Jaipur').
        max_price: Optional maximum one-way flight ticket budget in INR.
        sort_by: Sorting preference: 'price' (cheapest flight first) or 'duration' (fastest flight first). Default is 'price'.

    Returns:
        A formatted list of matching flight options with airline, timings, duration, and fare,
        along with best-value and fastest recommendations.
    """
    flights = find_flights(
        origin=origin,
        destination=destination,
        max_price=max_price,
        sort_by=sort_by,
    )

    if not flights:
        cities = db_service.get_available_cities()
        cities_str = ", ".join(cities)
        price_note = f" under ₹{max_price:,.0f}" if max_price else ""
        return (
            f"No direct flights found from '{origin}' to '{destination}'{price_note}.\n"
            f"Available flight network hubs include: {cities_str}.\n"
            f"Suggestion: Try searching for a nearby major hub or increasing the flight budget."
        )

    output_lines = [
        f"Found {len(flights)} flight option(s) from {origin.title()} to {destination.title()}:"
    ]

    # Identify highlights
    cheapest = min(flights, key=lambda f: f.price)
    fastest = min(flights, key=lambda f: f.duration_hours or 999.0)

    for i, f in enumerate(flights, 1):
        badges = []
        if f.flight_id == cheapest.flight_id:
            badges.append("[CHEAPEST]")
        if f.flight_id == fastest.flight_id:
            badges.append("[FASTEST]")
        badge_str = " " + " ".join(badges) if badges else ""

        dur_str = f"{f.duration_hours}h" if f.duration_hours else "N/A"
        output_lines.append(
            f"{i}. {f.airline} ({f.flight_id}){badge_str}\n"
            f"   - Departure: {f.departure_time} | Arrival: {f.arrival_time} (Duration: {dur_str})\n"
            f"   - Fare: ₹{f.price:,.0f} per person"
        )

    output_lines.append(
        f"\nRecommendation: For best value choose {cheapest.airline} ({cheapest.flight_id}) at ₹{cheapest.price:,.0f}. "
        f"For shortest travel time choose {fastest.airline} ({fastest.flight_id}) taking {fastest.duration_hours}h."
    )

    return "\n".join(output_lines)
