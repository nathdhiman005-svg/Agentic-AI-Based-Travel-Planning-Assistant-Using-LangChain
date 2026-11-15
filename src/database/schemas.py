"""
Pydantic data schemas for Flights, Hotels, and Places.
Provides type safety, field validation, and convenience helpers.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class FlightModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    flight_id: str
    airline: str
    from_city: str = Field(alias="from")
    to_city: str = Field(alias="to")
    departure_time: str
    arrival_time: str
    price: float

    @property
    def duration_hours(self) -> Optional[float]:
        """Calculates flight duration in hours if timestamps are parseable."""
        try:
            dep = datetime.fromisoformat(self.departure_time)
            arr = datetime.fromisoformat(self.arrival_time)
            duration = (arr - dep).total_seconds() / 3600.0
            return round(duration, 2)
        except Exception:
            return None

    @property
    def summary(self) -> str:
        """Human-readable summary of the flight option."""
        dur = f"{self.duration_hours}h" if self.duration_hours else "N/A"
        return (
            f"{self.airline} ({self.flight_id}) | "
            f"{self.from_city} -> {self.to_city} | "
            f"Departs: {self.departure_time} | Arrives: {self.arrival_time} "
            f"({dur}) | Fare: ₹{self.price:,.0f}"
        )


class HotelModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    hotel_id: str
    name: str
    city: str
    stars: int
    price_per_night: float
    amenities: List[str] = Field(default_factory=list)

    @property
    def summary(self) -> str:
        """Human-readable summary of the hotel recommendation."""
        amenities_str = ", ".join(self.amenities) if self.amenities else "None listed"
        return (
            f"{self.name} ({self.stars}-star) in {self.city} | "
            f"₹{self.price_per_night:,.0f}/night | Amenities: {amenities_str}"
        )


class PlaceModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    place_id: str
    name: str
    city: str
    type: str
    rating: float

    @property
    def summary(self) -> str:
        """Human-readable summary of the attraction/place."""
        return (
            f"{self.name} ({self.city}) | Category: {self.type} | "
            f"Rating: {self.rating:.1f}/5.0"
        )
