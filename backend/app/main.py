"""
FastAPI Application for Quantum Priority Router.
"""

import logging

from fastapi import FastAPI, HTTPException, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from contextlib import asynccontextmanager
import json

from src.security import validate_graph_path, DATA_DIR
from src.auth import verify_api_key

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
async def solve_route(request: SolverRequest, _: bool = Depends(verify_api_key)):
    """
    Solve routing problem using specified solver.

    - **quantum**: Uses QAOA (Quantum Approximate Optimization Algorithm)
    - **greedy**: Uses nearest-neighbor heuristic
    """
    if request.solver == "quantum":
        result = quantum_solve(
            request.graph,
            request.params,
            use_mock=settings.qaoa_use_mock
        )
    else:
        result = greedy_solve(request.graph)

    return result


@app.post("/compare", response_model=ComparisonResponse)
async def compare_solvers(graph: CityGraph, _: bool = Depends(verify_api_key)):
    """
    Run both quantum and greedy solvers and compare results.
    """
    quantum_result = quantum_solve(
        graph,
        use_mock=settings.qaoa_use_mock
    )
    greedy_result = greedy_solve(graph)

    return compare_solutions(greedy_result, quantum_result)


@app.post("/generate-city", response_model=CityGraph)
async def generate_city(request: GenerateCityRequest, _: bool = Depends(verify_api_key)):
    """
    Generate a random city graph for testing.

    Parameters are validated:
    - n_nodes: 2-25 (QAOA solver limit)
    - priority_ratio: 0.0-1.0
    - traffic_profile: low, medium, high, or mixed
    """
    return generate_random_city(
        n_nodes=request.n_nodes,
        priority_ratio=request.priority_ratio,
        traffic_profile=request.traffic_profile,
        seed=request.seed
    )


@app.get("/graphs")
async def list_graphs(_: bool = Depends(verify_api_key)):
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
async def get_graph(graph_name: str, _: bool = Depends(verify_api_key)):
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
