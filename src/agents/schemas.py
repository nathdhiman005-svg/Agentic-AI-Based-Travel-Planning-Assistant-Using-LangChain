"""
Structured output Pydantic schemas for the Agentic Travel Planning Assistant.
Enforces strict types for day-wise schedules, flights, hotels, weather, and budgets.
Supports JSON serialization and human-readable markdown generation.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SelectedFlight(BaseModel):
    """Details of the flight selected by the agent."""

    model_config = ConfigDict(populate_by_name=True)

    airline: str
    flight_id: str
    origin: Optional[str] = None
    destination: Optional[str] = None
    departure_time: str
    arrival_time: str
    fare: float
    duration: Optional[str] = None
    why_selected: Optional[str] = Field(
        default=None,
        description="Reasoning for selecting this flight (e.g. lowest fare or fastest transit)",
    )


class SelectedHotel(BaseModel):
    """Details of the hotel recommended by the agent."""

    model_config = ConfigDict(populate_by_name=True)

    hotel_name: str
    stars: int
    price_per_night: float
    total_price: float
    amenities: List[str] = Field(default_factory=list)
    why_selected: Optional[str] = Field(
        default=None,
        description="Reasoning for selecting this hotel (e.g. top guest rating or best value)",
    )


class DailyWeather(BaseModel):
    """Weather condition for an individual trip day."""

    day_number: int
    date: Optional[str] = None
    condition: str
    temperature_c: Optional[str] = None


class DailyPlan(BaseModel):
    """Activity schedule for a single day of the trip."""

    day_number: int
    title: str = Field(description="Brief theme or focus for the day")
    date: Optional[str] = None
    morning_activity: str
    afternoon_activity: str
    evening_activity: str
    weather: Optional[DailyWeather] = None


class BudgetBreakdown(BaseModel):
    """Itemized and total estimated expenditure for the trip."""

    flight_expense: float
    hotel_expense: float
    local_expenses: float
    total_budget: float
    is_within_budget: Optional[bool] = True
    budget_notes: Optional[str] = None


class TravelItineraryOutput(BaseModel):
    """Master structured itinerary produced by the agent."""

    model_config = ConfigDict(populate_by_name=True)

    trip_title: str = Field(description="E.g. 'Your 3-Day Trip to Goa'")
    destination: str
    origin: Optional[str] = None
    duration_days: int
    summary: str = Field(description="High-level overview of the curated trip experience")
    flight: Optional[SelectedFlight] = None
    hotel: Optional[SelectedHotel] = None
    weather_forecast: List[DailyWeather] = Field(default_factory=list)
    itinerary: List[DailyPlan] = Field(default_factory=list)
    budget: BudgetBreakdown
    reasoning: Optional[str] = Field(
        default=None,
        description="Explainability section: Why these recommendations fit user preferences",
    )

    def to_markdown(self) -> str:
        """Renders the itinerary in the exact human-readable format specified in the project rubric."""
        lines = [f"# {self.trip_title}", ""]

        if self.summary:
            lines.extend([f"**Overview:** {self.summary}", ""])

        # Flight
        if self.flight:
            lines.append("### Flight Selected:")
            lines.append(
                f"- **{self.flight.airline}** ({self.flight.flight_id}) – ₹{self.flight.fare:,.0f}"
            )
            lines.append(
                f"  - Departure: {self.flight.departure_time} | Arrival: {self.flight.arrival_time}"
            )
            if self.flight.why_selected:
                lines.append(f"  - *Selection Reason:* {self.flight.why_selected}")
            lines.append("")

        # Hotel
        if self.hotel:
            amenities_str = (
                f" ({', '.join(self.hotel.amenities)})" if self.hotel.amenities else ""
            )
            lines.append("### Hotel Booked:")
            lines.append(
                f"- **{self.hotel.hotel_name}** (₹{self.hotel.price_per_night:,.0f}/night, {self.hotel.stars}-star)"
            )
            lines.append(
                f"  - Total Stay Cost: ₹{self.hotel.total_price:,.0f}{amenities_str}"
            )
            if self.hotel.why_selected:
                lines.append(f"  - *Selection Reason:* {self.hotel.why_selected}")
            lines.append("")

        # Weather
        if self.weather_forecast:
            lines.append("### Weather:")
            for w in self.weather_forecast:
                temp_str = f" ({w.temperature_c})" if w.temperature_c else ""
                lines.append(f"- Day {w.day_number}: {w.condition}{temp_str}")
            lines.append("")

        # Itinerary
        if self.itinerary:
            lines.append("### Itinerary:")
            for day in self.itinerary:
                lines.append(f"**Day {day.day_number}: {day.title}**")
                lines.append(f"- *Morning:* {day.morning_activity}")
                lines.append(f"- *Afternoon:* {day.afternoon_activity}")
                lines.append(f"- *Evening:* {day.evening_activity}")
                lines.append("")

        # Budget
        lines.append("### Estimated Total Budget:")
        lines.append(f"- Flight: ₹{self.budget.flight_expense:,.0f}")
        lines.append(f"- Hotel: ₹{self.budget.hotel_expense:,.0f}")
        lines.append(f"- Food & Travel: ₹{self.budget.local_expenses:,.0f}")
        lines.append("-------------------------------------")
        lines.append(f"**Total Cost: ₹{self.budget.total_budget:,.0f}**")

        if self.budget.budget_notes:
            lines.append(f"*{self.budget.budget_notes}*")

        if self.reasoning:
            lines.extend(["", "### Why We Selected This:", self.reasoning])

        return "\n".join(lines)
