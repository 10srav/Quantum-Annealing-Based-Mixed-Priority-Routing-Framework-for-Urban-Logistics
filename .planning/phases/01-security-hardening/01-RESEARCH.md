# Phase 1: Security Hardening - Research

**Researched:** 2026-02-04
**Domain:** FastAPI Security, Input Validation, Error Sanitization
**Confidence:** HIGH

## Summary

This research addresses four security requirements for the Quantum Priority Router API: path traversal prevention (SEC-01), error response sanitization (SEC-02), node count validation (SEC-03), and Pydantic input validation (SEC-04). The codebase currently has known vulnerabilities including direct file path construction from user input, generic exception handling that exposes internal details, and missing upper-bound validation on node counts.

The standard approach uses Python's `pathlib` for path traversal prevention, FastAPI's custom exception handlers for error sanitization, and Pydantic's `Field` constraints for input validation. All recommendations are well-established patterns with extensive documentation.

**Primary recommendation:** Implement layered defense: validate inputs at API boundary with Pydantic, sanitize file paths with pathlib, catch exceptions at endpoint level, and wrap unhandled exceptions with a global handler.

## Standard Stack

The established libraries/tools for this domain:

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| FastAPI | 0.115+ | Web framework with validation | Built-in Pydantic integration, exception handlers |
| Pydantic | 2.x | Data validation | Type-safe, automatic error messages, Field constraints |
| pathlib | stdlib | Path manipulation | `resolve()` + `is_relative_to()` is official pattern |
| logging | stdlib | Server-side logging | Standard Python logging for error capture |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| re | stdlib | Regex validation | Path/filename pattern allowlisting |
| typing | stdlib | Type hints | Annotated types for constraints |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pathlib | os.path | pathlib is cleaner, `is_relative_to()` built-in (Python 3.9+) |
| Custom exception handler | fastapi-guard middleware | More features but external dependency |
| Manual validation | nh3/bleach | Overkill for filename sanitization |

**Installation:**
No new packages required - all security features use FastAPI, Pydantic, and stdlib.

## Architecture Patterns

### Recommended Project Structure

```
backend/
├── app/
│   ├── main.py           # API endpoints + exception handlers
│   └── exceptions.py     # Custom exception classes (NEW)
├── src/
│   ├── config.py         # Settings including max_nodes
│   ├── data_models.py    # Pydantic models with validators
│   └── security.py       # Path validation utilities (NEW)
```

### Pattern 1: Path Traversal Prevention with Allowlist + Resolve

**What:** Validate file paths against both an allowlist pattern AND verify resolved path stays within base directory.
**When to use:** Any endpoint that constructs file paths from user input.

```python
# Source: Python docs + OWASP best practices
from pathlib import Path
import re

# Allowlist pattern: alphanumeric, hyphen, underscore only
GRAPH_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')

def validate_graph_path(graph_name: str, base_dir: Path) -> Path:
    """
    Validate and resolve graph file path safely.

    Args:
        graph_name: User-provided graph identifier
        base_dir: Allowed base directory (e.g., backend/data)

    Returns:
        Resolved absolute path to graph file

    Raises:
        ValueError: If path validation fails
    """
    # Step 1: Allowlist validation
    if not GRAPH_NAME_PATTERN.match(graph_name):
        raise ValueError("Invalid graph name: must be alphanumeric, hyphens, underscores only")

    # Step 2: Construct and resolve path
    filepath = (base_dir / f"{graph_name}.json").resolve()

    # Step 3: Verify path is within base directory
    base_resolved = base_dir.resolve()
    if not filepath.is_relative_to(base_resolved):
        raise ValueError("Invalid graph path: path traversal detected")

    return filepath
```

### Pattern 2: Global Exception Handler with Sanitization

**What:** Catch all unhandled exceptions, log full details server-side, return generic message to client.
**When to use:** Every FastAPI application in production.

```python
# Source: FastAPI docs + Better Stack guide
import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global handler for unexpected exceptions.
    Logs full error for debugging, returns safe message to client.
    """
    # Log full details server-side
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True  # Include stack trace in logs
    )

    # Return sanitized response to client
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )
```

### Pattern 3: Pydantic Field Constraints for Numeric Bounds

**What:** Use `Field(ge=..., le=...)` for min/max validation directly in model definition.
**When to use:** Any numeric parameter with business constraints (like max_nodes=25).

```python
# Source: Pydantic docs
from pydantic import BaseModel, Field
from src.config import get_settings

settings = get_settings()

class GenerateCityRequest(BaseModel):
    """Request model for city generation with validated bounds."""
    n_nodes: int = Field(
        default=10,
        ge=2,  # Minimum 2 nodes for a valid graph
        le=settings.max_nodes,  # Maximum from config (25)
        description="Number of nodes to generate"
    )
    priority_ratio: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Ratio of priority nodes (0.0-1.0)"
    )
    traffic_profile: str = Field(
        default="mixed",
        pattern=r"^(low|medium|high|mixed)$",
        description="Traffic intensity profile"
    )
    seed: int | None = Field(
        default=None,
        description="Random seed for reproducibility"
    )
```

### Pattern 4: Custom Exception Classes for Domain Errors

**What:** Define specific exception types for different error categories.
**When to use:** When you need different HTTP status codes for different failure modes.

```python
# Source: FastAPI docs exception handling
from fastapi import HTTPException

class GraphNotFoundError(HTTPException):
    """Raised when requested graph file doesn't exist."""
    def __init__(self, graph_name: str):
        super().__init__(
            status_code=404,
            detail=f"Graph '{graph_name}' not found"
        )

class InvalidGraphNameError(HTTPException):
    """Raised when graph name fails validation."""
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="Invalid graph name: use only letters, numbers, hyphens, and underscores"
        )

class NodeLimitExceededError(HTTPException):
    """Raised when node count exceeds maximum."""
    def __init__(self, max_nodes: int):
        super().__init__(
            status_code=400,
            detail=f"Node count exceeds maximum allowed ({max_nodes})"
        )
```

### Anti-Patterns to Avoid

- **Catching generic Exception and exposing str(e):** Leaks internal details. Always sanitize.
- **Using os.path.join() without resolve:** Doesn't prevent `..` traversal.
- **Validating only the pattern OR only the resolved path:** Use both - defense in depth.
- **Logging to stdout in production:** Use structured logging with proper handlers.
- **Trusting `filename.endswith('.json')` as security:** Attackers can use `../../../etc/passwd.json`.

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Path traversal check | String manipulation | `pathlib.is_relative_to()` | Edge cases with symlinks, `..` normalization |
| Input string constraints | Manual if/raise | `Field(pattern=..., max_length=...)` | Consistent errors, declarative, tested |
| Numeric range validation | Manual bounds check | `Field(ge=..., le=...)` | Automatic error messages, type-safe |
| Error response format | Custom dict building | `HTTPException(detail=...)` | Consistent JSON structure, status codes |

**Key insight:** FastAPI + Pydantic already handle 90% of input validation. The remaining 10% (file paths) requires explicit security code.

## Common Pitfalls

### Pitfall 1: Partial Path Validation

**What goes wrong:** Developer validates filename pattern but doesn't check resolved path, or vice versa.
**Why it happens:** Assumes one check is sufficient; doesn't understand attack vectors.
**How to avoid:** Always apply BOTH checks: (1) allowlist pattern, (2) resolved path containment.
**Warning signs:** Code uses `re.match()` OR `is_relative_to()` but not both.

### Pitfall 2: Exception Handler Order

**What goes wrong:** Global `Exception` handler catches before specific `HTTPException` handler.
**Why it happens:** FastAPI processes handlers in registration order for same exception types.
**How to avoid:** Register specific exception handlers first; global handler catches only truly unexpected errors.
**Warning signs:** Custom HTTPException subclasses return 500 instead of their defined status code.

### Pitfall 3: Validation in Config vs Runtime

**What goes wrong:** `max_nodes` is in config.py but validation uses hardcoded `25`.
**Why it happens:** Developer copies config value instead of referencing it.
**How to avoid:** Always reference `settings.max_nodes` in validators, not literal values.
**Warning signs:** Changing config doesn't change behavior; tests pass with wrong limits.

### Pitfall 4: Logging Sensitive Data

**What goes wrong:** Log message includes user input that could contain PII or attack payloads.
**Why it happens:** Debugging convenience; `logger.error(f"Bad input: {user_data}")`.
**How to avoid:** Log request ID and error type, not raw user input. Sanitize if logging input is necessary.
**Warning signs:** Logs contain full request bodies, file paths, or stack traces with user data.

### Pitfall 5: Inconsistent Error Response Format

**What goes wrong:** Some errors return `{"detail": "..."}`, others return `{"error": "...", "message": "..."}`.
**Why it happens:** Different developers, different endpoints, no standard.
**How to avoid:** Use FastAPI's HTTPException consistently; all errors should have `detail` field.
**Warning signs:** Frontend has multiple error parsing branches; API docs show inconsistent schemas.

## Code Examples

Verified patterns from official sources:

### Secure Graph Loading Endpoint

```python
# Full implementation combining all patterns
# Source: FastAPI docs, Python pathlib docs, OWASP guidelines

from pathlib import Path
import re
import logging
from fastapi import FastAPI, HTTPException

logger = logging.getLogger(__name__)

GRAPH_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]+$')
DATA_DIR = Path(__file__).parent.parent / "data"

@app.get("/graphs/{graph_name}")
async def get_graph(graph_name: str):
    """Get a specific sample city graph with path traversal protection."""

    # Validate graph name against allowlist pattern
    if not GRAPH_NAME_PATTERN.match(graph_name):
        raise HTTPException(
            status_code=400,
            detail="Invalid graph name: use only letters, numbers, hyphens, underscores"
        )

    # Construct and resolve path
    filepath = (DATA_DIR / f"{graph_name}.json").resolve()
    base_resolved = DATA_DIR.resolve()

    # Verify path is within allowed directory
    if not filepath.is_relative_to(base_resolved):
        logger.warning(f"Path traversal attempt detected: {graph_name}")
        raise HTTPException(
            status_code=400,
            detail="Invalid graph name"
        )

    # Check file exists
    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Graph not found")

    # Load and return (errors caught by global handler)
    import json
    with open(filepath, "r") as f:
        return json.load(f)
```

### Request Model with All Validations

```python
# Source: Pydantic docs
from pydantic import BaseModel, Field, field_validator
from typing import Literal

class GenerateCityRequest(BaseModel):
    """Validated request for city generation."""
    n_nodes: int = Field(default=10, ge=2, le=25)
    priority_ratio: float = Field(default=0.3, ge=0.0, le=1.0)
    traffic_profile: Literal["low", "medium", "high", "mixed"] = "mixed"
    seed: int | None = None

    @field_validator('n_nodes')
    @classmethod
    def validate_node_count(cls, v: int) -> int:
        """Additional validation with custom error message."""
        if v > 25:
            raise ValueError(f'Node count {v} exceeds maximum of 25')
        return v
```

### Exception Handler Registration

```python
# Source: FastAPI docs
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging

app = FastAPI()
logger = logging.getLogger(__name__)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with field-specific messages."""
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})

    return JSONResponse(
        status_code=400,
        content={"detail": "Validation error", "errors": errors}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with consistent format."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors."""
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred"}
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `os.path.join()` + string checks | `pathlib.resolve()` + `is_relative_to()` | Python 3.9 | Cleaner, safer path handling |
| `constr(regex=...)` | `Field(pattern=...)` | Pydantic 2.0 | Regex param renamed to pattern |
| Bare `except Exception` | Global exception handler | FastAPI best practice | Consistent error responses |
| `@validator` decorator | `@field_validator` decorator | Pydantic 2.0 | New API, mode parameter |

**Deprecated/outdated:**

- **`regex` parameter in Pydantic:** Use `pattern` instead (Pydantic 2.x)
- **`@validator` decorator:** Use `@field_validator` (Pydantic 2.x)
- **`bleach` library:** Use `nh3` if HTML sanitization needed (bleach unmaintained)

## Open Questions

Things that couldn't be fully resolved:

1. **Graph file caching strategy**
   - What we know: Current code loads files on each request; could cache at startup
   - What's unclear: Whether graphs change at runtime (user uploads?)
   - Recommendation: Assume static for now; cache if confirmed immutable

2. **Request ID for error tracking**
   - What we know: Best practice is to include request ID in errors for correlation
   - What's unclear: Whether logging infrastructure exists
   - Recommendation: Defer to observability phase; not blocking for basic security

3. **Rate limiting scope**
   - What we know: SEC requirements don't mention rate limiting
   - What's unclear: Whether DoS protection is implicit in security scope
   - Recommendation: Out of scope for this phase; flagged for future

## Sources

### Primary (HIGH confidence)

- [FastAPI Official Docs - Error Handling](https://fastapi.tiangolo.com/tutorial/handling-errors/) - Exception handlers, HTTPException
- [Pydantic Official Docs - Fields](https://docs.pydantic.dev/latest/concepts/fields/) - Field constraints
- [Pydantic Official Docs - Validators](https://docs.pydantic.dev/latest/concepts/validators/) - @field_validator
- [Python pathlib Documentation](https://docs.python.org/3/library/pathlib.html) - resolve(), is_relative_to()

### Secondary (MEDIUM confidence)

- [Better Stack - FastAPI Error Handling](https://betterstack.com/community/guides/scaling-python/error-handling-fastapi/) - Production error sanitization patterns
- [LoadForge - FastAPI Security](https://loadforge.com/guides/securing-your-fastapi-web-service-best-practices-and-techniques) - Security best practices overview

### Tertiary (LOW confidence)

- Web search results for path traversal prevention - verified against Python docs

## Metadata

**Confidence breakdown:**

- Standard stack: HIGH - all stdlib or FastAPI/Pydantic built-ins
- Architecture: HIGH - patterns from official documentation
- Pitfalls: MEDIUM - some from experience, verified against docs
- Code examples: HIGH - adapted from official documentation

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - stable domain)
