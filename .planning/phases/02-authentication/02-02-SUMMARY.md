---
phase: 02-authentication
plan: 02
subsystem: api-security
tags: [rate-limiting, slowapi, security, api-protection]
dependency-graph:
  requires: [02-01]
  provides: [AUTH-03]
  affects: [03-testing]
tech-stack:
  added: [slowapi]
  patterns: [api-key-based-rate-limiting, retry-after-header]
key-files:
  created:
    - backend/src/rate_limit.py
  modified:
    - backend/requirements.txt
    - backend/src/config.py
    - backend/app/main.py
decisions:
  - "API-key-based rate limiting (not IP-based) for team tool fairness"
  - "Custom exception handler for Retry-After header (slowapi default incompatible with FastAPI response models)"
  - "Separate limits for solver vs standard endpoints (compute protection)"
metrics:
  duration: ~8 min
  completed: 2026-02-05
---

# Phase 02 Plan 02: Rate Limiting Summary

**One-liner:** slowapi rate limiting with API-key buckets, custom 429 handler with Retry-After header, differentiated limits for solver endpoints.

## What Was Built

### Rate Limiting Module (`backend/src/rate_limit.py`)
- Limiter configured with API-key extraction function
- Falls back to IP address for unauthenticated endpoints
- Default limit: 60 requests/minute
- headers_enabled=False (avoids Response type error with FastAPI models)

### Configuration (`backend/src/config.py`)
- `rate_limit_per_minute: int = 60` (standard endpoints)
- `rate_limit_solver_per_minute: int = 10` (compute-heavy endpoints)

### FastAPI Integration (`backend/app/main.py`)
- Custom `rate_limit_exceeded_handler` with Retry-After: 60 header
- Rate limit decorators on 5 protected endpoints:
  - `/solve` - 10/min (solver limit)
  - `/compare` - 10/min (solver limit)
  - `/generate-city` - 60/min (standard limit)
  - `/graphs` - 60/min (standard limit)
  - `/graphs/{graph_name}` - 60/min (standard limit)

## Technical Decisions

### 1. API-Key-Based Rate Limiting
- Each API key has its own rate limit bucket
- Prevents one team member from exhausting another's quota
- Falls back to IP for unauthenticated requests

### 2. Custom Exception Handler
- slowapi's default `_rate_limit_exceeded_handler` works with `_inject_headers`
- But `headers_enabled=True` causes errors when endpoints return Pydantic models (not Response objects)
- Solution: Custom handler that manually adds Retry-After header

### 3. Differentiated Limits
- Solver endpoints: 10/min (compute-heavy, protects backend resources)
- Standard endpoints: 60/min (lightweight operations)

## Commits

| Commit  | Type | Description                                    |
|---------|------|------------------------------------------------|
| ff1fcbc | feat | Add rate limiting module with slowapi          |
| ac38be8 | feat | Integrate rate limiting into FastAPI endpoints |
| bb18c69 | fix  | Add custom rate limit handler with Retry-After |

## Verification Results

| Criteria | Status |
|----------|--------|
| Rapid requests return 429 | PASS |
| 429 includes Retry-After header | PASS (60 seconds) |
| Different API keys independent | PASS |
| Solver limit < standard limit | PASS (10 vs 60) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Custom rate limit handler for Retry-After header**
- **Found during:** Task 3 testing
- **Issue:** slowapi's default handler with `headers_enabled=True` causes `Exception: parameter response must be an instance of starlette.responses.Response` when FastAPI endpoints return Pydantic models
- **Fix:** Created custom `rate_limit_exceeded_handler` that returns JSONResponse with Retry-After header
- **Files modified:** backend/app/main.py, backend/src/rate_limit.py
- **Commit:** bb18c69

## Dependencies

### Installed
- slowapi>=0.1.9

### Configuration
- RATE_LIMIT_PER_MINUTE (env var, default: 60)
- RATE_LIMIT_SOLVER_PER_MINUTE (env var, default: 10)

## Next Phase Readiness

- AUTH-03 (rate limiting) is satisfied
- Ready for Phase 3: Testing infrastructure
- No blockers identified
