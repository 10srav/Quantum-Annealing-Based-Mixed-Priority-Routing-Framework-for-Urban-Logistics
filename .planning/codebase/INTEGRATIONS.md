# External Integrations

**Analysis Date:** 2026-02-04

## APIs & External Services

**Quantum Computing (Optional):**
- D-Wave Leap Quantum Annealer - Quantum optimization service for QUBO problems
  - SDK/Client: Not directly integrated in current codebase
  - Auth: `DWAVE_API_TOKEN` environment variable
  - Status: Referenced in README but not actively used in backend code

## Data Storage

**Databases:**
- Not detected - No persistent database configured

**File Storage:**
- Local filesystem only - Sample city graphs stored as JSON files in `data/` directory
  - Location: `C:\Users\polli\Downloads\Quantum-Annealing-Based Mixed-Priority Routing Framework for Urban Logistics\data\`
  - Format: JSON serialized `CityGraph` objects
  - Access pattern: Read-only endpoint `/graphs/{graph_name}` in `backend/app/main.py` loads graphs from disk

**Caching:**
- In-memory caching only via `functools.lru_cache` for settings singleton in `backend/src/config.py`
- No external caching service

## Authentication & Identity

**Auth Provider:**
- Custom/None - No user authentication system
- The application is designed for single-user or internal use
- CORS configuration allows specific origins (`localhost:5173`, `localhost:3000`) but no identity/auth layer

## Monitoring & Observability

**Error Tracking:**
- Not detected - No external error tracking integration

**Logs:**
- Console logging only - Print statements in `backend/app/main.py` lifespan handler
- No structured logging or log aggregation
- FastAPI's built-in request logging when running with uvicorn

## CI/CD & Deployment

**Hosting:**
- Docker-based containerization via `docker-compose.yml`
  - Backend: Python 3.11-slim container, port 8000
  - Frontend: Node 20-alpine container, port 5173
- No cloud platform integration detected (AWS, Azure, GCP, etc.)

**CI Pipeline:**
- Not detected - No CI configuration files (GitHub Actions, GitLab CI, Jenkins, etc.)

## Environment Configuration

**Required env vars:**
- `DWAVE_API_TOKEN` - Optional, only needed if using D-Wave Leap quantum annealer
- `VITE_API_URL` - Frontend environment variable pointing to backend (default: `http://localhost:8000`)

**Optional env vars:**
- `QAOA_REPS` - QAOA layer count
- `QAOA_USE_MOCK` - Use mock sampler instead of real QAOA
- `QAOA_SHOTS` - Quantum measurement shots
- `QUBO_PENALTY_A`, `QUBO_PENALTY_B`, `QUBO_PENALTY_BP`, `QUBO_PENALTY_C` - Penalty parameters
- `TRAFFIC_LOW`, `TRAFFIC_MEDIUM`, `TRAFFIC_HIGH` - Traffic multipliers
- `API_HOST` - Server host binding
- `API_PORT` - Server port
- `CORS_ORIGINS` - Allowed CORS origins

**Secrets location:**
- Backend `.env` file at `backend/.env` (gitignored, not committed)
- Example provided in `backend/.env.example`
- Frontend environment via `VITE_API_URL` in docker-compose.yml

## Webhooks & Callbacks

**Incoming:**
- Not detected - No webhook endpoints

**Outgoing:**
- Not detected - No outgoing webhooks to external services

## HTTP Communication

**Frontend to Backend:**
- Native Fetch API via `frontend/src/lib/api.ts`
  - Base URL: `VITE_API_URL` environment variable
  - Endpoints:
    - `POST /solve` - Run solver (quantum or greedy)
    - `POST /compare` - Compare both solvers
    - `POST /generate-city` - Generate random city graph
    - `GET /health` - Health check and QAOA availability status
    - `GET /graphs` - List available sample graphs
    - `GET /graphs/{graph_name}` - Load specific graph

**CORS:**
- Enabled in FastAPI via `CORSMiddleware` in `backend/app/main.py`
- Allowed origins configured via `CORS_ORIGINS` environment variable
- Default: `http://localhost:5173`, `http://localhost:3000`

## Quantum Computing Integration

**QAOA Solver:**
- Implementation: `backend/src/qaoa_solver.py` with two modes:
  1. Real QAOA via Qiskit + Aer simulator (uses local quantum simulator)
  2. Mock sampler for testing without quantum dependencies
- Conditional import pattern allows running without Qiskit installed
- Status check via `/health` endpoint returns `qiskit_available` flag

---

*Integration audit: 2026-02-04*
