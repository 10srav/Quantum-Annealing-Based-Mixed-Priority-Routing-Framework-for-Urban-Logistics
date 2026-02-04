"""
Custom exception classes for the Quantum Priority Router API.

These exceptions provide domain-specific error handling with safe,
user-friendly messages that don't expose internal implementation details.
"""

from fastapi import HTTPException


class GraphNotFoundError(HTTPException):
    """Raised when requested graph file doesn't exist.

    Args:
        graph_name: The name of the graph that was not found.
    """
    def __init__(self, graph_name: str):
        super().__init__(
            status_code=404,
            detail=f"Graph '{graph_name}' not found"
        )


class InvalidGraphNameError(HTTPException):
    """Raised when graph name fails validation.

    Graph names must contain only letters, numbers, hyphens, and underscores
    to prevent path traversal and injection attacks.
    """
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Invalid graph name: use only letters, numbers, hyphens, and underscores"
        )


class NodeLimitExceededError(HTTPException):
    """Raised when node count exceeds maximum allowed.

    Args:
        max_nodes: The maximum number of nodes allowed.
    """
    def __init__(self, max_nodes: int):
        super().__init__(
            status_code=400,
            detail=f"Node count exceeds maximum allowed ({max_nodes})"
        )
