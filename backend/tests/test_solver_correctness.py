"""
Solver Correctness Tests.

Tests for QUBO constraint verification (TEST-03) and mock sampler completeness (TEST-04).
Verifies one-hot constraints, priority ordering, route completeness, and validation edge cases.
"""

import pytest
from src.data_models import Node, Edge, CityGraph, NodeType, TrafficLevel, QUBOParams
from src.qubo_builder import build_qubo, decode_route, validate_route
from src.qaoa_solver import MockSampler, quantum_solve


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def small_graph():
    """4-node graph: 2 priority, 2 normal."""
    nodes = [
        Node(id="P1", x=0, y=0, type=NodeType.PRIORITY),
        Node(id="P2", x=1, y=0, type=NodeType.PRIORITY),
        Node(id="N1", x=0, y=1, type=NodeType.NORMAL),
        Node(id="N2", x=1, y=1, type=NodeType.NORMAL),
    ]
    edges = [
        Edge(from_node="P1", to_node="P2", distance=1.0, traffic=TrafficLevel.LOW),
        Edge(from_node="P1", to_node="N1", distance=1.0, traffic=TrafficLevel.LOW),
        Edge(from_node="P2", to_node="N2", distance=1.0, traffic=TrafficLevel.LOW),
        Edge(from_node="N1", to_node="N2", distance=1.0, traffic=TrafficLevel.LOW),
        Edge(from_node="P1", to_node="N2", distance=1.41, traffic=TrafficLevel.MEDIUM),
        Edge(from_node="P2", to_node="N1", distance=1.41, traffic=TrafficLevel.MEDIUM),
    ]
    return CityGraph(nodes=nodes, edges=edges)


@pytest.fixture
def large_graph():
    """8-node graph for more thorough testing."""
    # 3 priority, 5 normal nodes in a grid
    nodes = [
        Node(id=f"P{i}", x=i, y=0, type=NodeType.PRIORITY) for i in range(3)
    ] + [
        Node(id=f"N{i}", x=i % 3, y=1 + i // 3, type=NodeType.NORMAL) for i in range(5)
    ]
    # Fully connected for simplicity
    edges = []
    for i, n1 in enumerate(nodes):
        for j, n2 in enumerate(nodes):
            if i < j:
                dist = ((n1.x - n2.x)**2 + (n1.y - n2.y)**2)**0.5
                edges.append(Edge(
                    from_node=n1.id, to_node=n2.id,
                    distance=round(dist, 2), traffic=TrafficLevel.LOW
                ))
    return CityGraph(nodes=nodes, edges=edges)


# =============================================================================
# Helper Functions
# =============================================================================

def verify_one_hot(sample: dict, n_nodes: int) -> tuple[bool, str]:
    """Verify one-hot constraints are satisfied in a sample.

    Returns (satisfied, error_message).
    """
    # Check each position has exactly one node
    for pos in range(n_nodes):
        count = sum(1 for k, v in sample.items()
                    if v == 1 and k.endswith(f"_{pos}"))
        if count != 1:
            return False, f"Position {pos} has {count} nodes (expected 1)"

    # Check each node appears exactly once
    node_counts = {}
    for key, val in sample.items():
        if val == 1:
            parts = key.split("_")
            node_id = "_".join(parts[1:-1])
            node_counts[node_id] = node_counts.get(node_id, 0) + 1

    for node_id, count in node_counts.items():
        if count != 1:
            return False, f"Node {node_id} appears {count} times (expected 1)"

    return True, ""


# =============================================================================
# TEST-03: QUBO One-Hot Constraints
# =============================================================================

class TestQUBOOneHotConstraints:
    """Tests for QUBO one-hot constraint satisfaction."""

    def test_one_hot_per_position(self, small_graph):
        """Verify each position has exactly one node assigned."""
        bqm = build_qubo(small_graph)
        sampler = MockSampler()
        result = sampler.sample(bqm)
        sample = result.first.sample

        n = len(small_graph.nodes)
        for pos in range(n):
            count = sum(1 for k, v in sample.items()
                        if v == 1 and k.endswith(f"_{pos}"))
            assert count == 1, f"Position {pos} has {count} nodes assigned"

    def test_one_hot_per_node(self, small_graph):
        """Verify each node appears at exactly one position."""
        bqm = build_qubo(small_graph)
        sampler = MockSampler()
        result = sampler.sample(bqm)
        sample = result.first.sample

        # Count occurrences of each node
        node_counts = {}
        for key, val in sample.items():
            if val == 1:
                parts = key.split("_")
                node_id = "_".join(parts[1:-1])
                node_counts[node_id] = node_counts.get(node_id, 0) + 1

        for node_id, count in node_counts.items():
            assert count == 1, f"Node {node_id} appears {count} times"

    def test_one_hot_with_mock_sampler(self, small_graph):
        """Run MockSampler, verify one-hot in result."""
        bqm = build_qubo(small_graph)
        sampler = MockSampler()
        result = sampler.sample(bqm)
        sample = result.first.sample

        n = len(small_graph.nodes)
        satisfied, error = verify_one_hot(sample, n)
        assert satisfied, f"One-hot constraint violated: {error}"

    def test_one_hot_large_graph(self, large_graph):
        """Verify one-hot constraints on larger graph."""
        bqm = build_qubo(large_graph)
        sampler = MockSampler()
        result = sampler.sample(bqm)
        sample = result.first.sample

        n = len(large_graph.nodes)
        satisfied, error = verify_one_hot(sample, n)
        assert satisfied, f"One-hot constraint violated: {error}"


# =============================================================================
# TEST-03: Priority Ordering
# =============================================================================

class TestPriorityOrdering:
    """Tests for priority node ordering constraints."""

    def test_priority_nodes_first_in_route(self, small_graph):
        """Verify priority nodes come before normal nodes in route."""
        result = quantum_solve(small_graph, use_mock=True)
        route = result.route

        priority_ids = {n.id for n in small_graph.priority_nodes}
        k = len(priority_ids)

        # First k positions should be priority nodes
        first_k = set(route[:k])
        assert first_k == priority_ids, \
            f"First {k} positions {first_k} should be {priority_ids}"

    def test_all_priority_visited(self, small_graph):
        """Verify all priority nodes are in the route."""
        result = quantum_solve(small_graph, use_mock=True)
        route = result.route

        priority_ids = {n.id for n in small_graph.priority_nodes}
        route_ids = set(route)

        assert priority_ids.issubset(route_ids), \
            f"Missing priority nodes: {priority_ids - route_ids}"

    def test_priority_constraint_penalty(self, small_graph):
        """Verify QUBO penalizes nodes in wrong positions.

        The QUBO coefficients combine multiple terms, so we check that:
        - Priority nodes have higher (less favorable) coefficients in wrong positions
        - Normal nodes have higher (less favorable) coefficients in priority positions
        """
        bqm = build_qubo(small_graph)

        # Priority node (P1) should have higher coefficient in normal positions (2,3)
        # than in priority positions (0,1) - higher = less favorable
        priority_correct = bqm.get_linear("x_P1_0")  # Position 0 (correct)
        priority_wrong = bqm.get_linear("x_P1_2")    # Position 2 (wrong)
        assert priority_wrong > priority_correct, \
            f"Priority node in wrong pos ({priority_wrong}) should have higher " \
            f"coefficient than correct pos ({priority_correct})"

        # Normal node (N1) should have higher coefficient in priority positions (0,1)
        # than in normal positions (2,3) - higher = less favorable
        normal_correct = bqm.get_linear("x_N1_2")   # Position 2 (correct)
        normal_wrong = bqm.get_linear("x_N1_0")     # Position 0 (wrong)
        assert normal_wrong > normal_correct, \
            f"Normal node in priority pos ({normal_wrong}) should have higher " \
            f"coefficient than normal pos ({normal_correct})"

    def test_priority_satisfied_flag(self, small_graph):
        """Verify validate_route returns correct priority_satisfied flag."""
        # Valid priority-first route
        valid_route = ["P1", "P2", "N1", "N2"]
        feasible, priority_satisfied = validate_route(valid_route, small_graph)
        assert feasible is True
        assert priority_satisfied is True

        # Invalid priority order
        invalid_route = ["N1", "P1", "P2", "N2"]
        feasible, priority_satisfied = validate_route(invalid_route, small_graph)
        assert feasible is True  # Still visits all nodes
        assert priority_satisfied is False  # Wrong order

    def test_priority_ordering_large_graph(self, large_graph):
        """Verify priority ordering on larger graph."""
        result = quantum_solve(large_graph, use_mock=True)

        priority_ids = {n.id for n in large_graph.priority_nodes}
        k = len(priority_ids)

        # Check that priority constraint is respected
        assert result.priority_satisfied is True or \
            set(result.route[:k]) == priority_ids


# =============================================================================
# TEST-04: Mock Sampler Completeness
# =============================================================================

class TestMockSamplerCompleteness:
    """Tests that MockSampler produces complete, valid routes."""

    def test_visits_all_nodes_small(self, small_graph):
        """Mock sampler should visit all nodes in small graph."""
        result = quantum_solve(small_graph, use_mock=True)

        node_ids = {n.id for n in small_graph.nodes}
        route_ids = set(result.route)

        assert route_ids == node_ids, \
            f"Route missing nodes: {node_ids - route_ids}"

    def test_visits_all_nodes_large(self, large_graph):
        """Mock sampler should visit all nodes in larger graph."""
        result = quantum_solve(large_graph, use_mock=True)

        node_ids = {n.id for n in large_graph.nodes}
        route_ids = set(result.route)

        assert route_ids == node_ids, \
            f"Route missing nodes: {node_ids - route_ids}"

    def test_no_duplicate_nodes(self, small_graph):
        """Route should not have duplicate nodes."""
        result = quantum_solve(small_graph, use_mock=True)

        assert len(result.route) == len(set(result.route)), \
            f"Route has duplicates: {result.route}"

    def test_feasible_flag_true(self, small_graph):
        """Feasible flag should be True for valid route."""
        result = quantum_solve(small_graph, use_mock=True)
        assert result.feasible is True

    def test_priority_satisfied_true(self, small_graph):
        """Priority satisfied flag should be True when priorities first."""
        result = quantum_solve(small_graph, use_mock=True)
        # Mock sampler uses greedy which should respect priority
        # Verify manually
        priority_ids = {n.id for n in small_graph.priority_nodes}
        k = len(priority_ids)

        # First k nodes should all be priority
        first_k = set(result.route[:k])
        assert first_k == priority_ids or result.priority_satisfied is True

    def test_route_length_equals_node_count(self, small_graph):
        """Route length should equal number of nodes."""
        result = quantum_solve(small_graph, use_mock=True)
        assert len(result.route) == len(small_graph.nodes)

    def test_metrics_are_finite(self, small_graph):
        """Distance and time should be finite for valid route."""
        result = quantum_solve(small_graph, use_mock=True)

        assert result.total_distance < float('inf')
        assert result.travel_time < float('inf')
        assert result.total_distance > 0
        assert result.travel_time > 0


# =============================================================================
# TEST-04: Mock Sampler Determinism
# =============================================================================

class TestMockSamplerDeterminism:
    """Tests for mock sampler behavior consistency."""

    def test_same_graph_same_route(self, small_graph):
        """Same graph should produce same route (deterministic)."""
        result1 = quantum_solve(small_graph, use_mock=True)
        result2 = quantum_solve(small_graph, use_mock=True)

        assert result1.route == result2.route

    def test_energy_is_finite(self, small_graph):
        """QUBO energy should be a finite number."""
        result = quantum_solve(small_graph, use_mock=True)

        assert result.energy is not None
        assert result.energy < float('inf')


# =============================================================================
# Route Validation Edge Cases
# =============================================================================

class TestRouteValidationEdgeCases:
    """Edge case tests for validate_route function."""

    def test_empty_route(self, small_graph):
        """Empty route should be infeasible."""
        feasible, priority_satisfied = validate_route([], small_graph)
        assert feasible is False

    def test_partial_route(self, small_graph):
        """Route missing nodes should be infeasible."""
        partial = ["P1", "P2"]  # Missing N1, N2
        feasible, priority_satisfied = validate_route(partial, small_graph)
        assert feasible is False

    def test_duplicate_nodes_in_route(self, small_graph):
        """Route with duplicates should be infeasible."""
        with_dup = ["P1", "P2", "P1", "N1"]
        feasible, priority_satisfied = validate_route(with_dup, small_graph)
        assert feasible is False

    def test_unknown_node_in_route(self, small_graph):
        """Route with unknown node should be infeasible."""
        unknown = ["P1", "P2", "N1", "UNKNOWN"]
        feasible, priority_satisfied = validate_route(unknown, small_graph)
        assert feasible is False

    def test_priority_violated_but_complete(self, small_graph):
        """Complete route with wrong order should be feasible but priority_satisfied=False."""
        wrong_order = ["N1", "P1", "P2", "N2"]  # Normal before priority
        feasible, priority_satisfied = validate_route(wrong_order, small_graph)
        assert feasible is True  # All nodes visited
        assert priority_satisfied is False  # Wrong order

    def test_all_priority_graph(self):
        """Graph with only priority nodes should work."""
        nodes = [
            Node(id="P1", x=0, y=0, type=NodeType.PRIORITY),
            Node(id="P2", x=1, y=0, type=NodeType.PRIORITY),
        ]
        edges = [Edge(from_node="P1", to_node="P2", distance=1.0, traffic=TrafficLevel.LOW)]
        graph = CityGraph(nodes=nodes, edges=edges)

        feasible, priority_satisfied = validate_route(["P1", "P2"], graph)
        assert feasible is True
        assert priority_satisfied is True

    def test_all_normal_graph(self):
        """Graph with only normal nodes should work."""
        nodes = [
            Node(id="N1", x=0, y=0, type=NodeType.NORMAL),
            Node(id="N2", x=1, y=0, type=NodeType.NORMAL),
        ]
        edges = [Edge(from_node="N1", to_node="N2", distance=1.0, traffic=TrafficLevel.LOW)]
        graph = CityGraph(nodes=nodes, edges=edges)

        feasible, priority_satisfied = validate_route(["N1", "N2"], graph)
        assert feasible is True
        assert priority_satisfied is True  # No priority nodes to violate


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
