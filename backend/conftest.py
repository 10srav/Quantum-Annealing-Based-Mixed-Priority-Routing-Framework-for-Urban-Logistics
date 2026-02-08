"""
Root conftest - sets environment before any test modules are imported.

This must be at the backend root (not in tests/) so it runs before
app.main's module-level get_settings() call during test collection.
"""

import os
from pathlib import Path

# Set working directory to backend/ so pydantic-settings finds .env
os.chdir(Path(__file__).parent)

# Set API key hash directly as env var to ensure tests can authenticate.
# SHA-256 hash of "test"
os.environ["API_KEY_HASH"] = (
    "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08"
)
