"""
QAOA Solver for Priority-Constrained Routing.

Uses Qiskit's QAOA (Quantum Approximate Optimization Algorithm) to solve the
QUBO formulation of the mixed-priority traveling salesman problem.
"""

import time
from typing import Any

from .data_models import CityGraph, QUBOParams, SolverResponse
from .qubo_builder import build_qubo, decode_route, validate_route, compute_route_metrics
from .config import get_settings

# Import dimod for BQM handling
from dimod import SampleSet

# Conditional import for Qiskit (allows running without Qiskit installed)
try:
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.converters import QuadraticProgramToQubo
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit_aer.primitives import Sampler
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


class MockSampler:
    """Mock sampler for testing without Qiskit/quantum access."""
    
    def sample(self, bqm, **kwargs):
        """Return a mock sample using greedy assignment."""
        import numpy as np
        
        variables = list(bqm.variables)
        n_vars = len(variables)
        
        # Parse variables to understand structure
        positions = {}
        for var in variables:
            parts = var.split("_")
            node_id = "_".join(parts[1:-1])
            pos = int(parts[-1])
            if pos not in positions:
                positions[pos] = []
            positions[pos].append((var, node_id))
        
        # Greedy assignment: one node per position
        sample = {var: 0 for var in variables}
        used_nodes = set()
        
        for pos in sorted(positions.keys()):
            for var, node_id in positions[pos]:
                if node_id not in used_nodes:
                    sample[var] = 1
                    used_nodes.add(node_id)
                    break
        
        energy = bqm.energy(sample)
        return SampleSet.from_samples([sample], vartype=bqm.vartype, energy=[energy])


class QAOASampler:
    """QAOA-based sampler using Qiskit."""
    
    def __init__(self, reps: int = 2, shots: int = 1024):
        """
        Initialize QAOA sampler.
        
        Args:
            reps: Number of QAOA layers (p parameter)
            shots: Number of measurement shots
        """
        self.reps = reps
        self.shots = shots
    
    def sample(self, bqm, **kwargs):
        """
        Solve QUBO using QAOA.
        
        Args:
            bqm: Binary Quadratic Model from dimod
            
        Returns:
            SampleSet with QAOA solution
        """
        # Convert BQM to Qiskit QuadraticProgram
        qp = QuadraticProgram()
        
        # Add binary variables
        for var in bqm.variables:
            qp.binary_var(var)
        
        # Build linear and quadratic terms
        linear = {}
        quadratic = {}
        
        for var, bias in bqm.linear.items():
            linear[var] = bias
        
        for (u, v), bias in bqm.quadratic.items():
            quadratic[(u, v)] = bias
        
        # Set objective (minimize)
        qp.minimize(constant=bqm.offset, linear=linear, quadratic=quadratic)
        
        # Create QAOA instance with Aer simulator
        sampler = Sampler()
        optimizer = COBYLA(maxiter=100)
        qaoa = QAOA(sampler=sampler, optimizer=optimizer, reps=self.reps)
        
        # Solve using MinimumEigenOptimizer
        algorithm = MinimumEigenOptimizer(qaoa)
        result = algorithm.solve(qp)
        
        # Convert result to dimod SampleSet format
        sample = {var: int(result.variables_dict.get(var, 0)) for var in bqm.variables}
        energy = bqm.energy(sample)
        
        return SampleSet.from_samples([sample], vartype=bqm.vartype, energy=[energy])


def quantum_solve(
    graph: CityGraph,
    params: QUBOParams | None = None,
    use_mock: bool = False
) -> SolverResponse:
    """
    Solve routing problem using QAOA quantum optimization.
    
    Args:
        graph: City graph to solve
        params: QUBO penalty parameters
        use_mock: Use mock sampler instead of real QAOA
        
    Returns:
        SolverResponse with route and metrics
    """
    start_time = time.time()
    
    if params is None:
        params = QUBOParams()
    
    # Build QUBO
    bqm = build_qubo(graph, params)
    
    # Select sampler
    settings = get_settings()
    
    if use_mock or not QISKIT_AVAILABLE or settings.qaoa_use_mock:
        sampler = MockSampler()
        solver_name = "mock"
    else:
        sampler = QAOASampler(reps=settings.qaoa_reps, shots=settings.qaoa_shots)
        solver_name = f"QAOA (reps={settings.qaoa_reps})"
    
    # Sample
    sampleset = sampler.sample(bqm, label="priority-routing")
    
    # Get best sample
    best = sampleset.first
    
    # Decode route
    node_ids = [n.id for n in graph.nodes]
    route = decode_route(best.sample, node_ids)
    
    # Validate
    feasible, priority_satisfied = validate_route(route, graph)
    
    # Compute metrics
    if feasible:
        total_distance, travel_time = compute_route_metrics(route, graph)
    else:
        total_distance = float('inf')
        travel_time = float('inf')
    
    solve_time_ms = (time.time() - start_time) * 1000
    
    return SolverResponse(
        route=route,
        total_distance=total_distance,
        travel_time=travel_time,
        feasible=feasible,
        priority_satisfied=priority_satisfied,
        solve_time_ms=solve_time_ms,
        energy=best.energy,
        solver_used=f"quantum ({solver_name})"
    )


def get_sampler_info() -> dict[str, Any]:
    """Get information about available QAOA samplers."""
    settings = get_settings()

    info = {
        "qiskit_available": QISKIT_AVAILABLE,
        "use_mock": settings.qaoa_use_mock if QISKIT_AVAILABLE else True,
        "qaoa_reps": settings.qaoa_reps,
        "qaoa_shots": settings.qaoa_shots,
    }

    if QISKIT_AVAILABLE:
        try:
            import qiskit
            info["qiskit_version"] = qiskit.__version__
        except Exception as e:
            info["error"] = str(e)

    return info


def check_solver_health() -> dict:
    """
    Check if QAOA solver is operational.

    Returns:
        dict with keys:
        - name: "qaoa_solver"
        - status: "healthy" | "degraded" | "unhealthy"
        - details: dict with diagnostic information
    """
    result = {
        "name": "qaoa_solver",
        "status": "healthy",
        "details": {}
    }

    # Check Qiskit availability
    result["details"]["qiskit_available"] = QISKIT_AVAILABLE

    if not QISKIT_AVAILABLE:
        result["status"] = "degraded"
        result["details"]["message"] = "Qiskit not installed, using mock solver"
        return result

    # Try to import critical Qiskit components
    try:
        from qiskit_aer.primitives import Sampler
        from qiskit_algorithms import QAOA
        result["details"]["qiskit_components"] = "ok"
    except ImportError as e:
        result["status"] = "degraded"
        result["details"]["qiskit_components"] = "missing"
        result["details"]["message"] = f"Qiskit component unavailable: {e}"
        return result

    # Quick smoke test: create sampler instance
    try:
        _ = Sampler()
        result["details"]["sampler_init"] = "ok"
    except Exception as e:
        result["status"] = "unhealthy"
        result["details"]["sampler_init"] = "failed"
        result["details"]["error"] = str(e)

    return result
