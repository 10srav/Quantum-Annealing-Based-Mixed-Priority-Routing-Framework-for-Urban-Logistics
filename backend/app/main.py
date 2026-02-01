"""
FastAPI Application for Quantum Priority Router.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import json
import os

from src.data_models import (
    CityGraph,
    SolverRequest,
    SolverResponse,
    ComparisonResponse,
    QUBOParams,
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
    print("🚀 Quantum Priority Router API starting...")
    yield
    # Shutdown
    print("👋 Shutting down...")


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


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "quantum-priority-router",
        "qaoa_info": get_sampler_info()
    }


@app.post("/solve", response_model=SolverResponse)
async def solve_route(request: SolverRequest):
    """
    Solve routing problem using specified solver.
    
    - **quantum**: Uses QAOA (Quantum Approximate Optimization Algorithm)
    - **greedy**: Uses nearest-neighbor heuristic
    """
    try:
        if request.solver == "quantum":
            result = quantum_solve(
                request.graph,
                request.params,
                use_mock=settings.qaoa_use_mock
            )
        else:
            result = greedy_solve(request.graph)
        
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/compare", response_model=ComparisonResponse)
async def compare_solvers(graph: CityGraph):
    """
    Run both quantum and greedy solvers and compare results.
    """
    try:
        quantum_result = quantum_solve(
            graph,
            use_mock=settings.qaoa_use_mock
        )
        greedy_result = greedy_solve(graph)
        
        return compare_solutions(greedy_result, quantum_result)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/generate-city", response_model=CityGraph)
async def generate_city(
    n_nodes: int = 10,
    priority_ratio: float = 0.3,
    traffic_profile: str = "mixed",
    seed: int | None = None
):
    """
    Generate a random city graph for testing.
    """
    try:
        return generate_random_city(
            n_nodes=n_nodes,
            priority_ratio=priority_ratio,
            traffic_profile=traffic_profile,
            seed=seed
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/graphs")
async def list_graphs():
    """
    List available sample city graphs.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    graphs = []
    
    if os.path.exists(data_dir):
        for filename in os.listdir(data_dir):
            if filename.endswith(".json"):
                graphs.append({
                    "name": filename.replace(".json", ""),
                    "path": f"/graphs/{filename.replace('.json', '')}"
                })
    
    return {"graphs": graphs}


@app.get("/graphs/{graph_name}")
async def get_graph(graph_name: str):
    """
    Get a specific sample city graph.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    filepath = os.path.join(data_dir, f"{graph_name}.json")
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Graph not found")
    
    with open(filepath, "r") as f:
        data = json.load(f)
    
    return data


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
