---
phase: 01-security-hardening
plan: 03
subsystem: api-validation
tags: [pydantic, validation, dos-prevention, input-sanitization]

dependency-graph:
  requires: [01-02]
  provides: [input-validation, node-count-limits, request-models]
  affects: [frontend-api-calls, testing]

tech-stack:
  added: []
  patterns: [pydantic-field-constraints, literal-types, request-body-models]

key-files:
  created: []
  modified:
    - backend/src/data_models.py
    - backend/app/main.py

decisions:
  - id: 01-03-D1
    area: api
    choice: "JSON body over query parameters for generate-city"
    why: "Enables Pydantic validation on request body; breaking change acceptable for testing endpoint"

metrics:
  duration: ~2 min
  completed: 2026-02-05
---

# Phase 01 Plan 03: Input Validation Summary

**One-liner:** Pydantic-validated GenerateCityRequest model with strict bounds (2-25 nodes, 0-1 priority ratio, enum traffic profile)

## What Was Done

### Task 1: Add GenerateCityRequest model with validated bounds
- **Commit:** e6c0004
- **Files:** backend/src/data_models.py
- **Changes:**
  - Added `GenerateCityRequest` Pydantic model before `SolverRequest`
  - `n_nodes`: int with `ge=2, le=25` constraints (QAOA solver limit)
  - `priority_ratio`: float with `ge=0.0, le=1.0` constraints
  - `traffic_profile`: `Literal["low", "medium", "high", "mixed"]` for enum validation
  - `seed`: optional int for reproducibility

### Task 2: Update generate-city endpoint to use request model
- **Commit:** d9e209f
- **Files:** backend/app/main.py
- **Changes:**
  - Added `GenerateCityRequest` to imports from data_models
  - Replaced query parameters with `request: GenerateCityRequest` body parameter
  - Updated docstring to document validated parameters
  - Endpoint now returns 400 with field-specific errors for invalid input

## Verification Results

All success criteria verified:

| Criterion | Result |
|-----------|--------|
| n_nodes > 25 returns 400 with field-specific error | PASS |
| n_nodes < 2 returns 400 | PASS |
| priority_ratio outside 0.0-1.0 returns 400 | PASS |
| traffic_profile validates enum values | PASS |
| Valid requests return city graph | PASS |
| Validation errors include field name | PASS |

Example error response for `n_nodes=30`:
```json
{
  "detail": "Validation error",
  "errors": [
    {"field": "body.n_nodes", "message": "Input should be less than or equal to 25"}
  ]
}
```

## Deviations from Plan

None - plan executed exactly as written.

## Decisions Made

1. **JSON body over query parameters** (01-03-D1)
   - Changed `/generate-city` from query parameters to JSON body
   - Enables Pydantic validation via request model
   - Breaking change acceptable since this is a testing endpoint
   - Frontend API calls will need to send JSON body instead of query params

## Technical Notes

- The `le=25` constraint is hardcoded intentionally - documented in PROJECT.md as QAOA solver limit
- `Literal` type already imported in data_models.py, no new imports needed
- Validation errors automatically handled by existing `RequestValidationError` handler from 01-02

## Security Impact

- **DoS Prevention:** Node counts above 25 now rejected at API layer before any computation
- **Input Sanitization:** All generate-city parameters validated with specific constraints
- **Error Handling:** Invalid inputs return 400 with field-specific messages (not 500 with stack traces)

## Next Phase Readiness

Phase 1 (Security Hardening) is now complete:
- [x] 01-01: Path traversal prevention
- [x] 01-02: Error sanitization
- [x] 01-03: Input validation

Ready to proceed to Phase 2 (Core Solver).
