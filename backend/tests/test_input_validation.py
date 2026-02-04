"""
Input Validation Tests for TEST-01.

Comprehensive tests verifying that the API correctly rejects:
- Malformed JSON requests
- Missing required fields
- Out-of-range values
- Invalid enum values

All tests verify 400 responses with helpful error messages.
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def assert_validation_error(response, expected_field: str = None):
    """Assert response is a validation error with optional field check.

    Args:
        response: The HTTP response from TestClient
        expected_field: Optional field name that should appear in the error message
    """
    assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
    data = response.json()
    assert "detail" in data or "errors" in data, f"Expected 'detail' or 'errors' in response: {data}"
    if expected_field:
        response_text = str(data).lower()
        assert expected_field.lower() in response_text, \
            f"Expected '{expected_field}' in error: {data}"


class TestMalformedJSON:
    """Tests for malformed JSON request handling."""

    def test_invalid_json_syntax(self):
        """Invalid JSON syntax should return 400."""
        response = client.post(
            "/solve",
            content="{broken json",
            headers={"Content-Type": "application/json"}
        )
        assert_validation_error(response)

    def test_empty_body(self):
        """Empty request body should return 400."""
        response = client.post(
            "/solve",
            content="",
            headers={"Content-Type": "application/json"}
        )
        assert_validation_error(response)

    def test_null_body(self):
        """Null JSON body should return 400."""
        response = client.post(
            "/solve",
            content="null",
            headers={"Content-Type": "application/json"}
        )
        assert_validation_error(response)

    def test_array_instead_of_object(self):
        """Array instead of object should return 400."""
        response = client.post(
            "/solve",
            content="[]",
            headers={"Content-Type": "application/json"}
        )
        assert_validation_error(response)


class TestMissingFields:
    """Tests for missing required fields."""

    def test_solve_missing_graph(self):
        """POST /solve with empty body should require graph field."""
        response = client.post("/solve", json={})
        assert_validation_error(response, expected_field="graph")

    def test_graph_missing_nodes(self):
        """Graph without nodes should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 1.0, "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="nodes")

    def test_graph_missing_edges(self):
        """Graph without edges should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ]
            }
        })
        assert_validation_error(response, expected_field="edges")

    def test_node_missing_id(self):
        """Node without id field should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 1.0, "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="id")

    def test_node_missing_type(self):
        """Node without type field should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 1.0, "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="type")

    def test_edge_missing_from(self):
        """Edge without from field should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"to": "N2", "distance": 1.0, "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="from")

    def test_edge_missing_distance(self):
        """Edge without distance field should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="distance")


class TestOutOfRangeValues:
    """Tests for out-of-range parameter values."""

    def test_generate_city_n_nodes_too_high(self):
        """n_nodes=30 (max is 25) should return 400."""
        response = client.post("/generate-city", json={"n_nodes": 30})
        assert_validation_error(response, expected_field="n_nodes")
        # Verify error mentions the constraint
        data = response.json()
        response_text = str(data).lower()
        assert "25" in response_text or "less than" in response_text, \
            f"Error should mention max value 25: {data}"

    def test_generate_city_n_nodes_too_low(self):
        """n_nodes=1 (min is 2) should return 400."""
        response = client.post("/generate-city", json={"n_nodes": 1})
        assert_validation_error(response, expected_field="n_nodes")
        # Verify error mentions the constraint
        data = response.json()
        response_text = str(data).lower()
        assert "2" in response_text or "greater than" in response_text, \
            f"Error should mention min value 2: {data}"

    def test_generate_city_n_nodes_zero(self):
        """n_nodes=0 should return 400."""
        response = client.post("/generate-city", json={"n_nodes": 0})
        assert_validation_error(response, expected_field="n_nodes")

    def test_generate_city_n_nodes_negative(self):
        """n_nodes=-5 should return 400."""
        response = client.post("/generate-city", json={"n_nodes": -5})
        assert_validation_error(response, expected_field="n_nodes")

    def test_generate_city_priority_ratio_too_high(self):
        """priority_ratio=1.5 (max is 1.0) should return 400."""
        response = client.post("/generate-city", json={"priority_ratio": 1.5})
        assert_validation_error(response, expected_field="priority_ratio")
        # Verify error mentions the constraint
        data = response.json()
        response_text = str(data).lower()
        assert "1" in response_text or "less than" in response_text, \
            f"Error should mention max value 1.0: {data}"

    def test_generate_city_priority_ratio_negative(self):
        """priority_ratio=-0.1 (min is 0.0) should return 400."""
        response = client.post("/generate-city", json={"priority_ratio": -0.1})
        assert_validation_error(response, expected_field="priority_ratio")

    def test_edge_negative_distance(self):
        """Edge with distance=-1 should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": -1, "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="distance")

    def test_edge_zero_distance(self):
        """Edge with distance=0 should return 400 (gt=0 constraint)."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 0, "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="distance")


class TestInvalidEnumValues:
    """Tests for invalid enum/literal values."""

    def test_invalid_node_type(self):
        """type='urgent' instead of priority/normal should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "urgent"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 1.0, "traffic": "low"}
                ]
            }
        })
        assert_validation_error(response, expected_field="type")

    def test_invalid_traffic_level(self):
        """traffic='extreme' instead of low/medium/high should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 1.0, "traffic": "extreme"}
                ]
            }
        })
        assert_validation_error(response, expected_field="traffic")

    def test_invalid_solver_type(self):
        """solver='neural' instead of quantum/greedy should return 400."""
        response = client.post("/solve", json={
            "graph": {
                "nodes": [
                    {"id": "N1", "x": 0, "y": 0, "type": "priority"},
                    {"id": "N2", "x": 1, "y": 1, "type": "normal"}
                ],
                "edges": [
                    {"from": "N1", "to": "N2", "distance": 1.0, "traffic": "low"}
                ]
            },
            "solver": "neural"
        })
        assert_validation_error(response, expected_field="solver")

    def test_invalid_traffic_profile(self):
        """traffic_profile='extreme' should return 400."""
        response = client.post("/generate-city", json={"traffic_profile": "extreme"})
        assert_validation_error(response, expected_field="traffic_profile")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
