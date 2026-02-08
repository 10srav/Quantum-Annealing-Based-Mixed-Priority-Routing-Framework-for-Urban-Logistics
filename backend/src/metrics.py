"""
Metrics computation for routing experiments.
"""

from .data_models import SolverResponse, ComparisonResponse


def compute_distance_reduction(greedy: SolverResponse, quantum: SolverResponse) -> float:
    """
    Compute percentage distance reduction of quantum vs greedy.
    
    DR = (D_greedy - D_quantum) / D_greedy * 100
    
    Returns positive value if quantum is better, negative if greedy is better.
    """
    if greedy.total_distance == 0:
        return 0.0
    
    return ((greedy.total_distance - quantum.total_distance) / greedy.total_distance) * 100


def compute_time_reduction(greedy: SolverResponse, quantum: SolverResponse) -> float:
    """
    Compute percentage travel time reduction of quantum vs greedy.
    """
    if greedy.travel_time == 0:
        return 0.0
    
    return ((greedy.travel_time - quantum.travel_time) / greedy.travel_time) * 100


def compare_solutions(
    greedy: SolverResponse,
    quantum: SolverResponse
) -> ComparisonResponse:
    """
    Compare greedy and quantum solutions.
    """
    # Build traffic time comparison
    traffic_time_comparison = None
    if quantum.traffic_time_ratio is not None or greedy.traffic_time_ratio is not None:
        traffic_time_comparison = {
            "quantum": quantum.traffic_time_ratio,
            "greedy": greedy.traffic_time_ratio,
        }

    return ComparisonResponse(
        greedy=greedy,
        quantum=quantum,
        distance_reduction_pct=round(compute_distance_reduction(greedy, quantum), 2),
        time_reduction_pct=round(compute_time_reduction(greedy, quantum), 2),
        traffic_time_comparison=traffic_time_comparison,
    )


def compute_experiment_stats(results: list[dict]) -> dict:
    """
    Compute aggregate statistics from multiple experiment runs.
    
    Args:
        results: List of experiment result dicts
        
    Returns:
        Dictionary with mean, std, min, max for each metric
    """
    import statistics
    
    if not results:
        return {}
    
    metrics = [
        "quantum_distance", "greedy_distance",
        "quantum_time", "greedy_time",
        "distance_reduction_pct", "time_reduction_pct",
        "quantum_solve_ms", "greedy_solve_ms"
    ]
    
    stats = {}
    for metric in metrics:
        values = [r.get(metric, 0) for r in results if metric in r]
        if values:
            stats[metric] = {
                "mean": round(statistics.mean(values), 2),
                "std": round(statistics.stdev(values) if len(values) > 1 else 0, 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2)
            }
    
    # Compute feasibility and priority satisfaction rates
    feasible_q = sum(1 for r in results if r.get("quantum_feasible", False))
    feasible_g = sum(1 for r in results if r.get("greedy_feasible", False))
    priority_q = sum(1 for r in results if r.get("quantum_priority_satisfied", False))
    priority_g = sum(1 for r in results if r.get("greedy_priority_satisfied", False))
    
    total = len(results)
    stats["quantum_feasibility_rate"] = round(feasible_q / total * 100, 1) if total > 0 else 0
    stats["greedy_feasibility_rate"] = round(feasible_g / total * 100, 1) if total > 0 else 0
    stats["quantum_priority_rate"] = round(priority_q / total * 100, 1) if total > 0 else 0
    stats["greedy_priority_rate"] = round(priority_g / total * 100, 1) if total > 0 else 0
    
    return stats
