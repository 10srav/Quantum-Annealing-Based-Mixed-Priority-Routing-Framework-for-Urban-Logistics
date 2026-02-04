"""
Data models for the Quantum Priority Router.
Defines Pydantic models for nodes, edges, graphs, and API request/responses.
"""

from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Literal


class NodeType(str, Enum):
    """Node priority classification."""
    PRIORITY = "priority"
    NORMAL = "normal"


class TrafficLevel(str, Enum):
    """Traffic intensity levels with associated multipliers."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Node(BaseModel):
    """A node in the city graph representing a delivery location."""
    id: str = Field(..., description="Unique node identifier")
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")
    type: NodeType = Field(..., description="Node priority type")
    label: str | None = Field(None, description="Human-readable label")


class Edge(BaseModel):
    """An edge connecting two nodes with distance and traffic info."""
    model_config = ConfigDict(populate_by_name=True)

    from_node: str = Field(..., alias="from", description="Source node ID")
    to_node: str = Field(..., alias="to", description="Target node ID")
    distance: float = Field(..., gt=0, description="Base distance in km")
    traffic: TrafficLevel = Field(..., description="Current traffic level")


class TrafficMultipliers(BaseModel):
    """Traffic level to time multiplier mapping."""
    low: float = 1.0
    medium: float = 1.5
    high: float = 2.0


class CityGraph(BaseModel):
    """Complete city graph with nodes, edges, and traffic configuration."""
    nodes: list[Node] = Field(..., min_length=2)
    edges: list[Edge] = Field(..., min_length=1)
    traffic_multipliers: dict[str, float] = Field(
        default_factory=lambda: {"low": 1.0, "medium": 1.5, "high": 2.0}
    )

    @property
    def priority_nodes(self) -> list[Node]:
        """Get all priority nodes."""
        return [n for n in self.nodes if n.type == NodeType.PRIORITY]

    @property
    def normal_nodes(self) -> list[Node]:
        """Get all normal nodes."""
        return [n for n in self.nodes if n.type == NodeType.NORMAL]

    def get_node(self, node_id: str) -> Node | None:
        """Get node by ID."""
        return next((n for n in self.nodes if n.id == node_id), None)

    def get_edge_weight(self, from_id: str, to_id: str) -> float:
        """Get traffic-weighted edge distance."""
        for edge in self.edges:
            if (edge.from_node == from_id and edge.to_node == to_id) or \
               (edge.from_node == to_id and edge.to_node == from_id):
                multiplier = self.traffic_multipliers.get(edge.traffic.value, 1.0)
                return edge.distance * multiplier
        # If no direct edge, compute Euclidean distance as fallback
        n1, n2 = self.get_node(from_id), self.get_node(to_id)
        if n1 and n2:
            return ((n1.x - n2.x) ** 2 + (n1.y - n2.y) ** 2) ** 0.5
        return float('inf')


class QUBOParams(BaseModel):
    """QUBO penalty coefficients for constraint tuning."""
    A: float = Field(100.0, description="One-hot constraint penalty")
    B: float = Field(500.0, description="Priority ordering penalty")
    Bp: float = Field(1000.0, description="Missing priority penalty")
    C: float = Field(1.0, description="Objective weight (distance)")


class GenerateCityRequest(BaseModel):
    """Validated request for city generation with bounds checking."""
    n_nodes: int = Field(
        default=10,
        ge=2,
        le=25,
        description="Number of nodes to generate (2-25)"
    )
    priority_ratio: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Ratio of priority nodes (0.0-1.0)"
    )
    traffic_profile: Literal["low", "medium", "high", "mixed"] = Field(
        default="mixed",
        description="Traffic intensity profile"
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility"
    )


class SolverRequest(BaseModel):
    """API request for route solving."""
    graph: CityGraph = Field(..., description="City graph to solve")
    solver: Literal["quantum", "greedy"] = Field("quantum", description="Solver type")
    params: QUBOParams | None = Field(None, description="QUBO parameters (quantum only)")


class SolverResponse(BaseModel):
    """API response with solved route and metrics."""
    route: list[str] = Field(..., description="Ordered list of node IDs")
    total_distance: float = Field(..., description="Total route distance (km)")
    travel_time: float = Field(..., description="Traffic-weighted travel time")
    feasible: bool = Field(..., description="Route satisfies all constraints")
    priority_satisfied: bool = Field(..., description="All priorities visited first")
    solve_time_ms: float = Field(..., description="Solver execution time")
    energy: float | None = Field(None, description="QUBO energy (quantum only)")
    solver_used: str = Field(..., description="Solver that produced this result")


class ComparisonResponse(BaseModel):
    """Response comparing quantum vs greedy solutions."""
    quantum: SolverResponse
    greedy: SolverResponse
    distance_reduction_pct: float = Field(..., description="% distance saved by quantum")
    time_reduction_pct: float = Field(..., description="% time saved by quantum")
