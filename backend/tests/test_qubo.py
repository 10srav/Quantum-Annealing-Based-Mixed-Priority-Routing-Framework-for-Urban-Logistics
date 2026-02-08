"""
Unit tests for QUBO Builder.
"""

import pytest
from src.data_models import Node, Edge, CityGraph, NodeType, TrafficLevel, QUBOParams
from src.qubo_builder import build_qubo, decode_route, validate_route, compute_route_metrics, count_priority_violations


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
        """Priority nodes in wrong positions should have higher bias (penalty) than allowed positions."""
        bqm = build_qubo(simple_graph)
        # Priority node (N1) in forbidden position 2 should have higher bias
        # than in allowed position 0 (penalty B is added for forbidden positions)
        assert bqm.get_linear("x_N1_2") > bqm.get_linear("x_N1_0")
        # Normal node (N3) in forbidden position 0 (priority zone) should have
        # higher bias than in allowed position 2
        assert bqm.get_linear("x_N3_0") > bqm.get_linear("x_N3_2")


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


@pytest.fixture
def depot_graph():
    """Create a graph with a depot + 3 delivery nodes."""
    nodes = [
        Node(id="D0", x=5, y=5, type=NodeType.DEPOT),
        Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
        Node(id="N2", x=1, y=1, type=NodeType.NORMAL),
        Node(id="N3", x=2, y=0, type=NodeType.NORMAL),
    ]
    edges = [
        Edge(from_node="D0", to_node="N1", distance=7.07, traffic=TrafficLevel.LOW),
        Edge(from_node="D0", to_node="N2", distance=5.66, traffic=TrafficLevel.LOW),
        Edge(from_node="D0", to_node="N3", distance=5.83, traffic=TrafficLevel.LOW),
        Edge(from_node="N1", to_node="N2", distance=1.41, traffic=TrafficLevel.LOW),
        Edge(from_node="N1", to_node="N3", distance=2.0, traffic=TrafficLevel.MEDIUM),
        Edge(from_node="N2", to_node="N3", distance=1.41, traffic=TrafficLevel.LOW),
    ]
    return CityGraph(
        nodes=nodes,
        edges=edges,
        traffic_multipliers={"low": 1.0, "medium": 1.5, "high": 2.0}
    )


class TestDepotQUBO:
    """Tests for depot handling in QUBO builder."""

    def test_qubo_excludes_depot_variables(self, depot_graph):
        """QUBO should have (n-1)^2 variables when depot is present."""
        bqm = build_qubo(depot_graph)
        delivery_count = len(depot_graph.delivery_nodes)
        assert delivery_count == 3
        assert len(bqm.variables) == delivery_count * delivery_count  # 9, not 16

    def test_qubo_no_depot_variable(self, depot_graph):
        """QUBO variables should not include depot node."""
        bqm = build_qubo(depot_graph)
        for var in bqm.variables:
            assert not var.startswith("x_D0_")

    def test_decode_route_prepends_depot(self):
        """decode_route should prepend depot_id when given."""
        sample = {
            "x_N1_0": 1, "x_N1_1": 0, "x_N1_2": 0,
            "x_N2_0": 0, "x_N2_1": 1, "x_N2_2": 0,
            "x_N3_0": 0, "x_N3_1": 0, "x_N3_2": 1,
        }
        route = decode_route(sample, ["N1", "N2", "N3"], depot_id="D0")
        assert route[0] == "D0"
        assert route == ["D0", "N1", "N2", "N3"]

    def test_decode_route_no_depot(self):
        """decode_route without depot_id should behave as before."""
        sample = {
            "x_N1_0": 1, "x_N1_1": 0,
            "x_N2_0": 0, "x_N2_1": 1,
        }
        route = decode_route(sample, ["N1", "N2"])
        assert route == ["N1", "N2"]

    def test_validate_route_with_depot(self, depot_graph):
        """Validation should pass when depot is at position 0 and priorities are first among delivery nodes."""
        route = ["D0", "N1", "N2", "N3"]
        feasible, priority_satisfied = validate_route(route, depot_graph)
        assert feasible is True
        assert priority_satisfied is True

    def test_validate_route_with_depot_priority_violated(self, depot_graph):
        """Validation should detect priority violation even with depot."""
        route = ["D0", "N2", "N1", "N3"]  # Normal N2 before priority N1
        feasible, priority_satisfied = validate_route(route, depot_graph)
        assert feasible is True
        assert priority_satisfied is False

    def test_count_violations_skips_depot(self, depot_graph):
        """count_priority_violations should skip depot at position 0."""
        # Priority N1 is at delivery position 0 (route position 1) → 0 violations
        route = ["D0", "N1", "N2", "N3"]
        assert count_priority_violations(route, depot_graph) == 0

    def test_count_violations_depot_with_violation(self, depot_graph):
        """count_priority_violations detects priority not in first k delivery positions."""
        # Priority N1 is at delivery position 2 (route position 3) → 1 violation
        route = ["D0", "N2", "N3", "N1"]
        assert count_priority_violations(route, depot_graph) == 1

    def test_single_depot_validator(self):
        """CityGraph should reject multiple depots."""
        nodes = [
            Node(id="D0", x=5, y=5, type=NodeType.DEPOT),
            Node(id="D1", x=3, y=3, type=NodeType.DEPOT),
            Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
        ]
        edges = [
            Edge(from_node="D0", to_node="N1", distance=1.0, traffic=TrafficLevel.LOW),
        ]
        with pytest.raises(ValueError, match="At most 1 depot"):
            CityGraph(nodes=nodes, edges=edges)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
