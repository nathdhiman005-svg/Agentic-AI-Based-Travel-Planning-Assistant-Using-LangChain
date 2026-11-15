"""
Hotel recommendation tool for the Agentic Travel Assistant.
Queries Neon Tech PostgreSQL (with local fallback) to suggest, filter,
and rank accommodations based on city, star ratings, nightly rates, and amenities.
"""

from typing import Optional, List, Union
from langchain_core.tools import tool
from src.database.db_service import db_service
from src.database.schemas import HotelModel


def find_hotels(
    city: str,
    min_stars: Optional[int] = None,
    max_price_per_night: Optional[float] = None,
    amenities: Optional[Union[str, List[str]]] = None,
    sort_by: str = "stars",
) -> List[HotelModel]:
    """Retrieves filtered hotel list from database service."""
    req_amenities: Optional[List[str]] = None
    if amenities:
        if isinstance(amenities, str):
            req_amenities = [a.strip() for a in amenities.split(",") if a.strip()]
        elif isinstance(amenities, list):
            req_amenities = [str(a).strip() for a in amenities if str(a).strip()]

    return db_service.get_hotels(
        city=city,
        min_stars=min_stars,
        max_price=max_price_per_night,
        required_amenities=req_amenities,
        sort_by=sort_by,
    )


@tool
def recommend_hotels(
    city: str,
    min_stars: Optional[int] = None,
    max_price_per_night: Optional[float] = None,
    amenities_preferred: Optional[str] = None,
    sort_by: str = "stars",
) -> str:
    """
    Find and recommend hotels in a specific city with budget and rating filters.
    Use this tool whenever travelers need lodging recommendations, room prices, or accommodation options.

    Args:
        city: The destination city (e.g. 'Goa', 'Delhi', 'Jaipur', 'Mumbai').
        min_stars: Optional minimum star rating between 1 and 5 (e.g. 3, 4, 5).
        max_price_per_night: Optional maximum room budget per night in INR.
        amenities_preferred: Optional comma-separated list of required amenities (e.g. 'wifi, pool, breakfast, gym').
        sort_by: Sorting preference: 'stars' (highest rated luxury first) or 'price' (cheapest hotel first). Default is 'stars'.

    Returns:
        A formatted list of hotel options with star ratings, nightly tariffs, amenities,
        and recommendations for top-rated and best-value accommodations.
    """
    hotels = find_hotels(
        city=city,
        min_stars=min_stars,
        max_price_per_night=max_price_per_night,
        amenities=amenities_preferred,
        sort_by=sort_by,
    )

    if not hotels:
        filter_parts = []
        if min_stars:
            filter_parts.append(f"{min_stars}+ stars")
        if max_price_per_night:
            filter_parts.append(f"under ₹{max_price_per_night:,.0f}/night")
        if amenities_preferred:
            filter_parts.append(f"with amenities: {amenities_preferred}")
        filters_str = " (" + ", ".join(filter_parts) + ")" if filter_parts else ""

        return (
            f"No hotels found in '{city}' matching your criteria{filters_str}.\n"
            f"Suggestion: Try lowering the minimum star rating or increasing the nightly budget limit."
        )

    output_lines = [f"Found {len(hotels)} hotel recommendation(s) in {city.title()}:"]

    # Highlights
    top_rated = max(hotels, key=lambda h: h.stars)
    cheapest = min(hotels, key=lambda h: h.price_per_night)

    for i, h in enumerate(hotels, 1):
        badges = []
        if h.stars == top_rated.stars:
            badges.append("[TOP RATED]")
        if h.hotel_id == cheapest.hotel_id:
            badges.append("[BEST VALUE]")
        badge_str = " " + " ".join(badges) if badges else ""

        amenities_str = ", ".join(h.amenities) if h.amenities else "Standard amenities"
        output_lines.append(
            f"{i}. {h.name} ({h.stars}-Star){badge_str}\n"
            f"   - Nightly Rate: ₹{h.price_per_night:,.0f} per room\n"
            f"   - Amenities: {amenities_str}\n"
            f"   - ID: {h.hotel_id}"
        )

    output_lines.append(
        f"\nRecommendation: For best comfort choose {top_rated.name} ({top_rated.stars}-star, ₹{top_rated.price_per_night:,.0f}/night). "
        f"For highest savings choose {cheapest.name} (₹{cheapest.price_per_night:,.0f}/night)."
    )

    return "\n".join(output_lines)
