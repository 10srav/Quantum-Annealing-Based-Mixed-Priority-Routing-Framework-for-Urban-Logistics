"""
Unit tests for Greedy Solver.
"""

import pytest
from src.data_models import Node, Edge, CityGraph, NodeType, TrafficLevel
from src.greedy_solver import greedy_solve


@pytest.fixture
def simple_graph():
    """Create a simple test graph."""
    nodes = [
        Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
        Node(id="N2", x=2, y=0, type=NodeType.PRIORITY),
        Node(id="N3", x=1, y=2, type=NodeType.NORMAL),
        Node(id="N4", x=3, y=2, type=NodeType.NORMAL),
    ]
    edges = [
        Edge(from_node="N1", to_node="N2", distance=2.0, traffic=TrafficLevel.LOW),
        Edge(from_node="N1", to_node="N3", distance=2.24, traffic=TrafficLevel.MEDIUM),
        Edge(from_node="N2", to_node="N3", distance=2.24, traffic=TrafficLevel.LOW),
        Edge(from_node="N2", to_node="N4", distance=2.24, traffic=TrafficLevel.LOW),
        Edge(from_node="N3", to_node="N4", distance=2.0, traffic=TrafficLevel.MEDIUM),
    ]
    return CityGraph(
        nodes=nodes,
        edges=edges,
        traffic_multipliers={"low": 1.0, "medium": 1.5, "high": 2.0}
    )


class TestGreedySolver:
    """Tests for greedy solver."""
    
    def test_greedy_returns_all_nodes(self, simple_graph):
        """Greedy should visit all nodes."""
        result = greedy_solve(simple_graph)
        assert len(result.route) == len(simple_graph.nodes)
        assert set(result.route) == {"N1", "N2", "N3", "N4"}
    
    def test_greedy_priority_first(self, simple_graph):
        """All priority nodes should appear before normal nodes."""
        result = greedy_solve(simple_graph)
        
        priority_ids = {"N1", "N2"}
        normal_ids = {"N3", "N4"}
        
        # Find positions of priority and normal nodes
        priority_positions = [i for i, n in enumerate(result.route) if n in priority_ids]
        normal_positions = [i for i, n in enumerate(result.route) if n in normal_ids]
        
        # All priority positions should be before all normal positions
        assert max(priority_positions) < min(normal_positions)
    
    def test_greedy_is_feasible(self, simple_graph):
        """Greedy result should always be feasible."""
        result = greedy_solve(simple_graph)
        assert result.feasible is True
    
    def test_greedy_priority_satisfied(self, simple_graph):
        """Greedy should always satisfy priority constraint."""
        result = greedy_solve(simple_graph)
        assert result.priority_satisfied is True
    
    def test_greedy_returns_metrics(self, simple_graph):
        """Greedy should return distance and time metrics."""
        result = greedy_solve(simple_graph)
        assert result.total_distance > 0
        assert result.travel_time > 0
        assert result.solve_time_ms >= 0
    
    def test_greedy_solver_name(self, simple_graph):
        """Result should indicate greedy solver was used."""
        result = greedy_solve(simple_graph)
        assert result.solver_used == "greedy"


class TestGreedyWithAllPriority:
    """Tests with all priority nodes."""
    
    def test_all_priority_nodes(self):
        """Should work with all priority nodes."""
        nodes = [
            Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
            Node(id="N2", x=1, y=0, type=NodeType.PRIORITY),
            Node(id="N3", x=2, y=0, type=NodeType.PRIORITY),
        ]
        edges = [
            Edge(from_node="N1", to_node="N2", distance=1.0, traffic=TrafficLevel.LOW),
            Edge(from_node="N2", to_node="N3", distance=1.0, traffic=TrafficLevel.LOW),
        ]
        graph = CityGraph(nodes=nodes, edges=edges)
        
        result = greedy_solve(graph)
        assert len(result.route) == 3
        assert result.feasible is True


class TestGreedyWithAllNormal:
    """Tests with all normal nodes."""
    
    def test_all_normal_nodes(self):
        """Should work with all normal nodes."""
        nodes = [
            Node(id="N1", x=0, y=0, type=NodeType.NORMAL),
            Node(id="N2", x=1, y=0, type=NodeType.NORMAL),
            Node(id="N3", x=2, y=0, type=NodeType.NORMAL),
        ]
        edges = [
            Edge(from_node="N1", to_node="N2", distance=1.0, traffic=TrafficLevel.LOW),
            Edge(from_node="N2", to_node="N3", distance=1.0, traffic=TrafficLevel.LOW),
        ]
        graph = CityGraph(nodes=nodes, edges=edges)
        
        result = greedy_solve(graph)
        assert len(result.route) == 3
        assert result.feasible is True
        assert result.priority_satisfied is True  # No priorities to satisfy


class TestGreedyWithDepot:
    """Tests for greedy solver with depot node."""

    @pytest.fixture
    def depot_graph(self):
        nodes = [
            Node(id="D0", x=5, y=5, type=NodeType.DEPOT),
            Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
            Node(id="N2", x=1, y=0, type=NodeType.NORMAL),
            Node(id="N3", x=2, y=0, type=NodeType.NORMAL),
        ]
        edges = [
            Edge(from_node="D0", to_node="N1", distance=7.07, traffic=TrafficLevel.LOW),
            Edge(from_node="D0", to_node="N2", distance=5.10, traffic=TrafficLevel.LOW),
            Edge(from_node="D0", to_node="N3", distance=5.83, traffic=TrafficLevel.LOW),
            Edge(from_node="N1", to_node="N2", distance=1.0, traffic=TrafficLevel.LOW),
            Edge(from_node="N2", to_node="N3", distance=1.0, traffic=TrafficLevel.LOW),
        ]
        return CityGraph(nodes=nodes, edges=edges)

    def test_greedy_starts_from_depot(self, depot_graph):
        """Greedy solver should start from depot when present."""
        result = greedy_solve(depot_graph)
        assert result.route[0] == "D0"

    def test_greedy_visits_all_nodes_with_depot(self, depot_graph):
        """Greedy should visit all nodes including depot."""
        result = greedy_solve(depot_graph)
        assert set(result.route) == {"D0", "N1", "N2", "N3"}
        assert len(result.route) == 4

    def test_greedy_depot_id_in_response(self, depot_graph):
        """Response should include depot_id."""
        result = greedy_solve(depot_graph)
        assert result.depot_id == "D0"

    def test_greedy_no_depot_id_without_depot(self, simple_graph):
        """Response should have None depot_id when no depot."""
        result = greedy_solve(simple_graph)
        assert result.depot_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
