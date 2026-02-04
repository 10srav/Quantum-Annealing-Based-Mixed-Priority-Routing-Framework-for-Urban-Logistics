"""
FastAPI Application for Quantum Priority Router.
"""

import asyncio
import logging
from functools import partial

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import json

from slowapi.errors import RateLimitExceeded

from src.security import validate_graph_path, DATA_DIR
from src.auth import verify_api_key
from src.rate_limit import limiter

logger = logging.getLogger(__name__)
from src.data_models import (
    CityGraph,
    SolverRequest,
    SolverResponse,
    ComparisonResponse,
    QUBOParams,
    GenerateCityRequest,
)
from src.qaoa_solver import quantum_solve, get_sampler_info
from src.greedy_solver import greedy_solve
from src.metrics import compare_solutions
from src.simulator import generate_random_city
from src.config import get_settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    print("Quantum Priority Router API starting...")
    yield
    # Shutdown
    print("Shutting down...")


app = FastAPI(
    title="Quantum Priority Router API",
    description="Quantum-classical hybrid routing optimization for urban logistics",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting
app.state.limiter = limiter


async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Handle rate limit exceeded with proper 429 response and Retry-After header.
    RFC 6585 recommends including Retry-After header with 429 responses.

    Note: We use a custom handler instead of slowapi's default because
    headers_enabled=True causes errors with FastAPI response models.
    """
    # Approximate retry time: 60 seconds for per-minute rate limits
    retry_after = 60
    return JSONResponse(
        status_code=429,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
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
    """Catch-all for unexpected errors. Logs full details, returns safe message."""
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}",
        exc_info=True
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again later."}
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "quantum-priority-router",
        "qaoa_info": get_sampler_info()
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
