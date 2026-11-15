"""
Places & attractions discovery tool for the Agentic Travel Assistant.
Retrieves and ranks points of interest (POIs) from Neon Tech PostgreSQL
(with local fallback) for constructing rich day-by-day itineraries.
"""

from typing import Optional, List
from langchain_core.tools import tool
from src.database.db_service import db_service
from src.database.schemas import PlaceModel


def find_places(
    city: str,
    category: Optional[str] = None,
    min_rating: Optional[float] = None,
    limit: Optional[int] = 5,
) -> List[PlaceModel]:
    """Retrieves ranked places from the database service."""
    return db_service.get_places(
        city=city,
        place_type=category,
        min_rating=min_rating,
        limit=limit,
    )


@tool
def discover_places(
    city: str,
    category: Optional[str] = None,
    min_rating: Optional[float] = None,
    limit: Optional[int] = 5,
) -> str:
    """
    Discover tourist attractions, heritage sites, and activities in a destination city.
    Use this tool to select places to visit for each day of the travel itinerary.

    Args:
        city: The destination city (e.g. 'Delhi', 'Goa', 'Jaipur', 'Mumbai', 'Kolkata').
        category: Optional category or type of attraction (e.g. 'temple', 'fort', 'museum', 'lake', 'market', 'beach').
        min_rating: Optional minimum traveler rating between 1.0 and 5.0 (e.g. 4.0, 4.5).
        limit: Maximum number of attractions to return (default is 5).

    Returns:
        A formatted list of top-rated attractions, their categories, ratings, and planning suggestions.
    """
    places = find_places(
        city=city,
        category=category,
        min_rating=min_rating,
        limit=limit,
    )

    if not places:
        all_city_places = db_service.get_places(city=city)
        if all_city_places:
            available_types = sorted(list({p.type for p in all_city_places}))
            types_str = ", ".join(available_types)
            return (
                f"No attractions in '{city}' match category='{category}' or rating>={min_rating}.\n"
                f"Available attraction categories in {city.title()}: {types_str}.\n"
                f"Suggestion: Remove the category filter or lower the rating threshold to see all sights."
            )
        else:
            cities = db_service.get_available_cities()
            return (
                f"No attraction records found for city '{city}'.\n"
                f"Available destination cities: {', '.join(cities)}."
            )

    output_lines = [
        f"Top Attractions & Sights in {city.title()} (Found {len(places)} options):"
    ]

    for i, p in enumerate(places, 1):
        badge = " [TOP ATTRACTION]" if p.rating >= 4.5 else ""
        output_lines.append(
            f"{i}. {p.name} ({p.type.title()}){badge}\n"
            f"   - Rating: {p.rating:.1f}/5.0\n"
            f"   - ID: {p.place_id}"
        )

    output_lines.append(
        "\nDay-Planning Tip: Schedule outdoor/heritage sights (forts, temples) in the morning to beat the heat, "
        "indoor spots (museums) during midday, and leisurely spots (markets, lakes) for the evening."
    )

    return "\n".join(output_lines)
