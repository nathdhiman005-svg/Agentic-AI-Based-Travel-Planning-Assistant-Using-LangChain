"""
Database connection manager and session generator.
Handles connection pooling with Neon Tech PostgreSQL and local SQLite fallback.
"""

from contextlib import contextmanager
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from src.utils.config import settings


def get_normalized_db_url(url: str) -> str:
    """Ensures PostgreSQL connections use psycopg2 driver."""
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+psycopg2://", 1)
    return url


db_url = get_normalized_db_url(settings.DATABASE_URL)

# Configure engine with pooling and health checks
engine = create_engine(
    db_url,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Provide a transactional database session scope."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> dict:
    """Verifies active connectivity to the database."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            db_type = "Neon Tech PostgreSQL" if settings.is_postgres else "SQLite"
            return {"status": "ok" if result == 1 else "error", "database": db_type}
    except Exception as e:
        return {"status": "error", "error": str(e)}
