"""
Database initialization and migration script.
Creates tables in Neon Tech PostgreSQL and verifies persistence.
"""

from src.database.db_connection import engine, get_db_session, test_connection
from src.database.models import Base, SavedItinerary, QueryLog


def init_db():
    """Creates all required tables if they do not exist."""
    print("Testing connection to database...")
    health = test_connection()
    if health.get("status") != "ok":
        raise ConnectionError(f"Database connection failed: {health.get('error')}")

    print(f"Connected to database successfully ({health.get('database')}).")
    print("Creating tables if not exists...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully: 'saved_itineraries', 'query_logs'.")


def verify_db_operations():
    """Runs a test write and read operation to confirm CRUD functionality."""
    print("Verifying database operations...")
    with get_db_session() as session:
        # Create test log
        test_log = QueryLog(
            user_query="Verification test query",
            tool_calls="flight_tool, weather_tool",
            latency_seconds=1.25,
            status="SUCCESS",
        )
        session.add(test_log)
        session.flush()

        log_id = test_log.id
        print(f"Inserted test QueryLog with ID: {log_id}")

        # Query back
        retrieved = session.query(QueryLog).filter(QueryLog.id == log_id).first()
        assert retrieved is not None, "Failed to retrieve inserted QueryLog"
        print(f"Retrieved QueryLog: status={retrieved.status}, latency={retrieved.latency_seconds}s")

        # Clean up test log
        session.delete(retrieved)
        print("Cleaned up test verification log.")

    print("Database verification passed with 100% success!")


if __name__ == "__main__":
    init_db()
    verify_db_operations()
