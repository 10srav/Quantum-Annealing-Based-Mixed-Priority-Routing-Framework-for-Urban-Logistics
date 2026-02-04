# Testing Patterns

**Analysis Date:** 2026-02-04

## Test Framework

**Runner:**
- pytest 7.4.0+
- Config: No explicit pytest.ini or pyproject.toml configuration found
- Async support: pytest-asyncio 0.23.0 for FastAPI tests

**Assertion Library:**
- pytest built-in assertions
- pytest.approx() for floating-point comparisons

**Run Commands:**
```bash
pytest backend/tests/                    # Run all backend tests
pytest backend/tests/test_greedy.py -v  # Run specific test file with verbose output
pytest backend/tests/ -k "test_solve"    # Run tests matching pattern
pytest tests/                            # Run with coverage
```

## Test File Organization

**Location:**
- Backend: co-located in `backend/tests/` directory (separate from source)
- Frontend: No tests found in repository

**Naming:**
- Test files: `test_*.py` prefix convention
- Test files: `backend/tests/test_api.py`, `backend/tests/test_greedy.py`, `backend/tests/test_qubo.py`
- Test classes: `TestX` prefix. Examples: `TestGreedySolver`, `TestHealthEndpoint`, `TestBuildQubo`
- Test methods: `test_*` prefix. Examples: `test_greedy_returns_all_nodes()`, `test_solve_returns_200()`

**Structure:**
```
backend/
├── tests/
│   ├── __init__.py
│   ├── test_api.py           # FastAPI integration tests
│   ├── test_greedy.py        # Greedy solver unit tests
│   └── test_qubo.py          # QUBO builder unit tests
└── src/
    ├── data_models.py
    ├── greedy_solver.py
    ├── qaoa_solver.py
    └── ...
```

## Test Structure

**Suite Organization:**

```python
class TestGreedySolver:
    """Tests for greedy solver."""

    def test_greedy_returns_all_nodes(self, simple_graph):
        """Greedy should visit all nodes."""
        result = greedy_solve(simple_graph)
        assert len(result.route) == len(simple_graph.nodes)
        assert set(result.route) == {"N1", "N2", "N3", "N4"}
```

**Patterns:**
- Fixtures for test data: `@pytest.fixture` decorator, reusable across test methods
- Fixture example from `test_greedy.py`:
  ```python
  @pytest.fixture
  def simple_graph():
      """Create a simple test graph."""
      nodes = [
          Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
          Node(id="N2", x=2, y=0, type=NodeType.PRIORITY),
          # ...
      ]
      edges = [
          Edge(from_node="N1", to_node="N2", distance=2.0, traffic=TrafficLevel.LOW),
          # ...
      ]
      return CityGraph(nodes=nodes, edges=edges, traffic_multipliers={...})
  ```
- Fixture injection: fixtures passed as parameters to test functions
- Setup/teardown: minimal, handled by fixture return values
- No explicit teardown needed (no external resources)

## Mocking

**Framework:** No explicit mocking library (unittest.mock) used
- Mock sampler implemented in source code: `MockSampler` class in `backend/src/qaoa_solver.py`
- TestClient from FastAPI used for API testing

**Patterns:**
- API integration tests use `TestClient(app)` to test routes directly
- Example from `test_api.py`:
  ```python
  from fastapi.testclient import TestClient
  from app.main import app

  client = TestClient(app)

  class TestHealthEndpoint:
      def test_health_returns_200(self):
          response = client.get("/health")
          assert response.status_code == 200
  ```
- Request fixtures: payload data as dictionaries, passed to `client.post(..., json=sample_request)`

**What to Mock:**
- External API calls (not present in current codebase)
- Quantum hardware (handled by `qaoa_use_mock` configuration flag)
- File I/O (not mocked, used directly in tests)

**What NOT to Mock:**
- Solver logic (greedy_solve, build_qubo tested directly)
- Data models (tested with real Pydantic objects)
- Route validation (tested with actual route data)
- FastAPI routes (tested with TestClient which runs real app)

## Fixtures and Factories

**Test Data:**
```python
@pytest.fixture
def simple_graph():
    """Create a simple test graph."""
    nodes = [
        Node(id="N1", x=0, y=0, type=NodeType.PRIORITY),
        Node(id="N2", x=1, y=1, type=NodeType.PRIORITY),
        Node(id="N3", x=2, y=0, type=NodeType.NORMAL),
        Node(id="N4", x=2, y=2, type=NodeType.NORMAL),
    ]
    edges = [
        Edge(from_node="N1", to_node="N2", distance=1.41, traffic=TrafficLevel.LOW),
        Edge(from_node="N2", to_node="N3", distance=1.41, traffic=TrafficLevel.LOW),
        Edge(from_node="N2", to_node="N4", distance=1.41, traffic=TrafficLevel.HIGH),
        Edge(from_node="N3", to_node="N4", distance=2.0, traffic=TrafficLevel.MEDIUM),
    ]
    return CityGraph(
        nodes=nodes,
        edges=edges,
        traffic_multipliers={"low": 1.0, "medium": 1.5, "high": 2.0}
    )
```

**Location:**
- Fixtures defined in test files using @pytest.fixture decorator
- Separate fixture classes not used (fixtures are module-level functions)
- Reused across multiple test classes by passing fixture parameter

## Coverage

**Requirements:** Not enforced (no coverage config found)

**View Coverage:**
```bash
pytest backend/tests/ --cov=src --cov-report=html
```

## Test Types

**Unit Tests:**
- Scope: Individual functions and classes (greedy_solve, build_qubo, validate_route)
- Location: `backend/tests/test_greedy.py`, `backend/tests/test_qubo.py`
- Approach: Test single function with various inputs
- Example: `test_greedy_returns_all_nodes()` tests that greedy solver visits all nodes
- Isolation: Fixtures provide test data, no external dependencies
- Assertions: Multiple assertions per test checking different properties

**Integration Tests:**
- Scope: Full API endpoints and request/response handling
- Location: `backend/tests/test_api.py`
- Approach: Use TestClient to make HTTP requests to actual FastAPI app
- Example: `test_solve_greedy_returns_200()` tests endpoint behavior
- Testing flow: client.post() → response.json() → assertions on data structure
- No database integration (in-memory only)

**E2E Tests:**
- Framework: Not implemented
- Status: No end-to-end tests for full user workflows
- Missing: Tests for frontend components, user interaction flows

## Common Patterns

**Async Testing:**
```python
# pytest-asyncio is installed but no async tests found in current codebase
# API tests use sync TestClient (FastAPI handles async under the hood)
# Pattern if async tests needed:
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result == expected
```

**Error Testing:**
```python
def test_solve_returns_metrics(self, sample_request):
    """Solve should return metrics."""
    response = client.post("/solve", json=sample_request)
    data = response.json()

    assert "total_distance" in data
    assert "travel_time" in data
    assert "feasible" in data
    assert "priority_satisfied" in data
    assert "solve_time_ms" in data
```

**Floating-Point Assertion:**
```python
def test_compute_simple_route(self, simple_graph):
    """Should compute distance and time for simple route."""
    route = ["N1", "N2"]
    total_distance, travel_time = compute_route_metrics(route, simple_graph)

    # N1 -> N2: distance=1.41, traffic=low (1.0x)
    assert total_distance == pytest.approx(1.41)
    assert travel_time == pytest.approx(1.41)
```

**Constraint Validation:**
```python
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
```

## Test Coverage Summary

**Well Tested:**
- Greedy solver algorithm: routing, priority constraints, distance/time calculations
- QUBO builder: variable naming, constraint penalties, route decoding/validation
- API endpoints: health, solve (both quantum and greedy), compare, generate-city
- Route metrics: distance computation, traffic multiplier application

**Not Tested:**
- React components (no frontend tests)
- QAOA solver implementation (quantum-specific, relies on Qiskit)
- Error cases in QAOA (only success path tested via mock)
- Configuration loading
- Edge cases: empty graphs, single-node graphs, missing edges
- Concurrent requests
- Backend performance/scaling

## Test Execution Pattern

**Running All Tests:**
```bash
cd backend
pytest tests/ -v
```

**Running Specific Test Class:**
```bash
pytest tests/test_greedy.py::TestGreedySolver -v
```

**Running Single Test:**
```bash
pytest tests/test_greedy.py::TestGreedySolver::test_greedy_returns_all_nodes -v
```

**Test Discovery:**
- pytest automatically discovers files matching `test_*.py` or `*_test.py`
- Tests within files discovered if functions/methods match `test_*` pattern
- Class-based tests must have `Test` prefix

---

*Testing analysis: 2026-02-04*
