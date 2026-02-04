"""
API Key authentication module for the Quantum Priority Router.

Security approach:
- API keys are stored as SHA-256 hashes, never plaintext
- Timing-safe comparison prevents timing attacks
- Header-based authentication (X-API-Key)
"""

import hashlib
import secrets
from fastapi import Header, HTTPException


def hash_api_key(key: str) -> str:
    """
    Hash an API key using SHA-256.

    Use this function to generate the hash to store in configuration.
    Never store plaintext API keys.

    Args:
        key: The plaintext API key

    Returns:
        The SHA-256 hex digest of the key
    """
    return hashlib.sha256(key.encode()).hexdigest()


def verify_api_key(x_api_key: str = Header(..., description="API key for authentication")) -> bool:
    """
    FastAPI dependency to verify API key from X-API-Key header.

    Performs timing-safe comparison against the stored hash to prevent
    timing attacks. Raises 401 if key is invalid or missing.

    Args:
        x_api_key: The API key from the X-API-Key header

    Returns:
        True if valid

    Raises:
        HTTPException: 401 if key is invalid
    """
    from src.config import get_settings

    settings = get_settings()

    # Hash the provided key
    provided_hash = hash_api_key(x_api_key)

    # Timing-safe comparison to prevent timing attacks
    if not settings.api_key_hash or not secrets.compare_digest(provided_hash, settings.api_key_hash):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )

    return True
