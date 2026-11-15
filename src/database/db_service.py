"""
Database service layer providing SQL-based query methods over Neon Tech PostgreSQL.
Includes graceful fallback to local JSON loader if database connectivity is unavailable.
Returns standardized Pydantic models (FlightModel, HotelModel, PlaceModel).
"""

from typing import List, Optional, Set
from sqlalchemy import func, desc, asc
from src.database.db_connection import get_db_session
from src.database.models import Flight, Hotel, Place, SavedItinerary, QueryLog
from src.database.schemas import FlightModel, HotelModel, PlaceModel
from src.database.json_loader import data_loader


class DatabaseService:
    """Service layer executing SQL queries against Neon Tech PostgreSQL."""

    def get_available_cities(self) -> List[str]:
        """Returns sorted list of distinct cities present in the database."""
        try:
            with get_db_session() as session:
                flight_from = [
                    c[0]
                    for c in session.query(func.distinct(Flight.from_city)).all()
                    if c[0]
                ]
                flight_to = [
                    c[0]
                    for c in session.query(func.distinct(Flight.to_city)).all()
                    if c[0]
                ]
                hotel_cities = [
                    c[0]
                    for c in session.query(func.distinct(Hotel.city)).all()
                    if c[0]
                ]
                place_cities = [
                    c[0]
                    for c in session.query(func.distinct(Place.city)).all()
                    if c[0]
                ]

                all_cities: Set[str] = set(
                    flight_from + flight_to + hotel_cities + place_cities
                )
                if all_cities:
                    return sorted(list(all_cities))
        except Exception:
            pass
        return data_loader.get_available_cities()

    def get_flights(
        self,
        source: str,
        destination: str,
        max_price: Optional[float] = None,
        sort_by: str = "price",
    ) -> List[FlightModel]:
        """Queries flights from Neon Tech using SQL indexing and filters."""
        try:
            with get_db_session() as session:
                query = session.query(Flight).filter(
                    func.lower(Flight.from_city) == source.strip().lower(),
                    func.lower(Flight.to_city) == destination.strip().lower(),
                )

                if max_price is not None:
                    query = query.filter(Flight.price <= max_price)

                if sort_by == "departure":
                    query = query.order_by(asc(Flight.departure_time))
                else:
                    # Default: cheapest first
                    query = query.order_by(asc(Flight.price))

                records = query.all()
                if records:
                    return [
                        FlightModel(
                            flight_id=r.flight_id,
                            airline=r.airline,
                            from_city=r.from_city,
                            to_city=r.to_city,
                            departure_time=r.departure_time,
                            arrival_time=r.arrival_time,
                            price=r.price,
                        )
                        for r in records
                    ]
        except Exception:
            pass
        return data_loader.get_flights(source, destination, max_price, sort_by)

    def get_hotels(
        self,
        city: str,
        min_stars: Optional[int] = None,
        max_price: Optional[float] = None,
        required_amenities: Optional[List[str]] = None,
        sort_by: str = "stars",
    ) -> List[HotelModel]:
        """Queries hotels from Neon Tech using SQL indexes and filters."""
        try:
            with get_db_session() as session:
                query = session.query(Hotel).filter(
                    func.lower(Hotel.city) == city.strip().lower()
                )

                if min_stars is not None:
                    query = query.filter(Hotel.stars >= min_stars)

                if max_price is not None:
                    query = query.filter(Hotel.price_per_night <= max_price)

                if sort_by == "price":
                    query = query.order_by(asc(Hotel.price_per_night), desc(Hotel.stars))
                else:
                    # Highest stars first, then lowest price
                    query = query.order_by(desc(Hotel.stars), asc(Hotel.price_per_night))

                records = query.all()
                results: List[HotelModel] = []
                for r in records:
                    amenities_list = r.amenities
                    if required_amenities:
                        req_lower = {a.strip().lower() for a in required_amenities}
                        if not req_lower.issubset({a.lower() for a in amenities_list}):
                            continue
                    results.append(
                        HotelModel(
                            hotel_id=r.hotel_id,
                            name=r.name,
                            city=r.city,
                            stars=r.stars,
                            price_per_night=r.price_per_night,
                            amenities=amenities_list,
                        )
                    )
                if results or min_stars or max_price:
                    return results
        except Exception:
            pass
        return data_loader.get_hotels(
            city, min_stars, max_price, required_amenities, sort_by
        )

    def get_places(
        self,
        city: str,
        place_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[PlaceModel]:
        """Queries tourist attractions from Neon Tech ranked by rating."""
        try:
            with get_db_session() as session:
                query = session.query(Place).filter(
                    func.lower(Place.city) == city.strip().lower()
                )

                if place_type and place_type.strip():
                    query = query.filter(
                        func.lower(Place.type).contains(place_type.strip().lower())
                    )

                if min_rating is not None:
                    query = query.filter(Place.rating >= min_rating)

                query = query.order_by(desc(Place.rating))

                if limit is not None and limit > 0:
                    query = query.limit(limit)

                records = query.all()
                if records or place_type or min_rating:
                    return [
                        PlaceModel(
                            place_id=r.place_id,
                            name=r.name,
                            city=r.city,
                            type=r.type,
                            rating=r.rating,
                        )
                        for r in records
                    ]
        except Exception:
            pass
        return data_loader.get_places(city, place_type, min_rating, limit)

    def save_itinerary(
        self,
        session_id: str,
        title: str,
        destination: str,
        total_cost: float,
        itinerary_json: str,
        origin: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Optional[int]:
        """Saves a finalized itinerary into Neon Tech database."""
        try:
            with get_db_session() as session:
                itinerary = SavedItinerary(
                    session_id=session_id,
                    title=title,
                    origin=origin,
                    destination=destination,
                    start_date=start_date,
                    end_date=end_date,
                    total_cost=total_cost,
                    itinerary_json=itinerary_json,
                )
                session.add(itinerary)
                session.flush()
                return itinerary.id
        except Exception as e:
            print(f"Error saving itinerary to database: {e}")
            return None

    def log_query(
        self,
        user_query: str,
        tool_calls: str,
        latency_seconds: float,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
    ):
        """Records agent invocation telemetry in Neon Tech database."""
        try:
            with get_db_session() as session:
                log = QueryLog(
                    user_query=user_query,
                    tool_calls=tool_calls,
                    latency_seconds=latency_seconds,
                    status=status,
                    error_message=error_message,
                )
                session.add(log)
        except Exception as e:
            print(f"Error logging query to database: {e}")


# Global database service instance
db_service = DatabaseService()
