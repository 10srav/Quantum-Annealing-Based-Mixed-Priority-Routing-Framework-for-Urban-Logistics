"""
Configuration settings for the Quantum Priority Router.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""
    
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
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Experiment Settings
    max_nodes: int = 25
    default_runs: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
