"""
API Integration Tests.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""
    
    def test_health_returns_200(self):
        """Health endpoint should return 200."""
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_response_structure(self):
        """Health response should have expected structure."""
        response = client.get("/health")
        data = response.json()
        
        assert "status" in data
        assert "service" in data
        assert "qaoa_info" in data


class TestSolveEndpoint:
    """Tests for solve endpoint."""
    
    @pytest.fixture
    def sample_request(self):
        """Sample solve request."""
        return {
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "priority"},
                    {"id": "N3", "x": 2, "y": 0, "type": "normal"},
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 1.41, "traffic": "low"},
                    {"from": "N2", "to": "N3", "distance": 1.41, "traffic": "medium"},
                ],
                "traffic_multipliers": {"low": 1.0, "medium": 1.5, "high": 2.0}
            },
            "solver": "greedy"
        }
    
    def test_solve_greedy_returns_200(self, sample_request):
        """Greedy solve should return 200."""
        response = client.post("/solve", json=sample_request)
        assert response.status_code == 200
    
    def test_solve_returns_route(self, sample_request):
        """Solve should return a route."""
        response = client.post("/solve", json=sample_request)
        data = response.json()
        
        assert "route" in data
        assert len(data["route"]) == 3
        assert set(data["route"]) == {"N1", "N2", "N3"}
    
    def test_solve_returns_metrics(self, sample_request):
        """Solve should return metrics."""
        response = client.post("/solve", json=sample_request)
        data = response.json()
        
        assert "total_distance" in data
        assert "travel_time" in data
        assert "feasible" in data
        assert "priority_satisfied" in data
        assert "solve_time_ms" in data
    
    def test_solve_quantum_mock(self, sample_request):
        """Quantum solve should work in mock mode."""
        sample_request["solver"] = "quantum"
        response = client.post("/solve", json=sample_request)
        assert response.status_code == 200


class TestCompareEndpoint:
    """Tests for compare endpoint."""
    
    @pytest.fixture
    def sample_graph(self):
        """Sample graph for comparison."""
        return {
            "nodes": [
                {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                {"id": "N2", "x": 1, "y": 1, "type": "normal"},
            ],
            "edges": [
                {"from": "N1", "to": "N2", "distance": 1.41, "traffic": "low"},
            ],
            "traffic_multipliers": {"low": 1.0, "medium": 1.5, "high": 2.0}
        }
    
    def test_compare_returns_200(self, sample_graph):
        """Compare should return 200."""
        response = client.post("/compare", json=sample_graph)
        assert response.status_code == 200
    
    def test_compare_returns_both_results(self, sample_graph):
        """Compare should return both quantum and greedy results."""
        response = client.post("/compare", json=sample_graph)
        data = response.json()
        
        assert "quantum" in data
        assert "greedy" in data
        assert "distance_reduction_pct" in data
        assert "time_reduction_pct" in data


class TestGenerateCityEndpoint:
    """Tests for city generation endpoint."""
    
    def test_generate_returns_200(self):
        """Generate should return 200."""
        response = client.post("/generate-city?n_nodes=5")
        assert response.status_code == 200
    
    def test_generate_returns_correct_node_count(self):
        """Generate should return requested number of nodes."""
        response = client.post("/generate-city?n_nodes=8")
        data = response.json()
        
        assert len(data["nodes"]) == 8
    
    def test_generate_includes_edges(self):
        """Generate should include edges."""
        response = client.post("/generate-city?n_nodes=5")
        data = response.json()
        
        assert "edges" in data
        assert len(data["edges"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
