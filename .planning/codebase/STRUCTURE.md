# Codebase Structure

**Analysis Date:** 2026-02-04

## Directory Layout

```
Quantum-Annealing-Based Mixed-Priority Routing Framework for Urban Logistics/
├── backend/                    # Python FastAPI server for solving
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py            # FastAPI application, route endpoints
│   ├── src/
│   │   ├── __init__.py
│   │   ├── config.py          # Settings, environment configuration
│   │   ├── data_models.py     # Pydantic models (Node, Edge, CityGraph, etc.)
│   │   ├── qubo_builder.py    # QUBO constraint encoding
│   │   ├── qaoa_solver.py     # QAOA quantum solver + MockSampler
│   │   ├── greedy_solver.py   # Greedy nearest-neighbor solver
│   │   ├── metrics.py         # Route quality metrics
│   │   ├── metrics_advanced.py # Advanced performance analysis
│   │   └── simulator.py       # Random city graph generation
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── test_qubo.py       # QUBO builder unit tests
│   │   ├── test_greedy.py     # Greedy solver unit tests
│   │   └── test_api.py        # API endpoint tests
│   ├── .env                   # Environment variables (development)
│   ├── .env.example           # Environment template
│   ├── requirements.txt       # Python package dependencies
│   ├── Dockerfile            # Docker image definition
│   ├── ablations.py          # Ablation study scripts
│   ├── experiments.py        # Experiment runner with metrics collection
│   └── tuning.py             # Parameter tuning utilities
├── frontend/                   # React/TypeScript web UI
│   ├── src/
│   │   ├── components/
│   │   │   ├── InteractiveMap.tsx    # OSM map for adding/editing nodes
│   │   │   ├── MapView.tsx           # Basic map component
│   │   │   ├── OSMMapView.tsx        # OpenStreetMap integration
│   │   │   ├── SolverControls.tsx    # Button controls for solving/generation
│   │   │   ├── MetricsTable.tsx      # Results metrics display
│   │   │   ├── RouteVisualizer.tsx   # Route sequence text display
│   │   │   ├── MetricsChart.tsx      # Comparison charts
│   │   │   ├── ResultsHistory.tsx    # Historical results tracking
│   │   │   └── index.ts              # Component barrel export
│   │   ├── hooks/
│   │   │   └── useSolver.ts          # React hooks: useSolver, useCityGraph, useHealth
│   │   ├── lib/
│   │   │   ├── api.ts               # API client, endpoint definitions
│   │   │   ├── config.ts            # Frontend configuration (API_BASE_URL)
│   │   │   └── types.ts             # TypeScript interfaces matching backend
│   │   ├── App.tsx                  # Root component, orchestration
│   │   ├── App.css                  # Styling
│   │   └── main.tsx                 # React DOM mount
│   ├── public/                 # Static assets (images, icons)
│   ├── package.json            # npm dependencies
│   ├── package-lock.json       # npm lock file
│   ├── tsconfig.json           # TypeScript root config
│   ├── tsconfig.app.json       # TypeScript app config
│   ├── tsconfig.node.json      # TypeScript node config
│   ├── vite.config.ts          # Vite bundler configuration
│   ├── eslint.config.js        # ESLint rules
│   ├── index.html              # HTML entry point
│   ├── Dockerfile              # Docker image for frontend
│   └── README.md               # Frontend-specific documentation
├── data/                       # Sample city graphs (JSON)
│   └── *.json                  # Pre-defined test graphs
├── docs/                       # Documentation
│   └── (technical docs, papers, references)
├── .git/                       # Git repository metadata
├── .claude/                    # Claude-specific context (ignored)
├── .planning/                  # Planning artifacts directory
│   └── codebase/              # Codebase analysis documents
│       ├── ARCHITECTURE.md    # Architecture analysis
│       └── STRUCTURE.md       # This file
├── docker-compose.yml         # Docker Compose orchestration
├── README.md                  # Top-level project README
└── Quantum Mixed Priority Routing.docx  # Project documentation

```

## Directory Purposes

**backend/app/:**
- Purpose: FastAPI application entry point and route definitions
- Contains: Python ASGI application initialization, endpoint handlers
- Key files: `backend/app/main.py` defines all REST endpoints (/solve, /compare, /generate-city, /health, /graphs)

**backend/src/:**
- Purpose: Core solving logic and domain models
- Contains: Solver algorithms, problem formulation, data validation, metrics computation
- Key files:
  - `data_models.py`: Pydantic validation for all domain objects
  - `qubo_builder.py`: Constraint encoding for quantum optimization
  - `qaoa_solver.py`: Qiskit QAOA implementation with mock fallback
  - `greedy_solver.py`: Nearest-neighbor heuristic solver
  - `simulator.py`: Synthetic graph generation for testing

**backend/tests/:**
- Purpose: Unit and integration tests
- Contains: Test suites for QUBO builder, solvers, and API endpoints
- Key files:
  - `test_qubo.py`: QUBO constraint encoding validation
  - `test_greedy.py`: Greedy solver correctness
  - `test_api.py`: API endpoint behavior

**frontend/src/components/:**
- Purpose: React UI components
- Contains: Reusable and page-level components for map, controls, results display
- Key files:
  - `InteractiveMap.tsx`: Main map visualization with click-to-add nodes, route highlighting
  - `SolverControls.tsx`: Form and buttons for solver selection, graph generation
  - `MetricsTable.tsx`: Results summary (distance, time, feasibility)
  - `RouteVisualizer.tsx`: Text list of route sequence

**frontend/src/hooks/:**
- Purpose: React state management logic
- Contains: Custom hooks encapsulating async operations and state updates
- Key files:
  - `useSolver.ts`: useSolver, useCityGraph, useHealth hooks for data fetching

**frontend/src/lib/:**
- Purpose: Utilities, configuration, and shared types
- Contains: API client, TypeScript types, configuration constants
- Key files:
  - `api.ts`: HTTP client with error handling
  - `types.ts`: TypeScript interfaces matching Pydantic models
  - `config.ts`: Environment-specific settings (API_BASE_URL, endpoints)

**data/:**
- Purpose: Sample city graphs for experiments and demo
- Contains: JSON files with pre-configured node/edge layouts
- Generated by: Experiments or manually created for reproducibility

**docs/:**
- Purpose: Project documentation
- Contains: Technical documentation, research papers, design notes

## Key File Locations

**Entry Points:**

- `backend/app/main.py`: FastAPI application entry; defines all POST/GET endpoints
- `frontend/src/main.tsx`: React DOM mount point; loads root App component
- `frontend/src/App.tsx`: Root React component; orchestrates page layout and state

**Configuration:**

- `backend/src/config.py`: Environment settings (QAOA params, QUBO penalties, API host/port, CORS origins)
- `backend/.env`: Development environment variables (DWAVE_API_TOKEN, custom QUBO penalties)
- `frontend/src/lib/config.ts`: API base URL and endpoint paths
- `frontend/vite.config.ts`: Vite bundler configuration

**Core Logic:**

- `backend/src/data_models.py`: Domain model definitions (Node, Edge, CityGraph, SolverRequest/Response)
- `backend/src/qubo_builder.py`: Binary quadratic model construction with constraints
- `backend/src/qaoa_solver.py`: Quantum solver using Qiskit QAOA (or mock mode)
- `backend/src/greedy_solver.py`: Classical greedy solver with traffic awareness
- `backend/src/metrics.py`: Route quality computation (distance, time, feasibility checks)

**Testing:**

- `backend/tests/test_qubo.py`: QUBO formulation unit tests
- `backend/tests/test_greedy.py`: Greedy algorithm unit tests
- `backend/tests/test_api.py`: API endpoint integration tests

## Naming Conventions

**Files:**

- Python modules: `snake_case.py` (e.g., `data_models.py`, `qubo_builder.py`)
- React components: `PascalCase.tsx` for component files (e.g., `InteractiveMap.tsx`, `SolverControls.tsx`)
- Hooks: `camelCase.ts` (e.g., `useSolver.ts`)
- Utilities: `camelCase.ts` for lib modules (e.g., `api.ts`, `types.ts`, `config.ts`)

**Directories:**

- Plural for collections: `components/`, `hooks/`, `src/`, `tests/`, `app/`
- Domain-specific names: `backend/`, `frontend/`, `data/`, `docs/`

**Code Naming (Python):**

- Classes: `PascalCase` (e.g., `CityGraph`, `SolverResponse`, `QAOASampler`, `MockSampler`)
- Functions: `snake_case` (e.g., `build_qubo`, `greedy_solve`, `quantum_solve`, `generate_random_city`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `QISKIT_AVAILABLE`)
- Private methods: Leading underscore (e.g., `_get_icon_url`)

**Code Naming (TypeScript/React):**

- Components: `PascalCase` (e.g., `InteractiveMap`, `SolverControls`, `MetricsTable`)
- Functions: `camelCase` (e.g., `solveRoute`, `compareSolvers`, `generateCity`)
- Hooks: `camelCase` with `use` prefix (e.g., `useSolver`, `useCityGraph`, `useHealth`)
- Types: `PascalCase` (e.g., `CityGraph`, `SolverResponse`, `SolverType`)
- Interfaces: `PascalCase` with optional `I` prefix (convention not strictly followed, but consistent with types)

## Where to Add New Code

**New Feature (e.g., new solver algorithm):**

- Algorithm implementation: `backend/src/new_solver.py`
  - Pattern: Function accepting `graph: CityGraph` → returns `SolverResponse`
  - Match: Metrics computation style in `backend/src/greedy_solver.py`
  - Integration: Add endpoint in `backend/app/main.py` or extend `/solve` dispatcher
- Tests: `backend/tests/test_new_solver.py`
  - Pattern: Use pytest with sample graphs from `data/`
  - Match: Test structure in `test_greedy.py`

**New React Component:**

- Component file: `frontend/src/components/ComponentName.tsx`
  - Pattern: Export as named function component with TypeScript props interface
  - Match: Props structure matching existing components (InteractiveMap, SolverControls)
  - Types: Use interfaces from `frontend/src/lib/types.ts`
- Import in: `frontend/src/components/index.ts` for barrel export
- Use in: Add to `frontend/src/App.tsx` or nest within parent component
- Styling: Inline CSS or external `ComponentName.css` per component

**New API Endpoint:**

- Handler function: Add to `backend/app/main.py`
  - Pattern: Async function decorated with `@app.post()` or `@app.get()`
  - Input: Pydantic model from `backend/src/data_models.py`
  - Output: Pydantic response model
  - Match: Error handling style in existing endpoints (lines 71-84)
- Types: Define request/response models in `backend/src/data_models.py`
- Frontend: Add HTTP function to `frontend/src/lib/api.ts` using `fetchApi` generic wrapper

**Utility/Helper Functions:**

- Backend helpers: `backend/src/utilities.py` or add to existing module if domain-specific
- Frontend helpers: `frontend/src/lib/utils.ts` for shared utilities, or co-locate in component if specific

**Configuration Changes:**

- Backend: Add field to `Settings` class in `backend/src/config.py`, set in `.env`
- Frontend: Add constant to `frontend/src/lib/config.ts`, export and use in components

## Special Directories

**data/:**
- Purpose: Sample city graphs stored as JSON files
- Generated: Yes (by simulator.py or manually)
- Committed: Yes (example graphs in version control)
- Usage: Loaded by `/graphs` and `/graphs/{graph_name}` endpoints for demo datasets

**.env (backend):**
- Purpose: Development environment variables
- Generated: No (copied from .env.example)
- Committed: No (listed in .gitignore for security)
- Contains: DWAVE_API_TOKEN, custom QUBO parameters, API configuration

**node_modules/ (frontend):**
- Purpose: npm package dependencies
- Generated: Yes (by `npm install`)
- Committed: No (listed in .gitignore)
- Size: ~500MB; omitted from version control

**.pytest_cache/ (backend):**
- Purpose: Pytest cache for test discovery optimization
- Generated: Yes (by pytest)
- Committed: No (listed in .gitignore)

**.planning/codebase/:**
- Purpose: GSD (Guided Specification Documents) codebase analysis
- Generated: Yes (by GSD mapping tools)
- Committed: Yes (part of planning system)
- Contains: ARCHITECTURE.md, STRUCTURE.md, CONVENTIONS.md, TESTING.md, CONCERNS.md

---

*Structure analysis: 2026-02-04*
