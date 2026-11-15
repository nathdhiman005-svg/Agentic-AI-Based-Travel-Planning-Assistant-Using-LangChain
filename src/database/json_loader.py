"""
Data access layer for local JSON datasets (flights, hotels, places).
Provides in-memory caching and flexible filtering/sorting functions.
"""

import json
from pathlib import Path
from typing import List, Optional, Set
from src.utils.config import settings
from src.database.schemas import FlightModel, HotelModel, PlaceModel


class JSONDataLoader:
    """Singleton-style cache and query manager for local travel datasets."""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or settings.DATA_SOURCES_DIR
        self._flights: Optional[List[FlightModel]] = None
        self._hotels: Optional[List[HotelModel]] = None
        self._places: Optional[List[PlaceModel]] = None

    def _load_flights(self) -> List[FlightModel]:
        if self._flights is None:
            file_path = self.data_dir / "flights.json"
            if not file_path.exists():
                raise FileNotFoundError(f"Flight dataset not found at: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            self._flights = [FlightModel(**item) for item in raw_data]
        return self._flights

    def _load_hotels(self) -> List[HotelModel]:
        if self._hotels is None:
            file_path = self.data_dir / "hotels.json"
            if not file_path.exists():
                raise FileNotFoundError(f"Hotel dataset not found at: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            self._hotels = [HotelModel(**item) for item in raw_data]
        return self._hotels

    def _load_places(self) -> List[PlaceModel]:
        if self._places is None:
            file_path = self.data_dir / "places.json"
            if not file_path.exists():
                raise FileNotFoundError(f"Places dataset not found at: {file_path}")
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            self._places = [PlaceModel(**item) for item in raw_data]
        return self._places

    def get_available_cities(self) -> List[str]:
        """Return a sorted list of all unique cities across datasets."""
        cities: Set[str] = set()
        for f in self._load_flights():
            cities.add(f.from_city.strip())
            cities.add(f.to_city.strip())
        for h in self._load_hotels():
            cities.add(h.city.strip())
        for p in self._load_places():
            cities.add(p.city.strip())
        return sorted(list(cities))

    def get_flights(
        self,
        source: str,
        destination: str,
        max_price: Optional[float] = None,
        sort_by: str = "price",
    ) -> List[FlightModel]:
        """
        Search flights by origin and destination with optional max price.
        sort_by options: 'price' (cheapest first), 'duration' (fastest first), 'departure'
        """
        src_lower = source.strip().lower()
        dst_lower = destination.strip().lower()

        results = [
            f
            for f in self._load_flights()
            if f.from_city.lower() == src_lower and f.to_city.lower() == dst_lower
        ]

        if max_price is not None:
            results = [f for f in results if f.price <= max_price]

        if sort_by == "duration":
            results.sort(key=lambda x: (x.duration_hours or 999.0, x.price))
        elif sort_by == "departure":
            results.sort(key=lambda x: x.departure_time)
        else:
            # Default: cheapest first
            results.sort(key=lambda x: x.price)

        return results

    def get_hotels(
        self,
        city: str,
        min_stars: Optional[int] = None,
        max_price: Optional[float] = None,
        required_amenities: Optional[List[str]] = None,
        sort_by: str = "stars",
    ) -> List[HotelModel]:
        """
        Search hotels in a specific city with star and budget filters.
        sort_by options: 'stars' (highest rated first), 'price' (cheapest first)
        """
        city_lower = city.strip().lower()
        results = [h for h in self._load_hotels() if h.city.lower() == city_lower]

        if min_stars is not None:
            results = [h for h in results if h.stars >= min_stars]

        if max_price is not None:
            results = [h for h in results if h.price_per_night <= max_price]

        if required_amenities:
            req_amenities_lower = {a.strip().lower() for a in required_amenities}
            results = [
                h
                for h in results
                if req_amenities_lower.issubset({a.lower() for a in h.amenities})
            ]

        if sort_by == "price":
            results.sort(key=lambda x: (x.price_per_night, -x.stars))
        else:
            # Default: highest stars first, then lowest price
            results.sort(key=lambda x: (-x.stars, x.price_per_night))

        return results

    def get_places(
        self,
        city: str,
        place_type: Optional[str] = None,
        min_rating: Optional[float] = None,
        limit: Optional[int] = None,
    ) -> List[PlaceModel]:
        """
        Search attractions / places of interest for a city.
        Filters by type (e.g. temple, fort, lake) and minimum rating.
        Sorted by rating (highest first).
        """
        city_lower = city.strip().lower()
        results = [p for p in self._load_places() if p.city.lower() == city_lower]

        if place_type is not None and place_type.strip():
            ptype_lower = place_type.strip().lower()
            results = [p for p in results if ptype_lower in p.type.lower()]

        if min_rating is not None:
            results = [p for p in results if p.rating >= min_rating]

        # Highest rating first
        results.sort(key=lambda x: -x.rating)

        if limit is not None and limit > 0:
            results = results[:limit]

        return results


# Global singleton instance
data_loader = JSONDataLoader()
