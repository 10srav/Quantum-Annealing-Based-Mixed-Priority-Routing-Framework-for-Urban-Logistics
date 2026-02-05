# Quantum-Annealing Mixed-Priority Routing Framework

A quantum-classical hybrid routing optimization system for urban logistics with mixed-priority delivery nodes. Combines QAOA (Quantum Approximate Optimization Algorithm) via Qiskit with classical greedy heuristics, wrapped in a full-stack application with interactive map visualization.

## Key Features

- **QAOA Quantum Solver** - QUBO-formulated route optimization using Qiskit's StatevectorSampler (Qiskit 2.x compatible), with a mock mode for environments without quantum hardware
- **Classical Greedy Solver** - Two-phase nearest-neighbor heuristic that enforces priority-first ordering
- **Priority-Constrained Routing** - All priority nodes (hospitals, emergency centers) are guaranteed to be visited before normal nodes
- **Traffic-Aware Optimization** - Edge weights adjusted by configurable traffic multipliers (low/medium/high)
- **Interactive Map UI** - OpenStreetMap-based interface with click-to-add delivery points and OSRM real road routing
- **Solver Comparison** - Side-by-side quantum vs. greedy metrics (distance, time, feasibility, energy)
- **Production-Ready Backend** - API key auth, rate limiting, structured logging, CORS configuration, graceful shutdown

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Quantum** | Qiskit 2.x, qiskit-optimization, qiskit-algorithms, dimod |
| **Backend** | Python 3.11+, FastAPI, Pydantic v2, NetworkX, NumPy |
| **Frontend** | React 19, TypeScript, Vite 7, Leaflet, React Leaflet, Leaflet Routing Machine |
| **Infrastructure** | Docker (multi-stage builds), Docker Compose (dev + production profiles) |
| **Testing** | pytest, pytest-asyncio, httpx |

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- (Optional) D-Wave Leap account for quantum annealing

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt

# Configure environment (copy and edit)
cp .env.example .env

# Run server
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The UI will be available at `http://localhost:5173`.

### Docker (Development)

```bash
docker-compose up
```

### Docker (Production)

```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

Production profile adds resource limits (CPU/memory), graceful shutdown (35s grace period), and sets `ENVIRONMENT=production`.

## API Endpoints

| Endpoint | Method | Auth | Rate Limit | Description |
|----------|--------|------|------------|-------------|
| `/health` | GET | No | 60/min | Health check with dependency status |
| `/solve` | POST | Yes | 10/min | Solve routing problem (quantum or greedy) |
| `/compare` | POST | Yes | 10/min | Compare quantum vs. greedy solvers |
| `/generate-city` | POST | Yes | 60/min | Generate random city graph |
| `/graphs` | GET | Yes | 60/min | List available sample graphs |
| `/graphs/{name}` | GET | Yes | 60/min | Get a specific sample graph |

Authentication uses an `X-API-Key` header. The key is validated against a SHA-256 hash stored in the `API_KEY_HASH` environment variable.

## QUBO Formulation

The quantum solver encodes the routing problem as a Quadratic Unconstrained Binary Optimization (QUBO) with four constraint terms:

| Constraint | Penalty | Default | Purpose |
|-----------|---------|---------|---------|
| One-hot | A | 100.0 | Exactly one node per route position |
| Uniqueness | B | 500.0 | Each node visited exactly once |
| Priority ordering | Bp | 1000.0 | Priority nodes before normal nodes |
| Distance objective | C | 1.0 | Minimize traffic-weighted travel distance |

See [docs/qubo_math.md](docs/qubo_math.md) for the full mathematical formulation.

## Configuration

### Backend Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `QAOA_USE_MOCK` | `false` | Use mock solver (no quantum hardware needed) |
| `QAOA_REPS` | `2` | Number of QAOA circuit layers |
| `QAOA_SHOTS` | `1024` | Measurement shots per run |
| `API_KEY_HASH` | `""` | SHA-256 hash of the API key |
| `CORS_ORIGINS` | `localhost:5173,3000` | Allowed CORS origins (JSON array or CSV) |
| `RATE_LIMIT_PER_MINUTE` | `60` | General endpoint rate limit |
| `RATE_LIMIT_SOLVER_PER_MINUTE` | `10` | Solver endpoint rate limit |
| `SOLVER_TIMEOUT_SECONDS` | `30` | Max solver execution time |
| `SHUTDOWN_TIMEOUT` | `30` | Graceful shutdown wait (seconds) |
| `LOG_LEVEL` | `INFO` | Logging verbosity |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DWAVE_API_TOKEN` | - | D-Wave Leap API token (if using D-Wave) |

### Frontend Environment Variables

| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API base URL |
| `VITE_API_KEY` | API key for authentication |

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI application & routes
│   │   ├── middleware.py         # Request context & logging middleware
│   │   ├── logging_config.py    # Structured JSON logging
│   │   └── exceptions.py        # Exception handlers
│   ├── src/
│   │   ├── qaoa_solver.py       # QAOA quantum solver (real + mock)
│   │   ├── greedy_solver.py     # Greedy nearest-neighbor solver
│   │   ├── qubo_builder.py      # QUBO matrix construction
│   │   ├── data_models.py       # Pydantic models
│   │   ├── config.py            # Environment configuration
│   │   ├── auth.py              # API key authentication
│   │   ├── security.py          # Path traversal protection
│   │   ├── rate_limit.py        # Rate limiting
│   │   ├── metrics.py           # Route metrics computation
│   │   └── simulator.py         # Random city graph generator
│   ├── tests/
│   │   ├── test_api.py
│   │   ├── test_qubo.py
│   │   ├── test_greedy.py
│   │   ├── test_input_validation.py
│   │   ├── test_security.py
│   │   └── test_solver_correctness.py
│   ├── Dockerfile               # Multi-stage production build
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── App.tsx              # Root component
│   │   ├── components/
│   │   │   ├── InteractiveMap.tsx    # OSM map with OSRM routing
│   │   │   ├── SolverControls.tsx   # City generator & solver UI
│   │   │   ├── MetricsTable.tsx     # Results comparison table
│   │   │   ├── RouteVisualizer.tsx  # Route sequence display
│   │   │   └── MetricsChart.tsx     # Performance charts
│   │   ├── hooks/
│   │   │   └── useSolver.ts     # Solver state management
│   │   └── lib/
│   │       ├── api.ts           # API client
│   │       ├── config.ts        # Frontend configuration
│   │       └── types.ts         # TypeScript interfaces
│   ├── Dockerfile
│   └── package.json
├── data/
│   └── example_city.json        # Sample 8-node city graph
├── docs/
│   ├── api.md                   # API documentation
│   ├── architecture.md          # System architecture
│   ├── setup.md                 # Setup guide
│   ├── specification.md         # Requirements specification
│   ├── qubo_math.md             # QUBO mathematical formulation
│   └── qubo_design.md           # QUBO design decisions
├── docker-compose.yml           # Development compose
├── docker-compose.prod.yml      # Production compose override
└── README.md
```

## Testing

```bash
cd backend
pytest tests/ -v
```

Tests cover API endpoints, QUBO construction, greedy solver correctness, input validation, security (path traversal, auth), and solver constraint satisfaction.

## Documentation

Detailed documentation is available in the [docs/](docs/) directory:

- [API Reference](docs/api.md) - Endpoint details with request/response examples
- [Architecture](docs/architecture.md) - System design and data flow
- [Setup Guide](docs/setup.md) - Installation and development setup
- [Specification](docs/specification.md) - Problem definition and requirements
- [QUBO Mathematics](docs/qubo_math.md) - Constraint formulation details
- [QUBO Design](docs/qubo_design.md) - Design decisions and trade-offs

## License

MIT
