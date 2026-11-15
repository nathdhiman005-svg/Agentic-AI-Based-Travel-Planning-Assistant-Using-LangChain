"""
Configuration loader and settings manager.
Loads variables from environment or .env file.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from dotenv import load_dotenv

# Base project directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file from project root
ENV_PATH = BASE_DIR / ".env"
load_dotenv(dotenv_path=ENV_PATH)


@dataclass(frozen=True)
class Settings:
    # Project paths
    BASE_DIR: Path = BASE_DIR
    DATA_SOURCES_DIR: Path = BASE_DIR / "data sources"

    # Ollama / LLM Settings
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    # Database Settings (Neon Tech PostgreSQL or SQLite fallback)
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./travel_planner.db")

    # External APIs
    OPEN_METEO_BASE_URL: str = os.getenv(
        "OPEN_METEO_BASE_URL", "https://api.open-meteo.com/v1/forecast"
    )

    # Application Preferences
    APP_TITLE: str = os.getenv("APP_TITLE", "Agentic Travel Planning Assistant")
    DEFAULT_CURRENCY: str = os.getenv("DEFAULT_CURRENCY", "INR")
    REQUEST_TIMEOUT_SECONDS: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "15"))

    @property
    def is_postgres(self) -> bool:
        """Return True if connected to Neon Tech / PostgreSQL database."""
        return self.DATABASE_URL.startswith(("postgresql://", "postgres://"))


# Singleton configuration instance
settings = Settings()
