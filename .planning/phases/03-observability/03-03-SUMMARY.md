---
phase: 03-observability
plan: 03
subsystem: request-context
tags: [correlation-id, middleware, request-tracking, error-handling, contextvars]
dependency-graph:
  requires: [03-01-structured-logging]
  provides: [request-context-middleware, correlation-id-tracking, error-request-id]
  affects: [support-workflows, distributed-tracing]
tech-stack:
  added: []
  patterns: [contextvars-for-async, middleware-chain, request-state]
key-files:
  created:
    - backend/app/middleware.py
  modified:
    - backend/app/main.py
decisions:
  - id: CTX-01
    choice: "ContextVar for request_id"
    reason: "Enables access to request_id anywhere in async context without passing through call stack"
  - id: CTX-02
    choice: "Support incoming X-Request-ID header"
    reason: "Enables distributed tracing when requests flow through multiple services"
  - id: CTX-03
    choice: "request_id in ALL error responses"
    reason: "Users can reference request_id when reporting issues for support correlation"
metrics:
  duration: 4 min
  completed: 2026-02-04
---

# Phase 03 Plan 03: Request Context Middleware Summary

Request correlation IDs that persist through entire request lifecycle for error tracking and support workflows.

## What Was Built

### Request Context Middleware (`backend/app/middleware.py`)

New dedicated middleware module providing:

- `RequestContextMiddleware` - Assigns unique UUID to each request
- `get_request_id()` - Helper function using contextvars for async access
- Support for incoming `X-Request-ID` header (distributed tracing)
- `X-Request-ID` header added to all responses
- `request.state.request_id` available in all handlers

```python
from app.middleware import RequestContextMiddleware, get_request_id

# Use in any async context
request_id = get_request_id()

# Or from request state in handlers
request_id = request.state.request_id
```

### Updated Error Handlers (`backend/app/main.py`)

All error responses now include `request_id`:

1. **Validation errors** (400) - `request_id` in response body
2. **HTTP exceptions** (4xx) - `request_id` in response body
3. **Global exceptions** (500) - `request_id` in response body (no internal details)
4. **Rate limit exceeded** (429) - `request_id` in response body

### Middleware Integration

- `RequestContextMiddleware` registered as outermost middleware (runs first)
- `LoggingMiddleware` updated to use request_id from request.state (single source of truth)
- Removed duplicate request_id generation from LoggingMiddleware

## Example Responses

### Success Response

```
HTTP/1.1 200 OK
x-request-id: 7d55e207-3556-49af-b0f0-61a4c7ac45b4
```

### Error Response (404)

```json
{
  "detail": "Not Found",
  "request_id": "c0f58537-1f1a-4fb2-b56d-532a6e8366f7"
}
```

### Validation Error (400)

```json
{
  "detail": "Validation error",
  "errors": [
    {"field": "body.n_nodes", "message": "Input should be less than or equal to 25"}
  ],
  "request_id": "99c48c1d-6215-4d4d-866e-a7a65289bbc9"
}
```

### Custom Request ID Passthrough

```bash
curl -H "X-Request-ID: custom-test-123" http://localhost:8000/health
# Response header: x-request-id: custom-test-123
```

## Deviations from Plan

None - plan executed exactly as written.

## Commits

| Commit | Type | Description |
|--------|------|-------------|
| a3ca31e | feat | Add request context middleware with correlation ID |
| 5549ac7 | feat | Integrate middleware and update error handlers |

## Verification Results

- [x] Every response includes X-Request-ID header
- [x] Error responses include request_id in JSON body
- [x] Server logs full error context (request_id, path, method, error)
- [x] Client responses contain NO internal details (paths, stack traces)
- [x] Incoming X-Request-ID header is respected (distributed tracing support)
- [x] request.state.request_id available in all request handlers
- [x] get_request_id() helper available for async context access

## Next Phase Readiness

**Phase 03 Observability complete:**
- 03-01: Structured JSON logging with request correlation
- 03-02: Metrics endpoint with dependency health checks
- 03-03: Request context middleware with correlation IDs

**Ready for Phase 04 (Testing):**
- All observability infrastructure in place
- Request tracking enables test debugging
- Structured logs enable test verification

**Dependencies satisfied:**
- Error responses include request_id for support reference
- Middleware chain properly ordered
- Context variable enables logging anywhere in async context

**No blockers identified.**
