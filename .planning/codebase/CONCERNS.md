# Codebase Concerns

**Analysis Date:** 2026-02-04

## Tech Debt

**Broad Exception Handling:**
- Issue: API endpoints catch generic `Exception` and expose raw error messages to clients via `detail=str(e)`
- Files: `backend/app/main.py` (lines 83-84, 101-102, 122-123)
- Impact: Exposes internal implementation details and stack traces to API consumers, potential security risk. Cannot distinguish between client errors (bad input), server errors (bugs), and external service failures
- Fix approach: Replace bare `except Exception` with specific exception types (`ValueError`, `KeyError`, `FileNotFoundError`). Log full exception internally, return sanitized messages to clients with appropriate HTTP status codes

**Unprotected File Path Access:**
- Issue: Graph file loading uses user-provided filename directly in path construction without validation
- Files: `backend/app/main.py` (lines 145-159)
- Impact: Potential path traversal vulnerability - user could request `/graphs/../../../etc/passwd` to read arbitrary files
- Fix approach: Validate `graph_name` against allowlist of valid graph files; use `pathlib.Path.resolve()` to verify path is within data directory

**Missing Input Validation on Parameters:**
- Issue: Generate-city endpoint accepts `n_nodes` without upper bound validation despite config having `max_nodes: 25`
- Files: `backend/app/main.py` (lines 105-123), `backend/src/config.py` (line 34)
- Impact: User can request 1000+ nodes, causing memory explosion and DoS
- Fix approach: Add Pydantic validators to `SolverRequest` and generation parameters that enforce max_nodes limit

**Inconsistent Error Handling Between Modules:**
- Issue: Solver modules handle errors differently - `qaoa_solver.py` falls back to mock sampler silently, but `greedy_solver.py` could return `None` from helper functions without validation
- Files: `backend/src/qaoa_solver.py` (lines 153-158), `backend/src/greedy_solver.py` (lines 63-77)
- Impact: Silent failures or unexpected None returns could propagate up without clear error messages
- Fix approach: Standardize error handling - either raise exceptions with clear messages or use Result types

**No Request Timeout Configuration:**
- Issue: API endpoints and async tasks have no timeout constraints
- Files: `backend/app/main.py`, `frontend/src/lib/api.ts`
- Impact: Slow quantum solver calls could hang indefinitely, blocking API resources. Browser requests have no abort mechanism
- Fix approach: Add request timeout middleware to FastAPI (`slowapi`), set `timeout` in fetch calls, add task cancellation tokens

## Known Bugs

**Priority Constraint Bug in Greedy Solver:**
- Symptoms: In some cases, the greedy solver may not correctly respect priority ordering when normal nodes have a `current` reference that's None
- Files: `backend/src/greedy_solver.py` (lines 96-99, 104-105)
- Trigger: When there are NO priority nodes (all normal), line 97 sets `current = normal_nodes[0]`, but line 102 starts with `unvisited_normal = normal_nodes[1:]` - missing first node in unvisited list after it's been used
- Workaround: Ensure at least one priority node by always generating at least one priority node (already done in `simulator.py` line 63-70)

**Infeasible Route Generation in Mock Sampler:**
- Symptoms: Mock QAOA sampler may return incomplete routes that don't visit all nodes
- Files: `backend/src/qaoa_solver.py` (lines 31-63, MockSampler.sample)
- Trigger: Greedy one-hot assignment may fail to assign all variables if constraint structure differs from expected
- Workaround: Falls back gracefully - `decode_route` filters out None values, route validation catches infeasibility
- Impact: When `feasible=False`, metrics show `total_distance=inf` and `travel_time=inf` but client still gets response

**Unused Parameter in quantum_solve:**
- Symptoms: `params` parameter passed to `quantum_solve` but sometimes ignored
- Files: `backend/app/main.py` (line 73), `backend/src/qaoa_solver.py` (line 148)
- Trigger: When `params=None`, defaults are used, but caller doesn't always pass params (compare endpoint line 93-95)
- Impact: QUBO penalty tuning is hard - /solve endpoint accepts params but /compare endpoint always uses defaults
- Fix approach: Make params required or ensure consistent defaults, document which endpoints support tuning

## Security Considerations

**Exposed Error Details in API:**
- Risk: `HTTPException(detail=str(e))` exposes Python exceptions, library names, file paths to API clients
- Files: `backend/app/main.py` (lines 84, 102, 123)
- Current mitigation: CORS is configured to allow localhost only
- Recommendations: (1) Log full exception with traceback server-side, (2) Return generic message to client ("Internal server error"), (3) Implement structured logging with request IDs for troubleshooting

**Path Traversal in Graph Loading:**
- Risk: `/graphs/{graph_name}` accepts arbitrary strings, could read files outside data directory
- Files: `backend/app/main.py` (lines 145-159)
- Current mitigation: Only `.json` files in `data/` directory exist, but no explicit validation
- Recommendations: (1) Maintain allowlist of valid graph names, (2) Use `pathlib.resolve()` with comparison against base directory, (3) Add tests for malicious paths like `../../../etc/passwd`

**Environment Variable Exposure in Health Endpoint:**
- Risk: Health endpoint may expose sensitive config via `get_sampler_info()`
- Files: `backend/app/main.py` (line 59), `backend/src/qaoa_solver.py` (lines 194-212)
- Current mitigation: Only exposes version numbers and availability flags
- Recommendations: Never expose `DWAVE_API_TOKEN`, CORS settings, or penalty parameters to unauthenticated endpoints

**Missing CORS for Production:**
- Risk: Current CORS allows `http://localhost:5173` and `http://localhost:3000` - won't work in production
- Files: `backend/src/config.py` (line 31), `backend/app/main.py` (lines 42-50)
- Current mitigation: Config is environment-aware via Pydantic settings
- Recommendations: (1) Make CORS origins environment-specific via env var, (2) Whitelist only exact domains, never `*`, (3) Add tests for CORS headers

## Performance Bottlenecks

**Quadratic QUBO Variable Growth:**
- Problem: QUBO solver scales with O(n²) variables (n nodes × n positions), becomes intractable above ~25 nodes
- Files: `backend/src/qubo_builder.py` (lines 49-56)
- Cause: Standard TSP-QUBO formulation using assignment matrix `x_{i,p}`
- Impact: At n=25 nodes, 625 variables; at n=50 nodes, 2500 variables - beyond practical quantum annealer capacity
- Improvement path: (1) For larger problems, use hierarchical/chunking approach, (2) Implement subtour elimination constraints more efficiently, (3) Consider state-space reduction by clustering nearby nodes

**Full Graph Connectivity Check:**
- Problem: `_ensure_connectivity()` uses O(n²) union-find operations to check connectivity
- Files: `backend/src/simulator.py` (lines 129-181)
- Cause: Iterates all node pairs to add edges until connected
- Impact: Negligible for test graphs (~10-20 nodes) but adds unnecessary overhead
- Improvement path: Use BFS/DFS instead of union-find for connectivity verification

**Repeated Distance Computations:**
- Problem: Distance between nodes computed multiple times across encoding stages
- Files: `backend/src/qubo_builder.py` (lines 127-138), `backend/src/greedy_solver.py` (lines 48-61), `backend/src/simulator.py` (lines 76-82)
- Cause: No edge weight caching; each distance lookup iterates edge list
- Impact: Small graphs (<20 nodes) unaffected; larger graphs see 2-3x overhead
- Improvement path: Pre-compute adjacency matrix or distance cache in CityGraph initialization

**Synchronous Route Metric Computation:**
- Problem: Route validation and metric computation happens synchronously in solver, blocking response
- Files: `backend/src/qaoa_solver.py` (lines 166-180), `backend/src/greedy_solver.py` (lines 116-139)
- Cause: No async/parallel computation for feasibility checking and distance calculation
- Impact: 10+ node problems take ~100ms+ to compute metrics
- Improvement path: Pre-compute all edge lengths on graph initialization, use NumPy vectorization for metrics

**Frontend API Error Handling Overhead:**
- Problem: API error responses are text, not parsed, and converted to generic "Unknown error" messages
- Files: `frontend/src/lib/api.ts` (lines 36-42), `frontend/src/hooks/useSolver.ts` (lines 51-54)
- Cause: `response.text()` is awaited even when parsing JSON would fail
- Impact: Error messages are uninformative to users
- Improvement path: (1) Return structured JSON errors from API, (2) Parse JSON errors before text fallback, (3) Distinguish 4xx vs 5xx in UI

## Fragile Areas

**QUBO Constraint Tuning:**
- Files: `backend/src/qubo_builder.py` (lines 58-122), `backend/src/config.py` (lines 17-21)
- Why fragile: Penalty coefficients (A=100, B=500, Bp=1000, C=1) are magic numbers with no principled selection. Small changes dramatically affect solution quality. No validation that penalties don't conflict
- Safe modification: (1) Document why each penalty value was chosen, (2) Add constraint solver to find non-conflicting penalties, (3) Run experiments.py ablation study before changing, (4) Add assertions that A < Bp (missing priority more important than wrong priority)
- Test coverage: `test_qubo.py` only checks variable count and naming, not penalty correctness

**Mock Sampler Correctness:**
- Files: `backend/src/qaoa_solver.py` (lines 31-63)
- Why fragile: Greedy one-hot assignment assumes specific QUBO structure - if constraint weights change, mock may diverge from real QAOA behavior
- Safe modification: (1) Verify mock output matches real QAOA on test cases, (2) Add comments explaining assumptions about variable naming and constraint order, (3) Consider using a proper QUBO solver library instead of custom greedy logic
- Test coverage: No tests verify mock sampler produces reasonable solutions

**Graph File Loading:**
- Files: `backend/app/main.py` (lines 145-159)
- Why fragile: `json.load()` will throw if file is malformed, caught too broadly. File path construction vulnerable to traversal
- Safe modification: (1) Use explicit path validation, (2) Pre-load all graphs at startup and cache them, (3) Add JSON schema validation with pydantic after loading
- Test coverage: No tests for malformed JSON or missing files

**Route Decoding Logic:**
- Files: `backend/src/qubo_builder.py` (lines 142-166)
- Why fragile: String splitting `node_id = "_".join(parts[1:-1])` assumes node IDs never contain underscores. If node ID is "zone_1", parsing breaks
- Safe modification: (1) Use explicit variable naming scheme that doesn't depend on string splitting, (2) Store metadata in a separate dict: `variables = {position: [(var_name, node_id), ...]}`, (3) Add tests with node IDs containing underscores
- Test coverage: `test_qubo.py` only tests default node names (N1, N2)

**Frontend Type Safety:**
- Files: `frontend/src/hooks/useSolver.ts` (lines 41, 61)
- Why fragile: Hook returns bare state object spread with `...state`, making it easy to accidentally access undefined fields. Error handling assumes Error type
- Safe modification: (1) Use TypeScript `as const` for hook return types, (2) Explicitly list returned properties, (3) Handle err more safely: `err instanceof Error ? err.message : String(err)`
- Test coverage: Frontend has no test files

## Scaling Limits

**QUBO Size Limit:**
- Current capacity: ~25 nodes (625 variables) practical; 50+ nodes (2500+ variables) unlikely to find good solutions
- Limit: D-Wave quantum annealer has ~5000+ qubits but embedding overhead and QUBO quality degrades
- Scaling path: (1) Implement problem decomposition (partition graph into sub-problems), (2) Use hybrid approach with greedy pre-processing, (3) Implement quantum-enhanced local search instead of full QUBO encoding

**Memory Usage in Graph Generation:**
- Current capacity: Can generate ~100-node graphs, but all edges stored in memory
- Limit: O(n²) edges for complete graphs; storing full CityGraph in memory becomes expensive
- Scaling path: (1) Use lazy edge loading, (2) Implement streaming experiment runner, (3) Store graphs to disk for large experiments

**API Concurrency:**
- Current capacity: Single FastAPI worker, no async/await optimization in solvers
- Limit: One request blocks the worker; multiple concurrent requests queue
- Scaling path: (1) Add async wrapper for solver calls, (2) Implement request queuing with FastAPI BackgroundTasks, (3) Add Celery task queue for long-running solves

## Dependencies at Risk

**Qiskit Version Pinning:**
- Risk: `requirements.txt` pins `qiskit>=1.0.0` but does not pin specific versions; Qiskit 1.x has breaking API changes between minor versions
- Impact: Environment could fail to install if Qiskit 1.5 changes import paths or API
- Migration plan: (1) Pin exact versions: `qiskit==1.0.2`, (2) Set up CI to test against multiple Qiskit versions, (3) Monitor Qiskit changelog for deprecations

**D-Wave SDK Optional Dependency:**
- Risk: Code imports D-Wave conditionally but actual leapHybridSampler usage not in codebase (uses Qiskit instead)
- Impact: Confusion about which quantum backend is used; README mentions D-Wave but implementation uses Qiskit
- Migration plan: Either (1) remove D-Wave references and use pure Qiskit, or (2) implement D-Wave backend option for comparison

**No Pinned Python Version:**
- Risk: `requirements.txt` doesn't specify Python version; README says "Python 3.11+" but uses match statements (3.10+) and | union syntax (3.10+)
- Impact: Code might run on Python 3.9 with some deps but fail mysteriously
- Migration plan: (1) Add `python_requires=">=3.10"` to any setup.py, (2) Pin in docker images and CI configs, (3) Test against 3.10 and 3.11

## Missing Critical Features

**No Input Sanitization:**
- Problem: CORS allows any origin in theory if configured differently; no rate limiting, CSRF tokens, or auth
- Blocks: Cannot safely deploy to production; vulnerable to brute force and abuse
- Recommended implementation: (1) Add `python-jose` for JWT auth, (2) Implement `slowapi` rate limiting per IP/key, (3) Add CSRF tokens if using cookies

**No Monitoring or Observability:**
- Problem: No logging, no metrics, no request tracking
- Blocks: Cannot debug production issues or understand solver performance
- Recommended implementation: (1) Add `structlog` for structured logging, (2) Export Prometheus metrics from `prometheus-client`, (3) Add X-Request-ID for tracing

**No Persistent Storage:**
- Problem: Experiment results written to CSV files, no database
- Blocks: Cannot query historical results, no audit trail
- Recommended implementation: (1) Add SQLite for local storage or PostgreSQL for scale, (2) Implement ORM with SQLAlchemy, (3) Add REST endpoints to query historical runs

**No Caching:**
- Problem: Identical graph/solver combinations recomputed each time
- Blocks: Cannot efficiently compare solver iterations
- Recommended implementation: (1) Use Redis for result caching, (2) Implement cache key from graph hash + params, (3) Add cache invalidation on parameter changes

## Test Coverage Gaps

**QUBO Constraint Enforcement Not Tested:**
- What's not tested: Whether penalties actually force one-hot constraints, priority ordering constraints
- Files: `backend/tests/test_qubo.py` (only checks variable count, not constraint correctness)
- Risk: QUBO could have weak penalties that solver ignores
- Priority: High - QUBO correctness is core to quantum advantage

**Mock Sampler Solution Quality Not Tested:**
- What's not tested: Whether mock sampler returns valid/reasonable solutions
- Files: No tests for `MockSampler.sample()` behavior
- Risk: Mock mode could hide bugs in QAOA integration
- Priority: High - used in all development/CI

**API Input Validation Not Tested:**
- What's not tested: Malformed JSON, missing fields, invalid parameter ranges
- Files: `backend/tests/test_api.py` only tests happy path
- Risk: API could crash on edge case inputs instead of returning 400
- Priority: Medium - affects reliability

**Frontend Component Tests Missing:**
- What's not tested: React components, hooks, error states
- Files: No test files in `frontend/`
- Risk: UI bugs go unnoticed, error messages untested
- Priority: Medium - affects user experience

**End-to-End Tests Missing:**
- What's not tested: Full workflow from frontend request to result
- Files: No e2e test files
- Risk: Integration bugs between frontend and backend undetected
- Priority: Low - functional testing covers main paths

---

*Concerns audit: 2026-02-04*
