"""
Automated unit tests for system edge cases and graceful fallbacks.
Tests route unviability, weather API resilience, budget ceilings, and data limits.
"""

import unittest
from src.tools.flight_tool import search_flights, find_flights
from src.tools.weather_tool import get_weather_forecast, fetch_weather_forecast
from src.tools.hotel_tool import recommend_hotels, find_hotels
from src.tools.places_tool import discover_places, find_places
from src.tools.budget_tool import calculate_budget, compute_trip_budget
from src.agents.travel_agent import travel_agent


class TestEdgeCasesAndFallbacks(unittest.TestCase):

    def test_unserviced_flight_route(self):
        """Verify unavailable flight route returns helpful guidance rather than crashing."""
        result = search_flights.invoke({"origin": "Jaipur", "destination": "Goa"})
        self.assertIn("No direct flights found", result)
        self.assertIn("Available flight network hubs include", result)

    def test_unknown_city_weather(self):
        """Verify non-existent city handles geocoding error gracefully."""
        result = get_weather_forecast.invoke({"city": "NonExistentCityXYZ", "days": 3})
        self.assertIn("Weather information unavailable", result)

    def test_strict_hotel_filter_fallback(self):
        """Verify hotel tool informs user when no hotel matches 5-star under ₹500."""
        result = recommend_hotels.invoke({
            "city": "Delhi",
            "min_stars": 5,
            "max_price_per_night": 500,
        })
        self.assertIn("No hotels found", result)
        self.assertIn("Suggestion", result)

    def test_unmatched_attraction_category(self):
        """Verify places tool lists available categories if requested category doesn't exist."""
        result = discover_places.invoke({
            "city": "Delhi",
            "category": "snow_sports",
        })
        self.assertIn("Available attraction categories in Delhi", result)

    def test_budget_deficit_alert(self):
        """Verify budget calculator flags deficits when costs exceed user ceiling."""
        result = compute_trip_budget(
            flight_cost_per_person=6000,
            hotel_cost_per_night=5000,
            trip_days=3,
            user_budget_limit=10000,
        )
        self.assertFalse(result["is_within_budget"])
        self.assertLess(result["remaining_buffer"], 0)

    def test_structured_parser_resilience(self):
        """Verify parser can extract realistic fallback models from minimal text."""
        output = travel_agent.parse_to_structured_itinerary(
            raw_markdown="Empty response from model",
            destination="Delhi",
            origin="Hyderabad",
            duration_days=3,
            budget_limit=15000,
            num_travelers=1,
        )
        self.assertIsNotNone(output.flight)
        self.assertIsNotNone(output.hotel)
        self.assertGreater(output.budget.total_budget, 0)


if __name__ == "__main__":
    unittest.main()
