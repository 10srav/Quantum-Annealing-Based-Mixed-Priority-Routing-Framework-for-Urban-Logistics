# System Architecture

## Overview

The Quantum Priority Router is a full-stack application for solving urban logistics routing problems using quantum annealing.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │   MapView    │ │SolverControls│ │ MetricsTable │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                          │                                      │
│                    REST API Calls                               │
└──────────────────────────│──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                          │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │  /solve      │ │  /compare    │ │ /generate    │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│         │                 │                 │                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                    Solver Layer                          │   │
│  │  ┌─────────────┐              ┌─────────────┐           │   │
│  │  │QUBO Builder │              │Greedy Solver│           │   │
│  │  └─────────────┘              └─────────────┘           │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────│──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    D-Wave Leap Cloud                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              LeapHybridSampler                           │   │
│  │     (Quantum-Classical Hybrid Optimization)              │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## Module Descriptions

### Backend Modules

| Module | Purpose |
|--------|---------|
| `data_models.py` | Pydantic schemas for Node, Edge, Graph, Request/Response |
| `qubo_builder.py` | Constructs QUBO from city graph with priority constraints |
| `d_wave_solver.py` | D-Wave LeapHybridSampler integration |
| `greedy_solver.py` | Nearest-neighbor baseline algorithm |
| `metrics.py` | Distance reduction, priority satisfaction metrics |
| `simulator.py` | Random city graph generator |
| `config.py` | Environment-based configuration |

### Frontend Components

| Component | Purpose |
|-----------|---------|
| `MapView` | SVG-based graph visualization |
| `SolverControls` | City generator + solver controls |
| `MetricsTable` | Results comparison table |
| `RouteVisualizer` | Route sequence display |

## Data Flow

### Solving Flow
```
1. User generates city graph (or loads sample)
2. User clicks "Solve" button
3. Frontend sends POST /solve with graph + solver type
4. Backend builds QUBO (if quantum) or runs greedy
5. D-Wave samples QUBO and returns solution
6. Backend decodes route, validates constraints
7. Response sent to frontend with route + metrics
8. UI updates map with highlighted route
```

### Comparison Flow
```
1. User clicks "Compare Both"
2. Frontend sends POST /compare with graph
3. Backend runs both solvers in parallel
4. Results aggregated with distance/time reduction %
5. Side-by-side display in UI
```

## API Endpoints

| Endpoint | Method | Request | Response |
|----------|--------|---------|----------|
| `/health` | GET | - | HealthResponse |
| `/solve` | POST | SolverRequest | SolverResponse |
| `/compare` | POST | CityGraph | ComparisonResponse |
| `/generate-city` | POST | params | CityGraph |
| `/graphs` | GET | - | GraphListResponse |
| `/graphs/{name}` | GET | - | CityGraph |

## Technology Stack

### Backend
- **Python 3.11+**
- **FastAPI** - REST API framework
- **Pydantic** - Data validation
- **D-Wave Ocean SDK** - Quantum annealing
- **dimod** - QUBO construction

### Frontend
- **React 19** + **TypeScript**
- **Vite** - Build tool
- **CSS3** - Styling (no framework)
