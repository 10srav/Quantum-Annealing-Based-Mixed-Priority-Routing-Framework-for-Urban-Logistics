"""
Unit tests for QUBO Builder.
"""

import pytest
from src.data_models import Node, Edge, CityGraph, NodeType, TrafficLevel, QUBOParams
from src.qubo_builder import build_qubo, decode_route, validate_route, compute_route_metrics


@pytest.fixture
def simple_graph():
    """Create a simple 4-node graph for testing."""
    nodes = [
        Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
        Node(id="N2", x=1, y=1, type=NodeType.PRIORITY),
        Node(id="N3", x=2, y=0, type=NodeType.NORMAL),
        Node(id="N4", x=2, y=2, type=NodeType.NORMAL),
    ]
    edges = [
        Edge(from_node="N1", to_node="N2", distance=1.41, traffic=TrafficLevel.LOW),
        Edge(from_node="N1", to_node="N3", distance=2.0, traffic=TrafficLevel.MEDIUM),
        Edge(from_node="N2", to_node="N3", distance=1.41, traffic=TrafficLevel.LOW),
        Edge(from_node="N2", to_node="N4", distance=1.41, traffic=TrafficLevel.HIGH),
        Edge(from_node="N3", to_node="N4", distance=2.0, traffic=TrafficLevel.MEDIUM),
    ]
    return CityGraph(
        nodes=nodes,
        edges=edges,
        traffic_multipliers={"low": 1.0, "medium": 1.5, "high": 2.0}
    )


class TestBuildQubo:
    """Tests for QUBO construction."""
    
    def test_qubo_has_correct_num_variables(self, simple_graph):
        """QUBO should have n^2 variables for n nodes."""
        bqm = build_qubo(simple_graph)
        n = len(simple_graph.nodes)
        assert len(bqm.variables) == n * n
    
    def test_qubo_variable_naming(self, simple_graph):
        """Variables should be named x_{node_id}_{position}."""
        bqm = build_qubo(simple_graph)
        assert "x_N1_0" in bqm.variables
        assert "x_N2_1" in bqm.variables
        assert "x_N4_3" in bqm.variables
    
    def test_qubo_with_custom_params(self, simple_graph):
        """QUBO should accept custom penalty parameters."""
        params = QUBOParams(A=200, B=1000, Bp=2000, C=0.5)
        bqm = build_qubo(simple_graph, params)
        assert bqm is not None
    
    def test_priority_constraint_penalties(self, simple_graph):
        """Priority nodes in wrong positions should have high penalties."""
        bqm = build_qubo(simple_graph)
        # Priority node (N1) in position 2 (normal position) should have penalty
        assert bqm.get_linear("x_N1_2") > 0
        # Normal node (N3) in position 0 (priority position) should have penalty
        assert bqm.get_linear("x_N3_0") > 0


class TestDecodeRoute:
    """Tests for route decoding."""
    
    def test_decode_valid_sample(self):
        """Should decode a valid sample to ordered route."""
        sample = {
            "x_N1_0": 1, "x_N1_1": 0, "x_N1_2": 0, "x_N1_3": 0,
            "x_N2_0": 0, "x_N2_1": 1, "x_N2_2": 0, "x_N2_3": 0,
            "x_N3_0": 0, "x_N3_1": 0, "x_N3_2": 1, "x_N3_3": 0,
            "x_N4_0": 0, "x_N4_1": 0, "x_N4_2": 0, "x_N4_3": 1,
        }
        route = decode_route(sample, ["N1", "N2", "N3", "N4"])
        assert route == ["N1", "N2", "N3", "N4"]
    
    def test_decode_reversed_route(self):
        """Should decode reversed assignment correctly."""
        sample = {
            "x_N1_0": 0, "x_N1_1": 0, "x_N1_2": 0, "x_N1_3": 1,
            "x_N2_0": 0, "x_N2_1": 0, "x_N2_2": 1, "x_N2_3": 0,
            "x_N3_0": 0, "x_N3_1": 1, "x_N3_2": 0, "x_N3_3": 0,
            "x_N4_0": 1, "x_N4_1": 0, "x_N4_2": 0, "x_N4_3": 0,
        }
        route = decode_route(sample, ["N1", "N2", "N3", "N4"])
        assert route == ["N4", "N3", "N2", "N1"]


class TestValidateRoute:
    """Tests for route validation."""
    
    def test_valid_route_with_priority_first(self, simple_graph):
        """Route with priorities first should be valid."""
        route = ["N1", "N2", "N3", "N4"]  # Priorities: N1, N2 first
        feasible, priority_satisfied = validate_route(route, simple_graph)
        assert feasible is True
        assert priority_satisfied is True
    
    def test_invalid_route_priority_not_first(self, simple_graph):
        """Route with priority not first should fail priority check."""
        route = ["N3", "N1", "N2", "N4"]  # Normal N3 before priorities
        feasible, priority_satisfied = validate_route(route, simple_graph)
        assert feasible is True  # Still visits all nodes
        assert priority_satisfied is False  # Priority constraint violated
    
    def test_incomplete_route(self, simple_graph):
        """Route missing nodes should be infeasible."""
        route = ["N1", "N2", "N3"]  # Missing N4
        feasible, priority_satisfied = validate_route(route, simple_graph)
        assert feasible is False


class TestComputeRouteMetrics:
    """Tests for route metric computation."""
    
    def test_compute_simple_route(self, simple_graph):
        """Should compute distance and time for simple route."""
        route = ["N1", "N2"]
        total_distance, travel_time = compute_route_metrics(route, simple_graph)
        
        # N1 -> N2: distance=1.41, traffic=low (1.0x)
        assert total_distance == pytest.approx(1.41)
        assert travel_time == pytest.approx(1.41)
    
    def test_traffic_multiplier_applied(self, simple_graph):
        """Traffic multiplier should affect travel time."""
        route = ["N1", "N3"]  # Medium traffic edge
        total_distance, travel_time = compute_route_metrics(route, simple_graph)
        
        # N1 -> N3: distance=2.0, traffic=medium (1.5x)
        assert total_distance == pytest.approx(2.0)
        assert travel_time == pytest.approx(3.0)  # 2.0 * 1.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
