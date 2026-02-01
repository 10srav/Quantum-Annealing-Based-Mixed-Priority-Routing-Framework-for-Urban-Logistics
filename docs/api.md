# API Documentation

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

Check API and D-Wave connection status.

```http
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "service": "quantum-priority-router",
  "dwave_info": {
    "available": true,
    "mode": "mock",
    "solver": "MockSampler"
  }
}
```

---

### Solve Route

Solve routing problem with specified solver.

```http
POST /solve
Content-Type: application/json
```

**Request Body:**
```json
{
  "graph": {
    "nodes": [
      {"id": "N1", "x": 0, "y": 0, "type": "priority"},
      {"id": "N2", "x": 2, "y": 1, "type": "normal"}
    ],
    "edges": [
      {"from": "N1", "to": "N2", "distance": 2.24, "traffic": "low"}
    ],
    "traffic_multipliers": {"low": 1.0, "medium": 1.5, "high": 2.0}
  },
  "solver": "quantum",
  "params": {
    "A": 100,
    "B": 500,
    "Bp": 1000,
    "C": 1.0
  }
}
```

**Parameters:**
| Field | Type | Description |
|-------|------|-------------|
| `graph` | CityGraph | City graph with nodes and edges |
| `solver` | string | `"quantum"` or `"greedy"` |
| `params` | QUBOParams | Optional QUBO penalties |

**Response:**
```json
{
  "route": ["N1", "N2"],
  "total_distance": 2.24,
  "travel_time": 2.24,
  "feasible": true,
  "priority_satisfied": true,
  "solve_time_ms": 125.5,
  "energy": -42.5,
  "solver_used": "quantum_mock"
}
```

---

### Compare Solvers

Run both quantum and greedy solvers and compare results.

```http
POST /compare
Content-Type: application/json
```

**Request Body:** CityGraph (same as solve endpoint's `graph` field)

**Response:**
```json
{
  "quantum": { ... },
  "greedy": { ... },
  "distance_reduction_pct": 12.5,
  "time_reduction_pct": 18.3
}
```

---

### Generate Random City

Create a random city graph for testing.

```http
POST /generate-city?n_nodes=10&priority_ratio=0.3&traffic_profile=mixed
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `n_nodes` | int | 8 | Number of nodes |
| `priority_ratio` | float | 0.3 | Fraction of priority nodes |
| `traffic_profile` | string | "mixed" | `"low"`, `"mixed"`, or `"high"` |
| `seed` | int | None | Random seed for reproducibility |

**Response:** CityGraph object

---

### List Sample Graphs

Get list of available sample graphs.

```http
GET /graphs
```

**Response:**
```json
{
  "graphs": ["example_city", "small_grid", "dense_network"]
}
```

---

### Get Sample Graph

Load a specific sample graph.

```http
GET /graphs/{name}
```

**Response:** CityGraph object

---

## Data Models

### Node

```typescript
{
  id: string;      // Unique identifier (e.g., "N1")
  x: number;       // X coordinate
  y: number;       // Y coordinate
  type: "priority" | "normal";
  label?: string;  // Optional human-readable label
}
```

### Edge

```typescript
{
  from: string;    // Source node ID
  to: string;      // Target node ID
  distance: number;
  traffic: "low" | "medium" | "high";
}
```

### CityGraph

```typescript
{
  nodes: Node[];
  edges: Edge[];
  traffic_multipliers: {
    low: number;    // Default: 1.0
    medium: number; // Default: 1.5
    high: number;   // Default: 2.0
  }
}
```

### QUBOParams

```typescript
{
  A: number;   // One-hot constraint penalty (default: 100)
  B: number;   // Priority ordering penalty (default: 500)
  Bp: number;  // Missing priority penalty (default: 1000)
  C: number;   // Objective weight (default: 1.0)
}
```

---

## Error Responses

```json
{
  "detail": "Error message describing what went wrong"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request - Invalid input data |
| 404 | Not Found - Graph/resource not found |
| 500 | Internal Server Error |
