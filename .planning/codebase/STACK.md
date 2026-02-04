# Technology Stack

**Analysis Date:** 2026-02-04

## Languages

**Primary:**
- Python 3.11+ - Backend server and quantum/classical solvers
- TypeScript 5.9 - Frontend application and React components
- JavaScript/JSX - React 19 components and utilities

**Secondary:**
- HTML/CSS - UI markup and styling (TailwindCSS)

## Runtime

**Environment:**
- Python 3.11 (backend)
- Node.js 20 LTS (frontend)
- Docker containers (development and deployment)

**Package Manager:**
- pip (Python package manager)
- npm (Node.js package manager)
- Lockfile: `package-lock.json` (present), `requirements.txt` (present)

## Frameworks

**Core Backend:**
- FastAPI 0.109+ - REST API framework for routing and solver endpoints
- Uvicorn 0.27+ - ASGI server for FastAPI application

**Core Frontend:**
- React 19.2 - UI library and component framework
- Vite 7.2 - Build tool and development server
- TypeScript - Type-safe JavaScript development

**Quantum Computing:**
- Qiskit 1.0+ - Quantum computing framework (QAOA implementation)
- Qiskit-Aer 0.13+ - Quantum simulator for local execution
- Qiskit-Optimization 0.6+ - Optimization problem handling
- Qiskit-Algorithms 0.3+ - QAOA algorithm implementation

**Graph & Math:**
- NetworkX 3.2+ - Graph data structures and operations
- NumPy 1.26+ - Numerical computing and linear algebra
- Dimod 0.12+ - Binary quadratic model (QUBO) handling

**Frontend UI Components:**
- Leaflet 1.9+ - Interactive maps and geospatial visualization
- React-Leaflet 5.0+ - React bindings for Leaflet maps

**Testing:**
- Pytest 7.4+ - Python test framework
- Pytest-asyncio 0.23+ - Async test support for FastAPI
- httpx 0.26+ - Async HTTP client for API testing

**Configuration & Validation:**
- Pydantic 2.5+ - Data validation and settings management
- Pydantic-Settings 2.1+ - Environment variable configuration
- Python-dotenv 1.0+ - .env file loading

**Data Processing:**
- Pandas 2.1+ - Data analysis and manipulation

## Key Dependencies

**Critical:**
- FastAPI - Core backend framework for routing and API endpoints
- Qiskit & Qiskit-Aer - Quantum computing and QAOA algorithm implementation
- React - Frontend UI framework
- Vite - Development and build tool with HMR support

**Infrastructure:**
- Dimod - QUBO formulation and sampling
- NetworkX - Graph-based routing problem representation
- NumPy - Mathematical computations for routing metrics

**Development:**
- ESLint 9.39 - JavaScript/TypeScript linting
- TypeScript ESLint - TypeScript-specific linting rules
- Vite plugins - React and TypeScript support

## Configuration

**Environment:**
- `.env` file at `backend/.env` (loaded via Pydantic-Settings)
- Environment variables:
  - `QAOA_REPS` - Number of QAOA circuit layers (default: 2)
  - `QAOA_USE_MOCK` - Use mock sampler instead of real QAOA (default: false)
  - `QAOA_SHOTS` - Measurement shots for quantum sampling (default: 1024)
  - `QUBO_PENALTY_A` - One-hot constraint penalty (default: 100.0)
  - `QUBO_PENALTY_B` - Priority ordering penalty (default: 500.0)
  - `QUBO_PENALTY_BP` - Missing priority penalty (default: 1000.0)
  - `QUBO_PENALTY_C` - Objective function weight (default: 1.0)
  - `TRAFFIC_LOW`, `TRAFFIC_MEDIUM`, `TRAFFIC_HIGH` - Traffic multipliers
  - `API_HOST` - API server host (default: 0.0.0.0)
  - `API_PORT` - API server port (default: 8000)
  - `CORS_ORIGINS` - Allowed CORS origins (default: localhost:5173, localhost:3000)
  - `DWAVE_API_TOKEN` - D-Wave Leap quantum annealer API token (optional)

**Build Configuration:**
- `frontend/tsconfig.json` - TypeScript configuration (includes app and node configs)
- `frontend/vite.config.ts` - Vite build configuration
- `frontend/package.json` - Scripts: `dev`, `build`, `lint`, `preview`
- Backend uses implicit configuration via `src/config.py` with `Settings` class

## Platform Requirements

**Development:**
- Python 3.11+ with pip
- Node.js 20+ with npm
- Vite development server (hot module reload)
- FastAPI with uvicorn

**Production:**
- Docker 20.10+
- Docker Compose 2.0+
- Deployment target: Containerized (services: backend FastAPI on 8000, frontend Vite on 5173)

---

*Stack analysis: 2026-02-04*
