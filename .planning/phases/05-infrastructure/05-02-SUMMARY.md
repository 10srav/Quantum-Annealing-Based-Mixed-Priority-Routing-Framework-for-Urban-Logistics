---
phase: 05
plan: 02
subsystem: infrastructure
tags: [cors, security, fastapi, pydantic]

dependency-graph:
  requires: [01-security-hardening, 02-authentication]
  provides: [environment-cors-config, cors-origin-validation]
  affects: [deployment, frontend-integration]

tech-stack:
  added: []
  patterns: [property-based-config, model-validator]

key-files:
  created: []
  modified:
    - backend/src/config.py
    - backend/tests/test_security.py

decisions:
  - id: cors-property
    choice: "Use property for cors_origins instead of pydantic field"
    reason: "Pydantic-settings tries to JSON-parse list fields before validators run"
  - id: cors-parse-formats
    choice: "Support both comma-separated and JSON array formats"
    reason: "Flexibility for different deployment environments"
  - id: wildcard-production-reject
    choice: "Reject wildcard '*' in production environment only"
    reason: "Allow development flexibility while enforcing security in production"

metrics:
  duration: ~6 min
  completed: 2026-02-05
---

# Phase 5 Plan 02: CORS Environment Configuration Summary

**One-liner:** Environment-driven CORS with comma/JSON parsing and production wildcard rejection.

## What Was Built

1. **Environment-Based CORS Configuration** (Task 1)
   - Added `parse_cors_origins_value()` function supporting:
     - Comma-separated format: `"https://a.com,https://b.com"`
     - JSON array format: `'["https://a.com","https://b.com"]'`
     - Single value: `"https://app.example.com"`
   - Added `get_cors_origins_from_env()` to read CORS_ORIGINS env var
   - Added `environment` field (development/staging/production)
   - Added model validator to reject wildcard `*` in production

2. **CORS Behavior Tests** (Task 2)
   - TestCORSBehavior class (6 tests):
     - Allowed origins receive CORS headers
     - Disallowed origins do NOT receive CORS headers
     - Preflight handling for both allowed and disallowed origins
     - No-origin requests (server-to-server) handled correctly
   - TestCORSConfiguration class (7 tests):
     - Comma-separated parsing
     - JSON array parsing
     - Single value parsing
     - Whitespace trimming
     - Empty value filtering
     - Wildcard rejection in production
     - Wildcard allowed in development

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Config approach | Property instead of field | Pydantic-settings JSON-parses lists before validators run |
| Parse formats | Comma + JSON array | Different tools/platforms prefer different formats |
| Wildcard behavior | Production-only rejection | Balances dev convenience with prod security |

## Verification Results

All must_haves verified:
- CORS_ORIGINS env var parsed as comma-separated or JSON array
- Default localhost origins work for development
- Requests from unlisted origins get no CORS headers (browser blocks)
- Wildcard "*" rejected when ENVIRONMENT=production

## Files Modified

| File | Changes |
|------|---------|
| backend/src/config.py | Added CORS parsing functions, environment field, model validator |
| backend/tests/test_security.py | Added 13 CORS tests (6 behavior + 7 config) |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| 1a0a24c | feat | Add environment-based CORS configuration |
| 1109b25 | test | Add CORS behavior and configuration tests |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for:** Phase 5 remaining plans (Dockerfile, Docker Compose)

**Dependencies satisfied:**
- CORS origins are now environment-configurable
- Security validation prevents wildcard in production
- All tests pass (70 tests in test_security.py)

**Notes for deployment:**
- Set `CORS_ORIGINS` env var in production to allowed frontend domains
- Set `ENVIRONMENT=production` to enable wildcard rejection
- Format: comma-separated (recommended) or JSON array
