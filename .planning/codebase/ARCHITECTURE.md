# Architecture

**Analysis Date:** 2026-02-04

## Pattern Overview

**Overall:** Full-stack quantum-classical hybrid architecture with clear separation between optimization backend and interactive frontend.

**Key Characteristics:**
- Backend-driven computation with quantum (QAOA) and classical (greedy) solving options
- RESTful API layer with FastAPI for request/response handling
- Stateless solver services that can be composed for comparison workflows
- QUBO-based problem formulation enabling quantum optimization
- React frontend with interactive map visualization and real-time route updates

## Layers

**API Layer:**
- Purpose: Accept routing requests, delegate to solvers, return results
- Location: `backend/app/main.py`
- Contains: FastAPI application, route definitions, CORS configuration
- Depends on: Data models, solver implementations, configuration
- Used by: Frontend React application via HTTP

**Solver Layer:**
- Purpose: Implement solving algorithms (quantum QAOA, greedy heuristic)
- Location: `backend/src/qaoa_solver.py`, `backend/src/greedy_solver.py`
- Contains: Algorithm implementations, solution decoding, feasibility checks
- Depends on: QUBO builder, data models, metrics computation
- Used by: API endpoints for route computation

**QUBO/Problem Formulation Layer:**
- Purpose: Convert routing constraints into binary quadratic model
- Location: `backend/src/qubo_builder.py`
- Contains: Constraint encoding, variable naming, penalty coefficient application
- Depends on: Data models, constraint specifications
- Used by: QAOA solver for quantum formulation

**Data Layer:**
- Purpose: Define domain models, validate data integrity
- Location: `backend/src/data_models.py`
- Contains: Pydantic models for nodes, edges, graphs, requests, responses
- Depends on: Pydantic validation framework
- Used by: All layers (API, solvers, builders)

**Simulation/Generation Layer:**
- Purpose: Generate synthetic city graphs for testing and experimentation
- Location: `backend/src/simulator.py`
- Contains: Random city generation, traffic assignment, node placement
- Depends on: Data models
- Used by: API generation endpoint, experiments

**Metrics/Analysis Layer:**
- Purpose: Compute route quality metrics and comparative analysis
- Location: `backend/src/metrics.py`, `backend/src/metrics_advanced.py`
- Contains: Route validation, distance/time computation, comparison calculations
- Depends on: Data models, solver responses
- Used by: Solvers, comparison endpoint

**Configuration Layer:**
- Purpose: Centralize environment and tuning settings
- Location: `backend/src/config.py`
- Contains: QAOA parameters, QUBO penalties, API settings, traffic multipliers
- Depends on: Pydantic settings, environment variables
- Used by: All backend layers

**Frontend State Management:**
- Purpose: React hooks managing solver state, graph state, async operations
- Location: `frontend/src/hooks/useSolver.ts`
- Contains: useCallback hooks for solve, compare, clear operations; state for results
- Depends on: API client library
- Used by: Top-level App component and nested components

**Frontend API Client:**
- Purpose: Encapsulate all HTTP communication with backend
- Location: `frontend/src/lib/api.ts`
- Contains: fetch wrappers, error handling, endpoint definitions
- Depends on: Configuration (API_BASE_URL, endpoints)
- Used by: React hooks for data fetching

**Frontend Components Layer:**
- Purpose: UI rendering and user interaction
- Location: `frontend/src/components/*.tsx`
- Contains: InteractiveMap, SolverControls, MetricsTable, RouteVisualizer, etc.
- Depends on: React hooks, data types
- Used by: App.tsx for composition

## Data Flow

**Solve Workflow (Single Solver):**

1. User selects solver type and parameters in SolverControls
2. SolverControls calls handleSolve in App.tsx with graph and solver choice
3. App calls useSolver.solve hook with graph, solver type, and optional QUBO params
4. Hook invokes api.solveRoute() which POST to `/solve` endpoint
5. Backend main.py receives SolverRequest, dispatches to qaoa_solver or greedy_solver
6. Solver reads graph structure, calls qubo_builder for constraint encoding
7. QAOA or greedy algorithm executes, returns SolverResponse with route and metrics
8. Response returns to frontend, hook updates state with quantumResult or greedyResult
9. App re-renders displaying selected route in InteractiveMap and metrics in MetricsTable

**Compare Workflow:**

1. User clicks compare button in SolverControls
2. App calls useSolver.compare hook with current graph
3. Hook invokes api.compareSolvers() which POST to `/compare` endpoint
4. Backend executes both quantum_solve and greedy_solve in parallel (conceptually)
5. metrics.compare_solutions computes relative performance metrics
6. ComparisonResponse returned with both solutions and reduction percentages
7. Frontend stores results in quantumResult, greedyResult, and comparison state
8. App displays both routes and side-by-side metrics

**Graph Generation Workflow:**

1. User specifies nodes, priority ratio, traffic profile in SolverControls
2. App calls useCityGraph.generate hook
3. Hook invokes api.generateCity() which POST to `/generate-city` endpoint
4. Backend simulator.generate_random_city() creates synthetic graph
5. Returns CityGraph with nodes, edges, traffic multipliers
6. Frontend updates graph state, clears previous results
7. InteractiveMap renders new city layout for user interaction

**State Management:**

- **Backend:** Stateless; all state in request payloads, no session tracking
- **Frontend:** Centralized in App.tsx component state (useEffect, useState)
  - graph state: current CityGraph being edited/solved
  - solverLoading: indicates async solver operation in progress
  - quantumResult, greedyResult: cached solution responses
  - comparison: cached comparison metrics
- **UI Reactivity:** useSolver and useCityGraph hooks maintain separate state; App orchestrates overall flow

## Key Abstractions

**CityGraph:**
- Purpose: Represents complete routing problem instance
- Examples: `backend/src/data_models.py` (lines 51-84), `frontend/src/lib/types.ts` (lines 32-42)
- Pattern: Pydantic BaseModel + TypeScript interface for type safety across stack

**SolverResponse:**
- Purpose: Standardized output from any solver algorithm
- Examples: `backend/src/data_models.py` (lines 102-112), `frontend/src/lib/types.ts` (lines 59-68)
- Pattern: Contains route, metrics (distance, time, feasibility, priority satisfaction), execution metadata

**QUBO Formulation:**
- Purpose: Encode routing problem as binary quadratic model for quantum solvers
- Examples: `backend/src/qubo_builder.py` (lines 20-130+)
- Pattern: Constraint penalties (one-hot per position, at-most-once per node, priority ordering) + objective function weighted by distance

**Sampler Interface:**
- Purpose: Abstract interface for sampling QUBO solutions (quantum or mock)
- Examples: `backend/src/qaoa_solver.py` (MockSampler class lines 31-63, QAOASampler class lines 66-130+)
- Pattern: Both implement sample(bqm) method returning SampleSet; allows swapping implementations

**API Request/Response Envelopes:**
- Purpose: Type-safe contract between frontend and backend
- Examples: `backend/src/data_models.py` SolverRequest/ComparisonResponse, `frontend/src/lib/api.ts` fetchApi generic
- Pattern: Pydantic validation on backend, TypeScript interfaces on frontend, JSON serialization bridge

## Entry Points

**Backend API Server:**
- Location: `backend/app/main.py` (lines 35-40, 162-164)
- Triggers: `uvicorn app.main:app` command or docker-compose
- Responsibilities: FastAPI initialization, middleware configuration, route definition, lifespan management

**Frontend React Application:**
- Location: `frontend/src/main.tsx`, `frontend/src/App.tsx` (lines 11-145)
- Triggers: Vite dev server (`npm run dev`) or production build
- Responsibilities: Initial data fetch (health check, city generation), App.tsx orchestration, component tree rendering

**API Health Endpoint:**
- Location: `backend/app/main.py` (lines 53-60)
- Triggers: GET /health from frontend or monitoring systems
- Responsibilities: Report service status, QAOA availability (Qiskit or mock mode), sampler configuration

## Error Handling

**Strategy:** Fail-fast with descriptive error messages; preserve partial results when possible.

**Patterns:**

- **Backend Validation:** Pydantic models reject invalid inputs before processing (e.g., missing required fields, constraint violations)
  - Example: `backend/src/data_models.py` Field(...) with validation rules

- **API Exception Handling:** FastAPI HTTPException wraps computation errors and returns status 500
  - Example: `backend/app/main.py` (lines 71-84, 92-102)

- **Frontend Error Capture:** React hooks catch errors in try/catch blocks, store error message in state
  - Example: `frontend/src/hooks/useSolver.ts` (lines 50-52, 72-74)

- **Graceful Degradation:** If Qiskit unavailable, QAOA solver falls back to MockSampler
  - Example: `backend/src/qaoa_solver.py` (lines 18-28, 31-63)

- **Route Feasibility:** Solvers compute feasibility flags (complete coverage, priority satisfaction) in response
  - Example: `backend/src/data_models.py` SolverResponse fields: feasible, priority_satisfied
  - Example: `backend/src/greedy_solver.py` (lines 118-128)

## Cross-Cutting Concerns

**Logging:**

- Backend: Print statements for startup/shutdown (FastAPI lifespan)
  - Location: `backend/app/main.py` (lines 29, 32)
- Frontend: Browser console via standard console.log (implicit in error handling)
- No centralized structured logging; suitable for development/prototyping phase

**Validation:**

- Backend: Pydantic BaseModel enforces type and constraint validation at API boundary
  - Example: `backend/src/data_models.py` Node, Edge, CityGraph classes with Field constraints
- Frontend: TypeScript type checking at compile-time prevents undefined fields
  - Example: `frontend/src/lib/types.ts` interfaces used throughout

**Authentication:**

- None implemented; backend is unsecured (development mode)
- D-Wave API token (DWAVE_API_TOKEN env var) is used for quantum sampler but not for API authentication
- CORS configured to allow localhost origins only
  - Location: `backend/app/main.py` (lines 42-50)

**Traffic Awareness:**

- Edge weights adjusted by traffic multipliers stored in CityGraph.traffic_multipliers
  - Example: `backend/src/data_models.py` get_edge_weight method (lines 73-84)
  - Example: `backend/src/greedy_solver.py` get_weighted_distance function (lines 48-61)
- QUBO builder uses base distances; traffic multipliers applied during metrics computation
  - Location: `backend/src/metrics.py` (implicit in route evaluation)

**Priority Constraint Enforcement:**

- Backend: QUBO builder encodes priority nodes must occupy first k positions
  - Location: `backend/src/qubo_builder.py` (Constraint 3 section)
- Frontend: MetricsTable displays priority_satisfied flag
  - Location: `frontend/src/components/MetricsTable.tsx` (implicit in result display)

---

*Architecture analysis: 2026-02-04*
