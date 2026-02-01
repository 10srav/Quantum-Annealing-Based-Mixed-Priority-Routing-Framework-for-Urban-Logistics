"""
Advanced Metrics Computation Module.

Provides comprehensive metrics for evaluating and comparing
routing solutions from quantum and greedy solvers.
"""

from dataclasses import dataclass
from typing import Optional
import statistics

from src.data_models import SolverResponse, CityGraph


@dataclass
class RouteMetrics:
    """Comprehensive metrics for a single route."""
    total_distance: float
    travel_time: float
    feasible: bool
    priority_satisfied: bool
    solve_time_ms: float
    
    # Derived metrics
    avg_leg_distance: float
    max_leg_distance: float
    min_leg_distance: float
    efficiency_ratio: float  # distance / euclidean_distance
    priority_zone_distance: float
    normal_zone_distance: float


@dataclass
class ComparisonMetrics:
    """Metrics comparing two solutions."""
    distance_reduction_pct: float
    time_reduction_pct: float
    solve_time_ratio: float  # quantum_time / greedy_time
    quantum_better: bool
    quantum_valid: bool


@dataclass
class ExperimentMetrics:
    """Aggregated metrics from multiple experiments."""
    n_experiments: int
    feasibility_rate: float
    priority_satisfaction_rate: float
    
    # Distance metrics
    avg_distance_reduction: float
    std_distance_reduction: float
    min_distance_reduction: float
    max_distance_reduction: float
    
    # Time metrics
    avg_time_reduction: float
    std_time_reduction: float
    
    # Solve time
    avg_quantum_solve_ms: float
    avg_greedy_solve_ms: float


def compute_route_metrics(
    result: SolverResponse,
    graph: CityGraph
) -> RouteMetrics:
    """
    Compute comprehensive metrics for a route.
    
    Args:
        result: Solver result with route
        graph: City graph
        
    Returns:
        RouteMetrics with all computed values
    """
    route = result.route
    
    if len(route) < 2:
        return RouteMetrics(
            total_distance=0,
            travel_time=0,
            feasible=False,
            priority_satisfied=False,
            solve_time_ms=result.solve_time_ms,
            avg_leg_distance=0,
            max_leg_distance=0,
            min_leg_distance=0,
            efficiency_ratio=0,
            priority_zone_distance=0,
            normal_zone_distance=0
        )
    
    # Build edge lookup
    edge_lookup = {}
    for edge in graph.edges:
        edge_lookup[(edge.from_node, edge.to_node)] = edge
        edge_lookup[(edge.to_node, edge.from_node)] = edge
    
    # Compute leg distances
    leg_distances = []
    for i in range(len(route) - 1):
        key = (route[i], route[i + 1])
        if key in edge_lookup:
            leg_distances.append(edge_lookup[key].distance)
        else:
            leg_distances.append(float('inf'))
    
    # Find priority zone boundary
    priority_ids = {n.id for n in graph.nodes if n.type.value == "priority"}
    k = len(priority_ids)
    
    priority_zone_dist = sum(leg_distances[:k-1]) if k > 1 else 0
    normal_zone_dist = sum(leg_distances[k:]) if k < len(route) else 0
    
    # Compute efficiency (actual / direct euclidean)
    node_lookup = {n.id: n for n in graph.nodes}
    if route[0] in node_lookup and route[-1] in node_lookup:
        start = node_lookup[route[0]]
        end = node_lookup[route[-1]]
        euclidean = ((end.x - start.x)**2 + (end.y - start.y)**2)**0.5
        efficiency = result.total_distance / euclidean if euclidean > 0 else 1
    else:
        efficiency = 1
    
    valid_legs = [d for d in leg_distances if d < float('inf')]
    
    return RouteMetrics(
        total_distance=result.total_distance,
        travel_time=result.travel_time,
        feasible=result.feasible,
        priority_satisfied=result.priority_satisfied,
        solve_time_ms=result.solve_time_ms,
        avg_leg_distance=statistics.mean(valid_legs) if valid_legs else 0,
        max_leg_distance=max(valid_legs) if valid_legs else 0,
        min_leg_distance=min(valid_legs) if valid_legs else 0,
        efficiency_ratio=efficiency,
        priority_zone_distance=priority_zone_dist,
        normal_zone_distance=normal_zone_dist
    )


def compare_solutions(
    quantum_result: SolverResponse,
    greedy_result: SolverResponse
) -> ComparisonMetrics:
    """
    Compare quantum and greedy solutions.
    
    Args:
        quantum_result: Result from quantum solver
        greedy_result: Result from greedy solver
        
    Returns:
        ComparisonMetrics with reduction percentages
    """
    # Distance reduction: positive means quantum is better
    if greedy_result.total_distance > 0:
        dist_reduction = (
            (greedy_result.total_distance - quantum_result.total_distance)
            / greedy_result.total_distance * 100
        )
    else:
        dist_reduction = 0
    
    # Time reduction
    if greedy_result.travel_time > 0:
        time_reduction = (
            (greedy_result.travel_time - quantum_result.travel_time)
            / greedy_result.travel_time * 100
        )
    else:
        time_reduction = 0
    
    # Solve time ratio
    if greedy_result.solve_time_ms > 0:
        solve_ratio = quantum_result.solve_time_ms / greedy_result.solve_time_ms
    else:
        solve_ratio = float('inf')
    
    return ComparisonMetrics(
        distance_reduction_pct=dist_reduction,
        time_reduction_pct=time_reduction,
        solve_time_ratio=solve_ratio,
        quantum_better=dist_reduction > 0 and quantum_result.feasible,
        quantum_valid=quantum_result.feasible and quantum_result.priority_satisfied
    )


def aggregate_experiment_results(
    quantum_results: list[SolverResponse],
    greedy_results: list[SolverResponse]
) -> ExperimentMetrics:
    """
    Aggregate metrics from multiple experiment runs.
    
    Args:
        quantum_results: List of quantum solver results
        greedy_results: List of greedy solver results
        
    Returns:
        ExperimentMetrics with aggregated statistics
    """
    n = len(quantum_results)
    
    if n == 0:
        return ExperimentMetrics(
            n_experiments=0,
            feasibility_rate=0,
            priority_satisfaction_rate=0,
            avg_distance_reduction=0,
            std_distance_reduction=0,
            min_distance_reduction=0,
            max_distance_reduction=0,
            avg_time_reduction=0,
            std_time_reduction=0,
            avg_quantum_solve_ms=0,
            avg_greedy_solve_ms=0
        )
    
    # Count feasible and priority-satisfied
    feasible = sum(1 for r in quantum_results if r.feasible)
    priority_sat = sum(1 for r in quantum_results if r.priority_satisfied)
    
    # Compute reductions for feasible solutions
    distance_reductions = []
    time_reductions = []
    
    for qr, gr in zip(quantum_results, greedy_results):
        if qr.feasible and gr.total_distance > 0:
            dr = (gr.total_distance - qr.total_distance) / gr.total_distance * 100
            distance_reductions.append(dr)
        if qr.feasible and gr.travel_time > 0:
            tr = (gr.travel_time - qr.travel_time) / gr.travel_time * 100
            time_reductions.append(tr)
    
    # Solve times
    quantum_times = [r.solve_time_ms for r in quantum_results]
    greedy_times = [r.solve_time_ms for r in greedy_results]
    
    return ExperimentMetrics(
        n_experiments=n,
        feasibility_rate=feasible / n,
        priority_satisfaction_rate=priority_sat / n,
        avg_distance_reduction=statistics.mean(distance_reductions) if distance_reductions else 0,
        std_distance_reduction=statistics.stdev(distance_reductions) if len(distance_reductions) > 1 else 0,
        min_distance_reduction=min(distance_reductions) if distance_reductions else 0,
        max_distance_reduction=max(distance_reductions) if distance_reductions else 0,
        avg_time_reduction=statistics.mean(time_reductions) if time_reductions else 0,
        std_time_reduction=statistics.stdev(time_reductions) if len(time_reductions) > 1 else 0,
        avg_quantum_solve_ms=statistics.mean(quantum_times) if quantum_times else 0,
        avg_greedy_solve_ms=statistics.mean(greedy_times) if greedy_times else 0
    )


def format_metrics_report(metrics: ExperimentMetrics) -> str:
    """
    Format experiment metrics as a readable report.
    
    Args:
        metrics: Aggregated experiment metrics
        
    Returns:
        Formatted string report
    """
    return f"""
╔══════════════════════════════════════════════════════════╗
║                  EXPERIMENT RESULTS                       ║
╠══════════════════════════════════════════════════════════╣
║  Experiments Run:       {metrics.n_experiments:>6}                           ║
║  Feasibility Rate:      {metrics.feasibility_rate*100:>6.1f}%                          ║
║  Priority Satisfaction: {metrics.priority_satisfaction_rate*100:>6.1f}%                          ║
╠══════════════════════════════════════════════════════════╣
║                  DISTANCE REDUCTION                       ║
║  Average:    {metrics.avg_distance_reduction:>+7.2f}% ± {metrics.std_distance_reduction:.2f}%                        ║
║  Range:      [{metrics.min_distance_reduction:>+7.2f}%, {metrics.max_distance_reduction:>+7.2f}%]                     ║
╠══════════════════════════════════════════════════════════╣
║                   TIME REDUCTION                          ║
║  Average:    {metrics.avg_time_reduction:>+7.2f}% ± {metrics.std_time_reduction:.2f}%                        ║
╠══════════════════════════════════════════════════════════╣
║                    SOLVE TIME                             ║
║  Quantum:    {metrics.avg_quantum_solve_ms:>8.1f} ms                              ║
║  Greedy:     {metrics.avg_greedy_solve_ms:>8.1f} ms                              ║
╚══════════════════════════════════════════════════════════╝
"""
