"""
FastAPI Application for Quantum Priority Router.
"""

import asyncio
import signal
import time
from functools import partial
from typing import Set

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
import json

from slowapi.errors import RateLimitExceeded

from src.security import validate_graph_path, DATA_DIR
from src.auth import verify_api_key
from src.rate_limit import limiter
from app.logging_config import configure_logging, get_logger, is_debug_enabled
from app.middleware import RequestContextMiddleware, get_request_id

logger = get_logger(__name__)

# Track active requests for graceful shutdown
active_requests: Set[asyncio.Task] = set()
shutdown_event = asyncio.Event()
from src.data_models import (
    CityGraph,
    SolverRequest,
    SolverResponse,
    ComparisonResponse,
    QUBOParams,
    GenerateCityRequest,
)
from src.qaoa_solver import quantum_solve, get_sampler_info, check_solver_health
from src.greedy_solver import greedy_solve
from src.metrics import compare_solutions
from src.simulator import generate_random_city
from src.config import get_settings


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for structured request/response logging.

    Uses request_id from RequestContextMiddleware and logs:
    - request_id (UUID)
    - timestamp (ISO format)
    - method (HTTP verb)
    - path (endpoint)
    - status_code
    - duration_ms
    - client_ip

    At DEBUG level, also logs request/response bodies.
    """

    async def dispatch(self, request: Request, call_next):
        # Get request_id from RequestContextMiddleware (single source of truth)
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.perf_counter()

        # Get client IP (handle proxy scenarios)
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # Log request body at DEBUG level only
        request_body = None
        if is_debug_enabled() and request.method in ("POST", "PUT", "PATCH"):
            try:
                body_bytes = await request.body()
                request_body = body_bytes.decode("utf-8")
                # Reconstruct request body stream for downstream handlers
                # FastAPI will re-read from the cached body
            except Exception:
                request_body = "<unreadable>"

        try:
            response = await call_next(request)
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log the request with all metadata
            log_data = {
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "client_ip": client_ip,
            }

            # Add request body at DEBUG level
            if request_body:
                log_data["request_body"] = request_body

            logger.info("request_completed", **log_data)

            # Note: X-Request-ID header is added by RequestContextMiddleware
            return response

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "request_failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip,
                error=str(exc),
            )
            raise


class RequestTrackingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to track active requests for graceful shutdown.

    Adds the current task to active_requests set on request start,
    removes it on completion. This allows the shutdown handler to
    wait for all in-flight requests to complete.
    """

    async def dispatch(self, request: Request, call_next):
        task = asyncio.current_task()
        if task is not None:
            active_requests.add(task)
        try:
            response = await call_next(request)
            return response
        finally:
            if task is not None:
                active_requests.discard(task)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler with graceful shutdown.

    On startup: Configures logging.
    On shutdown: Waits for in-flight requests to complete (up to shutdown_timeout).
    """
    # Startup: Configure structured logging
    settings = get_settings()
    configure_logging(settings.log_level)
    logger.info("startup", service="quantum-priority-router", log_level=settings.log_level)
    yield
    # Shutdown - wait for in-flight requests
    logger.info(
        "shutdown_initiated",
        service="quantum-priority-router",
        active_requests=len(active_requests)
    )
    shutdown_event.set()

    if active_requests:
        logger.info(
            "waiting_for_requests",
            active_count=len(active_requests),
            timeout_seconds=settings.shutdown_timeout
        )
        try:
            await asyncio.wait_for(
                asyncio.gather(*active_requests, return_exceptions=True),
                timeout=settings.shutdown_timeout
            )
            logger.info("graceful_shutdown_complete", service="quantum-priority-router")
        except asyncio.TimeoutError:
            logger.warning(
                "shutdown_timeout_reached",
                timeout_seconds=settings.shutdown_timeout,
                remaining_requests=len(active_requests)
            )
    else:
        logger.info("shutdown_complete", service="quantum-priority-router", message="No active requests")


app = FastAPI(
    title="Quantum Priority Router API",
    description="Quantum-classical hybrid routing optimization for urban logistics",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware configuration
# Note: Middleware executes in REVERSE order of registration (last added = first to execute)
# So we add in order: CORS, Logging, RequestContext, RequestTracking
# Execution order: RequestTracking -> RequestContext -> Logging -> CORS -> Route handler
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging middleware (runs after RequestContextMiddleware sets request_id)
app.add_middleware(LoggingMiddleware)

# Request context middleware (sets request_id for all other middleware)
app.add_middleware(RequestContextMiddleware)

# Request tracking middleware (runs first - tracks active requests for graceful shutdown)
app.add_middleware(RequestTrackingMiddleware)

# Rate limiting
app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded with proper 429 response and Retry-After header.
    RFC 6585 recommends including Retry-After header with 429 responses.

    Note: We use a custom handler instead of slowapi's default because
    headers_enabled=True causes errors with FastAPI response models.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    # Approximate retry time: 60 seconds for per-minute rate limits
    retry_after = 60
    return JSONResponse(
        status_code=429,
        content={
            "detail": f"Rate limit exceeded: {exc.detail}",
            "request_id": request_id
        },
        headers={"Retry-After": str(retry_after)}
    )


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


async def run_solver_with_timeout(solver_func, *args, **kwargs):
    """
    Run a synchronous solver function with timeout.

    Wraps sync function in executor and applies timeout.
    Returns 504 Gateway Timeout if solver exceeds configured timeout.
    """
    loop = asyncio.get_event_loop()
    func = partial(solver_func, *args, **kwargs)
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, func),
            timeout=settings.solver_timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail=f"Solver request timed out after {settings.solver_timeout_seconds} seconds"
        )


# Exception handlers - sanitize errors before returning to clients
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors with field-specific messages."""
    request_id = getattr(request.state, "request_id", "unknown")
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        errors.append({"field": field, "message": error["msg"]})
    return JSONResponse(
        status_code=400,
        content={
            "detail": "Validation error",
            "errors": errors,
            "request_id": request_id
        }
    )


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions with consistent format including request_id."""
    request_id = getattr(request.state, "request_id", "unknown")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "request_id": request_id
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch-all for unexpected errors. Logs full details, returns safe message with request_id."""
    # Get request_id from middleware (always available via RequestContextMiddleware)
    request_id = getattr(request.state, "request_id", "unknown")

    logger.error(
        "unhandled_exception",
        request_id=request_id,
        method=request.method,
        path=request.url.path,
        error_type=type(exc).__name__,
        error_message=str(exc),
        exc_info=True
    )

    # Return safe message with request_id for support reference
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again later.",
            "request_id": request_id
        }
    )


@app.get("/health")
async def health_check():
    """
    Health check endpoint with dependency status.

    Returns:
        - status: "healthy" | "degraded" | "unhealthy"
        - service: service name
        - timestamp: ISO timestamp
        - dependencies: list of dependency statuses
    """
    from datetime import datetime, timezone

    # Check dependencies
    solver_health = check_solver_health()

    dependencies = [solver_health]

    # Determine overall status (worst of all dependencies)
    statuses = [d["status"] for d in dependencies]
    if "unhealthy" in statuses:
        overall_status = "unhealthy"
    elif "degraded" in statuses:
        overall_status = "degraded"
    else:
        overall_status = "healthy"

    return {
        "status": overall_status,
        "service": "quantum-priority-router",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dependencies": dependencies
    }


@app.post("/solve", response_model=SolverResponse)
@limiter.limit(f"{settings.rate_limit_solver_per_minute}/minute")
async def solve_route(request: Request, solver_request: SolverRequest, _: bool = Depends(verify_api_key)):
    """
    Solve routing problem using specified solver.

    - **quantum**: Uses QAOA (Quantum Approximate Optimization Algorithm)
    - **greedy**: Uses nearest-neighbor heuristic

    Returns 504 Gateway Timeout if solver exceeds configured timeout.
    """
    if solver_request.solver == "quantum":
        result = await run_solver_with_timeout(
            quantum_solve,
            solver_request.graph,
            solver_request.params,
            use_mock=settings.qaoa_use_mock
        )
    else:
        result = await run_solver_with_timeout(
            greedy_solve,
            solver_request.graph
        )

    return result


@app.post("/compare", response_model=ComparisonResponse)
@limiter.limit(f"{settings.rate_limit_solver_per_minute}/minute")
async def compare_solvers(request: Request, graph: CityGraph, _: bool = Depends(verify_api_key)):
    """
    Run both quantum and greedy solvers and compare results.

    Returns 504 Gateway Timeout if either solver exceeds configured timeout.
    """
    quantum_result = await run_solver_with_timeout(
        quantum_solve,
        graph,
        use_mock=settings.qaoa_use_mock
    )
    greedy_result = await run_solver_with_timeout(
        greedy_solve,
        graph
    )

    return compare_solutions(greedy_result, quantum_result)


@app.post("/generate-city", response_model=CityGraph)
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def generate_city(request: Request, city_request: GenerateCityRequest, _: bool = Depends(verify_api_key)):
    """
    Generate a random city graph for testing.

    Parameters are validated:
    - n_nodes: 2-25 (QAOA solver limit)
    - priority_ratio: 0.0-1.0
    - traffic_profile: low, medium, high, or mixed
    """
    return generate_random_city(
        n_nodes=city_request.n_nodes,
        priority_ratio=city_request.priority_ratio,
        traffic_profile=city_request.traffic_profile,
        seed=city_request.seed
    )


@app.get("/graphs")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def list_graphs(request: Request, _: bool = Depends(verify_api_key)):
    """
    List available sample city graphs.
    """
    graphs = []

    if DATA_DIR.exists():
        for filepath in DATA_DIR.iterdir():
            if filepath.suffix == ".json":
                graphs.append({
                    "name": filepath.stem,
                    "path": f"/graphs/{filepath.stem}"
                })

    return {"graphs": graphs}


@app.get("/graphs/{graph_name}")
@limiter.limit(f"{settings.rate_limit_per_minute}/minute")
async def get_graph(request: Request, graph_name: str, _: bool = Depends(verify_api_key)):
    """
    Get a specific sample city graph.

    Security: Uses allowlist validation to prevent path traversal attacks.
    Only alphanumeric names with hyphens/underscores are accepted.
    """
    try:
        filepath = validate_graph_path(graph_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not filepath.exists():
        raise HTTPException(status_code=404, detail="Graph not found")

    with open(filepath, "r") as f:
        data = json.load(f)

    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
