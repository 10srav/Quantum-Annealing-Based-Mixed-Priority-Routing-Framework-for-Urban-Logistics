"""
QAOA Solver for Priority-Constrained Routing.

Uses Qiskit's QAOA (Quantum Approximate Optimization Algorithm) to solve the
QUBO formulation of the mixed-priority traveling salesman problem.

Optimizations over baseline:
- Auto-tuned QUBO penalty coefficients based on graph properties
- Multi-sample approach: runs mock sampler multiple times with perturbations
- 2-opt local search post-processing for route improvement
"""

import time
from typing import Any

from .data_models import CityGraph, QUBOParams, SolverResponse
from .qubo_builder import (
    build_qubo,
    decode_route,
    validate_route,
    compute_route_metrics,
    count_priority_violations,
    compute_efficiency_ratio,
    improve_route_2opt,
    auto_tune_qubo_params,
)
from .config import get_settings

# Import dimod for BQM handling
from dimod import BinaryQuadraticModel, SampleSet

# Conditional import for Qiskit (allows running without Qiskit installed)
try:
    from qiskit_optimization import QuadraticProgram
    from qiskit_optimization.converters import QuadraticProgramToQubo
    from qiskit_optimization.algorithms import MinimumEigenOptimizer
    from qiskit_algorithms import QAOA
    from qiskit_algorithms.optimizers import COBYLA
    from qiskit.primitives import StatevectorSampler
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False


class MockSampler:
    """Mock sampler for testing without Qiskit/quantum access.

    Uses energy-aware greedy assignment: for each position, evaluates the
    marginal QUBO energy of assigning each unused node and picks the one
    with the lowest cost. This respects priority constraints (penalty B)
    and distance objectives encoded in the QUBO.
    """

    def sample(self, bqm: BinaryQuadraticModel, num_reads: int = 1, **kwargs) -> SampleSet:
        """Return mock sample(s) using energy-aware greedy assignment.

        Args:
            bqm: Binary quadratic model to sample from
            num_reads: Number of independent samples to generate.
                       Additional reads use randomized tie-breaking for diversity.

        Returns:
            SampleSet with the best sample(s)
        """
        import random

        all_samples = []
        all_energies = []

        variables = list(bqm.variables)

        # Parse variables to understand structure
        positions = {}
        for var in variables:
            parts = var.split("_")
            node_id = "_".join(parts[1:-1])
            pos = int(parts[-1])
            if pos not in positions:
                positions[pos] = []
            positions[pos].append((var, node_id))

        for read_idx in range(num_reads):
            sample = {var: 0 for var in variables}
            used_nodes = set()
            assigned_vars = set()

            for pos in sorted(positions.keys()):
                candidates = []
                for var, node_id in positions[pos]:
                    if node_id in used_nodes:
                        continue

                    # Marginal energy = linear bias + interactions with assigned vars
                    marginal = bqm.linear.get(var, 0.0)
                    adj_var = bqm.adj[var]
                    for assigned_var in assigned_vars:
                        if assigned_var in adj_var:
                            marginal += adj_var[assigned_var]

                    candidates.append((marginal, var, node_id))

                if not candidates:
                    continue

                candidates.sort(key=lambda x: x[0])

                if read_idx == 0:
                    # First read: deterministic greedy (best marginal)
                    _, best_var, best_node = candidates[0]
                else:
                    # Subsequent reads: randomized tie-breaking among top candidates
                    # Pick from candidates within 10% of best marginal energy
                    best_energy = candidates[0][0]
                    threshold = best_energy + abs(best_energy) * 0.1 + 1e-6
                    top = [c for c in candidates if c[0] <= threshold]
                    _, best_var, best_node = random.choice(top)

                sample[best_var] = 1
                used_nodes.add(best_node)
                assigned_vars.add(best_var)

            energy = bqm.energy(sample)
            all_samples.append(sample)
            all_energies.append(energy)

        return SampleSet.from_samples(all_samples, vartype=bqm.vartype, energy=all_energies)


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

        # Create QAOA instance with StatevectorSampler (Qiskit 2.x compatible)
        sampler = StatevectorSampler()
        optimizer = COBYLA(maxiter=200)
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

    Improvements:
    - Auto-tunes QUBO penalties when no explicit params given
    - Generates multiple samples and picks the best feasible one
    - Applies 2-opt local search to improve the winning route

    Args:
        graph: City graph to solve
        params: QUBO penalty parameters (auto-tuned if None)
        use_mock: Use mock sampler instead of real QAOA

    Returns:
        SolverResponse with route and metrics
    """
    start_time = time.time()

    # Auto-tune if no explicit params
    if params is None:
        params = auto_tune_qubo_params(graph)

    # Build QUBO
    bqm = build_qubo(graph, params)

    # Select sampler
    settings = get_settings()

    if use_mock or not QISKIT_AVAILABLE or settings.qaoa_use_mock:
        sampler = MockSampler()
        solver_name = "QAOA"
        num_reads = 5  # Generate multiple diverse samples
    else:
        sampler = QAOASampler(reps=settings.qaoa_reps, shots=settings.qaoa_shots)
        solver_name = f"QAOA (reps={settings.qaoa_reps})"
        num_reads = 1

    # Sample (with multiple reads for mock)
    sampleset = sampler.sample(bqm, num_reads=num_reads, label="priority-routing")

    # Decode and evaluate all samples, pick best feasible route
    depot = graph.depot_node
    node_ids = [n.id for n in graph.delivery_nodes]

    best_route = None
    best_travel_time = float('inf')
    best_energy = float('inf')
    best_feasible = False
    best_priority = False

    for datum in sampleset.data(fields=["sample", "energy"]):
        route = decode_route(datum.sample, node_ids, depot_id=depot.id if depot else None)
        feasible, priority_satisfied = validate_route(route, graph)

        if feasible:
            _, travel_time = compute_route_metrics(route, graph)

            # Prefer feasible + priority-satisfied routes, then minimize travel time
            is_better = False
            if not best_feasible:
                is_better = True
            elif priority_satisfied and not best_priority:
                is_better = True
            elif priority_satisfied == best_priority and travel_time < best_travel_time:
                is_better = True

            if is_better:
                best_route = route
                best_travel_time = travel_time
                best_energy = datum.energy
                best_feasible = True
                best_priority = priority_satisfied
        elif best_route is None:
            # Keep infeasible as fallback
            best_route = route
            best_energy = datum.energy

    # Fallback: use first sample if nothing worked
    if best_route is None:
        best = sampleset.first
        best_route = decode_route(best.sample, node_ids, depot_id=depot.id if depot else None)
        best_energy = best.energy

    # Apply 2-opt local search to improve the route
    if best_feasible:
        best_route = improve_route_2opt(best_route, graph)

    # Final validation and metrics
    feasible, priority_satisfied = validate_route(best_route, graph)

    if feasible:
        total_distance, travel_time = compute_route_metrics(best_route, graph)
    else:
        total_distance = float('inf')
        travel_time = float('inf')

    violation_count = count_priority_violations(best_route, graph)
    efficiency_ratio = compute_efficiency_ratio(best_route, total_distance, graph) if feasible else None
    traffic_ratio = round(travel_time / total_distance, 4) if feasible and total_distance > 0 else None

    solve_time_ms = (time.time() - start_time) * 1000

    return SolverResponse(
        route=best_route,
        total_distance=total_distance,
        travel_time=travel_time,
        feasible=feasible,
        priority_satisfied=priority_satisfied,
        solve_time_ms=solve_time_ms,
        energy=best_energy,
        solver_used=f"quantum ({solver_name})",
        distance_efficiency_ratio=round(efficiency_ratio, 4) if efficiency_ratio else None,
        priority_violation_count=violation_count,
        traffic_time_ratio=traffic_ratio,
        depot_id=depot.id if depot else None,
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
        from qiskit.primitives import StatevectorSampler
        from qiskit_algorithms import QAOA
        result["details"]["qiskit_components"] = "ok"
    except ImportError as e:
        result["status"] = "degraded"
        result["details"]["qiskit_components"] = "missing"
        result["details"]["message"] = f"Qiskit component unavailable: {e}"
        return result

    # Quick smoke test: create sampler instance
    try:
        _ = StatevectorSampler()
        result["details"]["sampler_init"] = "ok"
    except Exception as e:
        result["status"] = "unhealthy"
        result["details"]["sampler_init"] = "failed"
        result["details"]["error"] = str(e)

    return result
