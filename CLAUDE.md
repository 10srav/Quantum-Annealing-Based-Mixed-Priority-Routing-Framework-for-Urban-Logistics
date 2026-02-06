# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Quantum-classical hybrid routing optimization for urban logistics with mixed-priority delivery nodes. Uses QAOA (Quantum Approximate Optimization Algorithm) via Qiskit with a fallback mock mode, plus a classical greedy baseline solver.

## Build & Run Commands

### Backend (FastAPI + Python)
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

pip install -r requirements.txt
cp .env.example .env         # Configure environment
uvicorn app.main:app --reload
```
API runs at `http://localhost:8000`

### Frontend (React + Vite)
```bash
cd frontend
npm install
npm run dev
```
UI runs at `http://localhost:5173`

### Testing
```bash
cd backend
pytest tests/ -v                     # All tests
pytest tests/test_qubo.py -v         # Specific test file
pytest tests/ -k "test_priority" -v  # Tests matching pattern
```

### Docker
```bash
docker-compose up                                          # Development
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up  # Production
```

### Linting
```bash
cd frontend && npm run lint
```

## Architecture

### Solver Pipeline
1. **Input**: CityGraph with nodes (priority/normal) and traffic-weighted edges
2. **QUBO Builder** (`src/qubo_builder.py`): Encodes routing as Quadratic Unconstrained Binary Optimization
3. **Solvers**:
   - QAOA (`src/qaoa_solver.py`): Qiskit StatevectorSampler or MockSampler (set `QAOA_USE_MOCK=true`)
   - Greedy (`src/greedy_solver.py`): Nearest-neighbor baseline (priority-unaware, for comparison)
4. **Output**: Route sequence, distance, travel time, feasibility, priority satisfaction

### Key Constraint: Priority Ordering
Priority nodes (hospitals, emergency) MUST be visited before normal nodes. The QUBO enforces this via penalty term Bp (default 1000.0). The greedy solver intentionally ignores priorities to demonstrate quantum advantage.

### QUBO Encoding (TSP-style permutation)
- Variable: `x_{node_id}_{position}` = 1 if node is at position
- Penalties: A (one-hot) + B (uniqueness) + Bp (priority ordering) + C (distance objective)
- See `docs/qubo_math.md` for full formulation

### Backend Structure
- `app/main.py`: FastAPI routes and middleware
- `src/qaoa_solver.py`: QAOA with Qiskit, includes MockSampler for non-quantum testing
- `src/qubo_builder.py`: QUBO matrix construction with priority constraints
- `src/greedy_solver.py`: Priority-unaware baseline
- `src/data_models.py`: Pydantic schemas (Node, Edge, CityGraph, SolverRequest/Response)
- `src/config.py`: Environment-based settings

### Frontend Structure
- `components/InteractiveMap.tsx`: OSM map with Leaflet, click-to-add nodes, OSRM routing
- `components/SolverControls.tsx`: City generator and solver trigger
- `components/MetricsTable.tsx`: Quantum vs greedy comparison
- `lib/api.ts`: Typed API client with X-API-Key auth

## Configuration

### Backend Environment Variables
Key settings in `backend/.env`:
- `QAOA_USE_MOCK=true`: Use mock solver (no Qiskit required)
- `QAOA_REPS=2`: QAOA circuit layers
- `QUBO_PENALTY_A/B/BP/C`: Constraint penalty coefficients
- `API_KEY_HASH`: SHA-256 hash for authentication
- `SOLVER_TIMEOUT_SECONDS=30`: Max solver execution time

### Frontend Environment Variables
- `VITE_API_URL`: Backend API URL
- `VITE_API_KEY`: API key for X-API-Key header

## API Authentication
All endpoints except `/health` require `X-API-Key` header. Key is validated against SHA-256 hash in `API_KEY_HASH` env var.

## Testing Patterns
- API tests use `pytest-asyncio` and `httpx.AsyncClient`
- QUBO tests verify constraint satisfaction (feasibility, priority ordering)
- Security tests cover path traversal, auth bypasses, rate limiting
- Solver correctness tests verify both quantum and greedy produce valid routes

## MockSampler Behavior
When `QAOA_USE_MOCK=true`, `MockSampler` in `src/qaoa_solver.py` uses energy-aware greedy assignment over the QUBO matrix. It respects priority penalties baked into the QUBO, so it should produce priority-satisfying routes (unlike the baseline greedy solver which ignores priorities).
