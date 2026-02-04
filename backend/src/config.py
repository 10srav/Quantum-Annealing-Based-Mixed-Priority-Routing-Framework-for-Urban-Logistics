"""
Configuration settings for the Quantum Priority Router.
"""

import json
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator
from functools import lru_cache
from typing import Any


def parse_cors_origins_value(v: Any) -> list[str]:
    """
    Parse CORS origins from various input formats.

    Supports:
    - JSON array: '["http://a.com", "http://b.com"]'
    - Comma-separated: "http://a.com,http://b.com"
    - List passthrough
    """
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        # Try JSON array first
        if v.startswith("["):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                pass
        # Fall back to comma-separated
        return [origin.strip() for origin in v.split(",") if origin.strip()]
    return v


def get_cors_origins_from_env() -> list[str]:
    """
    Get CORS origins from environment variable.

    Returns default development origins if env var not set.
    """
    env_value = os.environ.get("CORS_ORIGINS")
    if env_value:
        return parse_cors_origins_value(env_value)
    return ["http://localhost:5173", "http://localhost:3000"]


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Allow extra fields - cors_origins is handled via property
        extra="ignore",
    )

    # QAOA Configuration
    qaoa_reps: int = 2  # Number of QAOA layers
    qaoa_use_mock: bool = False  # Use mock solver for testing
    qaoa_shots: int = 1024  # Measurement shots

    # QUBO Default Parameters
    qubo_penalty_a: float = 100.0  # One-hot constraint
    qubo_penalty_b: float = 500.0  # Priority ordering
    qubo_penalty_bp: float = 1000.0  # Missing priority
    qubo_penalty_c: float = 1.0  # Objective weight

    # Traffic Multipliers
    traffic_low: float = 1.0
    traffic_medium: float = 1.5
    traffic_high: float = 2.0

    # API Settings
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Environment mode (development, staging, production)
    environment: str = "development"

    @property
    def cors_origins(self) -> list[str]:
        """
        Get CORS origins from environment.

        Parses CORS_ORIGINS env var as comma-separated or JSON array.
        Defaults to localhost origins for development.
        """
        return get_cors_origins_from_env()

    @model_validator(mode="after")
    def validate_cors_origins_for_production(self) -> "Settings":
        """Reject wildcard CORS origin in production mode."""
        origins = self.cors_origins
        if self.environment == "production" and "*" in origins:
            raise ValueError("Wildcard CORS origin '*' not allowed in production")
        return self

    # Authentication
    # Store the SHA-256 hash of the API key, never the plaintext key
    api_key_hash: str = ""

    # Rate Limiting
    rate_limit_per_minute: int = 60  # Requests per minute per API key
    rate_limit_solver_per_minute: int = 10  # Lower limit for compute-heavy solver endpoints

    # Timeout Settings
    solver_timeout_seconds: int = 30  # Max time for solver endpoints
    shutdown_timeout: int = 30  # Seconds to wait for in-flight requests during shutdown

    # Logging
    log_level: str = "INFO"  # DEBUG shows request/response bodies

    # Experiment Settings
    max_nodes: int = 25
    default_runs: int = 10


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
