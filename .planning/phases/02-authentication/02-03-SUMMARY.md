---
phase: 02-authentication
plan: 03
subsystem: api
tags: [asyncio, timeout, fastapi, http-504]

# Dependency graph
requires:
  - phase: 02-01
    provides: API key authentication for protected endpoints
provides:
  - Configurable solver timeout (SOLVER_TIMEOUT_SECONDS)
  - 504 Gateway Timeout for slow solver requests
  - Async timeout wrapper for sync solver functions
affects: [03-solver-improvements, 04-testing]

# Tech tracking
tech-stack:
  added: []
  patterns: [asyncio.wait_for for sync-to-async timeout wrapping]

key-files:
  created: []
  modified:
    - backend/src/config.py
    - backend/app/main.py
    - backend/.env.example

key-decisions:
  - "30-second default timeout for solver endpoints"
  - "Individual timeout per solver call in /compare (worst case 60s total)"
  - "Only solver endpoints affected, non-solver endpoints remain unaffected"

patterns-established:
  - "run_solver_with_timeout: async wrapper for sync functions with configurable timeout"
  - "504 Gateway Timeout for compute-intensive operations that exceed time limit"

# Metrics
duration: 4min
completed: 2026-02-04
---

# Phase 2 Plan 3: Request Timeout Handling Summary

**Configurable timeout wrapper for solver endpoints using asyncio.wait_for, returning 504 Gateway Timeout with clear error message**

## Performance

- **Duration:** 4 min
- **Started:** 2026-02-04T19:13:58Z
- **Completed:** 2026-02-04T19:17:30Z
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Added configurable `solver_timeout_seconds` setting with 30-second default
- Implemented `run_solver_with_timeout` async wrapper using asyncio.wait_for
- Wrapped `/solve` and `/compare` endpoints with timeout protection
- Clear 504 error message includes timeout duration

## Task Commits

Each task was committed atomically:

1. **Task 1: Add timeout configuration** - `353d223` (feat)
2. **Task 2: Implement timeout wrapper for solver endpoints** - `88e63f4` (feat)
3. **Task 3: Test timeout behavior** - No commit (verification only)

## Files Created/Modified
- `backend/src/config.py` - Added solver_timeout_seconds setting
- `backend/app/main.py` - Added run_solver_with_timeout wrapper, updated /solve and /compare endpoints
- `backend/.env.example` - Documented SOLVER_TIMEOUT_SECONDS environment variable

## Decisions Made
- **30-second default timeout:** Reasonable for QAOA solver on small graphs (up to 25 nodes)
- **Individual solver timeouts:** Each solver call in /compare has its own timeout (worst case 60s for both)
- **Targeted timeout:** Only solver endpoints affected, keeping /generate-city, /graphs fast and unaffected

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None - plan 02-02 (rate limiting) ran in parallel and added rate limiter decorators to endpoints, which integrated cleanly with timeout implementation.

## User Setup Required

None - timeout is configurable via environment variable but works with sensible default.

Optional configuration in `.env`:
```
SOLVER_TIMEOUT_SECONDS=30  # Increase for larger graphs or production
```

## Next Phase Readiness
- AUTH-04 satisfied: Solver requests exceeding timeout return 504 Gateway Timeout
- Ready for testing phase to add timeout behavior tests
- Timeout value tunable for production workloads

---
*Phase: 02-authentication*
*Completed: 2026-02-04*
