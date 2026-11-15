"""
Database seeding script for Neon Tech PostgreSQL.
Parses raw JSON data sources and populates relational SQL tables with idempotency.
"""

import json
from pathlib import Path
from src.utils.config import settings
from src.database.db_connection import engine, get_db_session
from src.database.models import Base, Flight, Hotel, Place


def seed_database():
    """Creates tables if needed and seeds flights, hotels, and places into Neon PostgreSQL."""
    data_dir = settings.DATA_SOURCES_DIR

    print("Step 1: Creating database tables and indexes in Neon PostgreSQL...")
    Base.metadata.create_all(bind=engine)
    print("Tables & indexes verified.")

    flights_file = data_dir / "flights.json"
    hotels_file = data_dir / "hotels.json"
    places_file = data_dir / "places.json"

    with get_db_session() as session:
        # 1. Seed Flights
        if flights_file.exists():
            with open(flights_file, "r", encoding="utf-8") as f:
                flights_data = json.load(f)

            print(f"Seeding {len(flights_data)} flights...")
            for item in flights_data:
                flight = Flight(
                    flight_id=item["flight_id"],
                    airline=item["airline"],
                    from_city=item["from"],
                    to_city=item["to"],
                    departure_time=item["departure_time"],
                    arrival_time=item["arrival_time"],
                    price=float(item["price"]),
                )
                session.merge(flight)  # Upsert based on PK

        # 2. Seed Hotels
        if hotels_file.exists():
            with open(hotels_file, "r", encoding="utf-8") as f:
                hotels_data = json.load(f)

            print(f"Seeding {len(hotels_data)} hotels...")
            for item in hotels_data:
                hotel = Hotel(
                    hotel_id=item["hotel_id"],
                    name=item["name"],
                    city=item["city"],
                    stars=int(item["stars"]),
                    price_per_night=float(item["price_per_night"]),
                    amenities_json=json.dumps(item.get("amenities", [])),
                )
                session.merge(hotel)  # Upsert based on PK

        # 3. Seed Places
        if places_file.exists():
            with open(places_file, "r", encoding="utf-8") as f:
                places_data = json.load(f)

            print(f"Seeding {len(places_data)} places...")
            for item in places_data:
                place = Place(
                    place_id=item["place_id"],
                    name=item["name"],
                    city=item["city"],
                    type=item["type"],
                    rating=float(item["rating"]),
                )
                session.merge(place)  # Upsert based on PK

    print("\nDatabase Seeding Complete! Verifying record counts...")
    with get_db_session() as session:
        f_count = session.query(Flight).count()
        h_count = session.query(Hotel).count()
        p_count = session.query(Place).count()
        print(f" - Flights in Neon PostgreSQL: {f_count}")
        print(f" - Hotels in Neon PostgreSQL: {h_count}")
        print(f" - Places in Neon PostgreSQL: {p_count}")


if __name__ == "__main__":
    seed_database()
