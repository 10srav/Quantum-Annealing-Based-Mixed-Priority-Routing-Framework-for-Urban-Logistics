---
phase: 02
plan: 01
subsystem: authentication
tags: [security, api-key, middleware, fastapi]

dependency_graph:
  requires: [01-security-hardening]
  provides: [api-key-auth, auth-middleware]
  affects: [02-02, 02-03, frontend]

tech_stack:
  added: []
  patterns: [header-based-auth, hash-comparison, timing-safe-validation]

key_files:
  created:
    - backend/src/auth.py
  modified:
    - backend/src/config.py
    - backend/app/main.py
    - backend/.env.example

decisions:
  - id: AUTH-HASH
    choice: SHA-256 hash storage for API keys
    reason: Standard secure approach - never store plaintext secrets

metrics:
  duration: ~5 min
  completed: 2026-02-05
---

# Phase 02 Plan 01: API Key Authentication Summary

**One-liner:** API key middleware with SHA-256 hashing and timing-safe comparison protecting all data endpoints

## What Was Built

### API Key Authentication Module (`backend/src/auth.py`)

Created authentication module with:

1. **`hash_api_key(key: str) -> str`**: SHA-256 hashing function for generating key hashes
2. **`verify_api_key(x_api_key: str = Header(...))`**: FastAPI dependency that:
   - Extracts X-API-Key header (required)
   - Hashes the provided key
   - Uses `secrets.compare_digest` for timing-safe comparison
   - Raises 401 HTTPException on mismatch

### Configuration Updates (`backend/src/config.py`)

Added `api_key_hash: str = ""` setting to store the hash (never plaintext).

### Endpoint Protection (`backend/app/main.py`)

Applied `Depends(verify_api_key)` to all data endpoints:
- POST `/solve`
- POST `/compare`
- POST `/generate-city`
- GET `/graphs`
- GET `/graphs/{graph_name}`

Health endpoint `/health` remains public for monitoring systems.

## Verification Results

| Test | Expected | Actual |
|------|----------|--------|
| /health without key | 200 OK | 200 OK |
| /graphs without key | 401/422 | 422 "Field required" |
| /graphs with invalid key | 401 | 401 "Invalid API key" |
| /graphs with valid key | 200 OK | 200 OK |
| /generate-city with valid key | 200 OK | 200 OK |

## Commits

| Hash | Type | Description |
|------|------|-------------|
| db660f1 | feat | Add API key authentication module |
| e6123e7 | feat | Apply API key auth to protected endpoints |
| 75cc63b | fix | Remove emojis from startup logs for Windows compatibility |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed Windows Unicode encoding error in startup logs**

- **Found during:** Task 3 (server startup for testing)
- **Issue:** Emoji characters in `print()` statements caused `UnicodeEncodeError` on Windows cp1252 encoding
- **Fix:** Replaced emoji characters with plain text in lifespan print statements
- **Files modified:** backend/app/main.py
- **Commit:** 75cc63b

## Security Notes

- API keys are **never** stored in plaintext - only SHA-256 hashes
- Timing-safe comparison (`secrets.compare_digest`) prevents timing attacks
- The `.env` file with actual key hash is in `.gitignore` (not committed)
- `.env.example` documents how to generate hashes

## Key Artifacts

```python
# backend/src/auth.py - Core authentication
def verify_api_key(x_api_key: str = Header(...)) -> bool:
    settings = get_settings()
    provided_hash = hash_api_key(x_api_key)
    if not settings.api_key_hash or not secrets.compare_digest(provided_hash, settings.api_key_hash):
        raise HTTPException(status_code=401, detail="Invalid API key")
    return True
```

```python
# backend/app/main.py - Endpoint protection pattern
@app.post("/solve", response_model=SolverResponse)
async def solve_route(request: SolverRequest, _: bool = Depends(verify_api_key)):
```

## Next Phase Readiness

Ready for 02-02 (Rate Limiting):
- Auth middleware pattern established
- Endpoint protection in place
- Foundation for per-key rate limiting
