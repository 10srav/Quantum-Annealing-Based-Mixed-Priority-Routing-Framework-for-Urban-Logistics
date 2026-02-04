# Quantum-Annealing Mixed-Priority Routing Framework

## What This Is

A quantum-classical hybrid optimization system for urban logistics routing problems. The system solves vehicle routing with mixed-priority nodes (priority nodes must be visited before normal nodes) using QAOA quantum solvers via Qiskit, with a classical greedy baseline for comparison. Includes a FastAPI backend and React/TypeScript frontend for visualization.

## Core Value

**Demonstrate quantum advantage in constrained routing optimization** — the system must produce valid, priority-respecting routes that outperform classical baselines on metrics (distance, time, constraint satisfaction).

## Requirements

### Validated

*Existing capabilities from codebase:*

- ✓ QAOA quantum solver with Qiskit integration — existing
- ✓ Greedy nearest-neighbor baseline solver — existing
- ✓ Priority-constrained routing (priority nodes before normal) — existing
- ✓ Traffic-aware edge weights — existing
- ✓ Random city graph generation — existing
- ✓ Route visualization with metrics display — existing
- ✓ Solver comparison (quantum vs greedy) — existing
- ✓ Interactive map with route display — existing

### Active

*Production hardening requirements:*

- [ ] Fix path traversal vulnerability in graph loading
- [ ] Sanitize error messages (no stack traces to clients)
- [ ] Add input validation with bounds checking
- [ ] Implement API key authentication
- [ ] Add request rate limiting
- [ ] Add request timeouts for solver calls
- [ ] Implement structured logging
- [ ] Add health check with dependency status
- [ ] Configure CORS for production domains
- [ ] Add comprehensive test coverage
- [ ] Dockerize for production deployment

### Out of Scope

- OAuth/JWT user accounts — API keys sufficient for team tool
- Database persistence — file-based storage acceptable for team scale
- Horizontal scaling — single-instance sufficient for 10-50 users
- Real D-Wave hardware integration — Qiskit QAOA simulator is the focus
- Mobile app — web interface only

## Context

**Current State:** Functional prototype with working solvers and UI. Has significant security vulnerabilities (path traversal, error exposure), missing input validation, no authentication, and limited test coverage. Not safe for production deployment.

**Target State:** Production-ready team tool with secure API, proper error handling, API key auth, and comprehensive tests. Deployable via Docker to any hosting platform.

**Technical Environment:**
- Backend: Python 3.11+, FastAPI, Qiskit, NetworkX
- Frontend: React 19, TypeScript, Vite, TailwindCSS
- Infrastructure: Docker Compose

**Known Issues from Codebase Audit:**
- Path traversal in `/graphs/{graph_name}` endpoint
- Generic exception handling exposes internals
- No upper bound validation on node count (DoS risk)
- Mock sampler correctness not tested
- QUBO constraint enforcement not tested

## Constraints

- **Security**: Must fix all identified vulnerabilities before deployment
- **Compatibility**: Must maintain existing API contract (frontend compatibility)
- **Scale**: ~25 node limit for QAOA solver (fundamental constraint)
- **Auth**: API key-based (no user management overhead)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| API keys over JWT | Team tool doesn't need user accounts; simpler to implement and manage | — Pending |
| File-based storage | Team scale doesn't justify database complexity | — Pending |
| Single-instance architecture | 10-50 users doesn't require horizontal scaling | — Pending |
| Qiskit QAOA focus | D-Wave hardware access not available; Qiskit provides good simulation | — Pending |

---
*Last updated: 2026-02-04 after initialization*
