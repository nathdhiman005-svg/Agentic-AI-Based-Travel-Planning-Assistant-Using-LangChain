"""
Tools package for the Agentic Travel Planning Assistant.
Exports all specialized LangChain tools.
"""

from src.tools.weather_tool import get_weather_forecast, fetch_weather_forecast
from src.tools.flight_tool import search_flights, find_flights
from src.tools.hotel_tool import recommend_hotels, find_hotels
from src.tools.places_tool import discover_places, find_places
from src.tools.budget_tool import calculate_budget, compute_trip_budget

ALL_TRAVEL_TOOLS = [
    get_weather_forecast,
    search_flights,
    recommend_hotels,
    discover_places,
    calculate_budget,
]

__all__ = [
    "get_weather_forecast",
    "fetch_weather_forecast",
    "search_flights",
    "find_flights",
    "recommend_hotels",
    "find_hotels",
    "discover_places",
    "find_places",
    "calculate_budget",
    "compute_trip_budget",
    "ALL_TRAVEL_TOOLS",
]
