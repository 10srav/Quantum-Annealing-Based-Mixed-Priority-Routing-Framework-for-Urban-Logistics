# Roadmap: Quantum Routing Framework - Production Hardening

## Overview

This roadmap transforms the functional quantum routing prototype into a production-ready team tool. The work progresses from securing the API foundation (fixing critical vulnerabilities), through authentication and observability layers, to comprehensive testing that validates the hardening, and finally to production infrastructure. Each phase delivers a complete, verifiable capability that unblocks the next.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Security Hardening** - Fix vulnerabilities, sanitize errors, validate inputs ✓
- [x] **Phase 2: Authentication** - API key auth with rate limiting and timeouts ✓
- [x] **Phase 3: Observability** - Structured logging, health checks, request tracing ✓
- [x] **Phase 4: Testing** - Validation tests, security tests, solver correctness tests ✓
- [x] **Phase 5: Infrastructure** - Docker production build, CORS config, graceful shutdown ✓

## Phase Details

### Phase 1: Security Hardening
**Goal**: API is secure from known vulnerabilities and handles errors safely
**Depends on**: Nothing (critical foundation)
**Requirements**: SEC-01, SEC-02, SEC-03, SEC-04
**Success Criteria** (what must be TRUE):
  1. Graph loading endpoint rejects path traversal attempts (../../../etc/passwd returns 400, not file contents)
  2. API error responses contain generic messages only (no stack traces, file paths, or library names visible to clients)
  3. Node count requests above 25 are rejected with clear validation error
  4. Malformed JSON and missing required fields return 400 with field-specific validation messages
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md - Path traversal fix and file access hardening ✓
- [x] 01-02-PLAN.md - Error sanitization and exception handling ✓
- [x] 01-03-PLAN.md - Input validation with Pydantic models ✓

### Phase 2: Authentication
**Goal**: API access is controlled and protected from abuse
**Depends on**: Phase 1 (secure foundation before exposing auth)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04
**Success Criteria** (what must be TRUE):
  1. Requests without valid API key header receive 401 Unauthorized
  2. API keys are not stored in plaintext (hashed comparison only)
  3. Excessive requests from same key are throttled with 429 response and retry-after header
  4. Solver endpoint requests that exceed timeout return 504 Gateway Timeout (not hang indefinitely)
**Plans**: TBD

Plans:
- [x] 02-01-PLAN.md - API key authentication middleware ✓
- [x] 02-02-PLAN.md - Rate limiting with slowapi ✓
- [x] 02-03-PLAN.md - Request timeout configuration ✓

### Phase 3: Observability
**Goal**: Operators have visibility into system behavior and health
**Depends on**: Phase 1 (logging must use sanitized error context)
**Requirements**: OBS-01, OBS-02, OBS-03, OBS-04
**Success Criteria** (what must be TRUE):
  1. Every request generates a JSON log entry with request ID, timestamp, endpoint, and duration
  2. Health endpoint reports solver availability status and can detect when Qiskit is unavailable
  3. Errors are logged with full context server-side while clients receive only request ID for support reference
  4. Request/response bodies can be logged at DEBUG level without appearing in production INFO logs
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md - Structured logging with structlog ✓
- [x] 03-02-PLAN.md - Health check endpoint with dependency status ✓
- [x] 03-03-PLAN.md - Request context and correlation IDs ✓

### Phase 4: Testing
**Goal**: Security hardening and solver correctness are validated with automated tests
**Depends on**: Phase 1, 2, 3 (tests validate all hardening work)
**Requirements**: TEST-01, TEST-02, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. Test suite includes cases for malformed JSON, missing fields, and out-of-range values that verify 400 responses
  2. Test suite includes path traversal attempts and verifies error messages contain no internal paths
  3. Test suite verifies QUBO one-hot constraints are satisfied and priority nodes appear before normal nodes in solutions
  4. Test suite verifies mock sampler returns complete routes that visit all nodes
**Plans**: 3 plans

Plans:
- [x] 04-01-PLAN.md - API input validation test suite ✓
- [x] 04-02-PLAN.md - Security test suite ✓
- [x] 04-03-PLAN.md - QUBO and solver correctness tests ✓

### Phase 5: Infrastructure
**Goal**: Application is deployable to production with proper configuration
**Depends on**: Phase 4 (deploy only tested, validated code)
**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Docker image builds with multi-stage process (builder stage separate from runtime)
  2. CORS origins are configurable via environment variable and reject requests from unlisted origins
  3. In-flight solver requests complete before shutdown (SIGTERM triggers graceful drain)
  4. Docker Compose production profile sets memory and CPU limits on containers
**Plans**: 3 plans

Plans:
- [x] 05-01-PLAN.md - Production Dockerfile with multi-stage build ✓
- [x] 05-02-PLAN.md - Environment-based CORS and configuration ✓
- [x] 05-03-PLAN.md - Graceful shutdown and Docker Compose production profile ✓

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Security Hardening | 3/3 | ✓ Complete | 2026-02-05 |
| 2. Authentication | 3/3 | ✓ Complete | 2026-02-05 |
| 3. Observability | 3/3 | ✓ Complete | 2026-02-05 |
| 4. Testing | 3/3 | ✓ Complete | 2026-02-05 |
| 5. Infrastructure | 3/3 | ✓ Complete | 2026-02-05 |

---
*Roadmap created: 2026-02-04*
*Depth: standard (5-8 phases)*
*Coverage: 20/20 v1 requirements mapped*
