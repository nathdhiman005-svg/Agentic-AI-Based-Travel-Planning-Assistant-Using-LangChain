"""
SQLAlchemy ORM models for Neon Tech PostgreSQL database.
Defines normalized tables for Flights, Hotels, Places, Saved Itineraries, and Query Logs.
Adheres to PEP 8, indexing best practices, and clean naming conventions.
"""

from datetime import datetime
import json
from typing import List, Optional
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Text,
    DateTime,
    Index,
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Flight(Base):
    """Relational table storing available flight routes and pricing."""

    __tablename__ = "flights"

    flight_id = Column(String(50), primary_key=True)
    airline = Column(String(100), nullable=False)
    from_city = Column(String(100), nullable=False, index=True)
    to_city = Column(String(100), nullable=False, index=True)
    departure_time = Column(String(50), nullable=False)
    arrival_time = Column(String(50), nullable=False)
    price = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite index for rapid route lookups
    __table_args__ = (
        Index("idx_flight_route_price", "from_city", "to_city", "price"),
    )

    def __repr__(self):
        return f"<Flight({self.flight_id}: {self.airline} {self.from_city}->{self.to_city} ₹{self.price})>"


class Hotel(Base):
    """Relational table storing hotel accommodations, star ratings, and amenities."""

    __tablename__ = "hotels"

    hotel_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    stars = Column(Integer, nullable=False, index=True)
    price_per_night = Column(Float, nullable=False, index=True)
    amenities_json = Column(Text, nullable=False, default="[]")  # Serialized JSON list
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite index for filtering hotels by city and star rating
    __table_args__ = (
        Index("idx_hotel_city_stars_price", "city", "stars", "price_per_night"),
    )

    @property
    def amenities(self) -> List[str]:
        try:
            return json.loads(self.amenities_json)
        except Exception:
            return []

    @amenities.setter
    def amenities(self, value: List[str]):
        self.amenities_json = json.dumps(value)

    def __repr__(self):
        return f"<Hotel({self.hotel_id}: {self.name} in {self.city}, {self.stars}* ₹{self.price_per_night})>"


class Place(Base):
    """Relational table storing tourist attractions and points of interest."""

    __tablename__ = "places"

    place_id = Column(String(50), primary_key=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    type = Column(String(100), nullable=False)
    rating = Column(Float, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite index for finding top rated places in a city
    __table_args__ = (
        Index("idx_place_city_rating", "city", "rating"),
    )

    def __repr__(self):
        return f"<Place({self.place_id}: {self.name} in {self.city}, rating={self.rating})>"


class SavedItinerary(Base):
    """Stores finalized trip itineraries saved by the user."""

    __tablename__ = "saved_itineraries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    origin = Column(String(100), nullable=True)
    destination = Column(String(100), nullable=False, index=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    total_cost = Column(Float, nullable=False, default=0.0)
    itinerary_json = Column(Text, nullable=False)  # Full JSON payload
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<SavedItinerary(id={self.id}, title='{self.title}', destination='{self.destination}')>"


class QueryLog(Base):
    """Logs agent execution runs, tool invocations, and latency metrics."""

    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_query = Column(Text, nullable=False)
    tool_calls = Column(Text, nullable=True)  # List of tools invoked
    latency_seconds = Column(Float, nullable=False, default=0.0)
    status = Column(String(20), nullable=False, default="SUCCESS")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<QueryLog(id={self.id}, status='{self.status}', latency={self.latency_seconds:.2f}s)>"
