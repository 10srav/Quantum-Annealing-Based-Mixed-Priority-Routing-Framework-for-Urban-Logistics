"""
Security utilities for the Quantum Priority Router API.

This module provides path validation and sanitization functions to prevent
path traversal attacks and other security vulnerabilities when handling
user-supplied file paths.
"""

import re
from pathlib import Path


# Allowlist pattern for graph names: alphanumeric, hyphens, underscores only.
# This prevents path traversal (../, ..\\) and other injection attacks by
# rejecting any characters that could be interpreted as path components.
GRAPH_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

# Base directory for graph data files.
# All validated paths must resolve to locations within this directory.
DATA_DIR = Path(__file__).parent.parent / "data"


def validate_graph_path(graph_name: str) -> Path:
    """
    Validate a graph name and return the safe, absolute file path.

    This function implements defense-in-depth with two security checks:
    1. Allowlist validation: Graph name must match alphanumeric pattern
    2. Path traversal check: Resolved path must stay within DATA_DIR

    Args:
        graph_name: The user-supplied graph name to validate.

    Returns:
        Path: The validated absolute path to the graph JSON file.

    Raises:
        ValueError: If the graph name contains invalid characters or
                   if the resolved path would escape the data directory.

    Security:
        - Rejects names with path separators (/, \\), dots, spaces, etc.
        - Prevents symlink attacks by resolving to absolute path
        - Ensures final path is within the designated data directory
    """
    # Check 1: Allowlist validation - reject any non-alphanumeric characters
    if not GRAPH_NAME_PATTERN.match(graph_name):
        raise ValueError(
            "Invalid graph name: must be alphanumeric, hyphens, underscores only"
        )

    # Construct the file path and resolve to absolute
    filepath = (DATA_DIR / f"{graph_name}.json").resolve()

    # Check 2: Path traversal detection - ensure path stays within DATA_DIR
    # This catches edge cases that might slip past the pattern check
    if not filepath.is_relative_to(DATA_DIR.resolve()):
        raise ValueError("Invalid graph path: path traversal detected")

    return filepath
