"""
Experiment Harness for Quantum vs Greedy Comparison.

Runs systematic experiments across different graph sizes and traffic profiles,
logging results to CSV for analysis.
"""

import csv
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Literal

from src.data_models import QUBOParams
from src.simulator import generate_random_city
from src.greedy_solver import greedy_solve
from src.qaoa_solver import quantum_solve
from src.metrics import compute_distance_reduction, compute_time_reduction


def run_experiment(
    n_nodes: int,
    priority_ratio: float,
    traffic_profile: Literal["low", "mixed", "high"],
    seed: int,
    params: QUBOParams | None = None,
    use_mock: bool = True
) -> dict:
    """
    Run a single experiment comparing quantum and greedy solvers.
    
    Args:
        n_nodes: Number of nodes in graph
        priority_ratio: Fraction of priority nodes
        traffic_profile: Traffic distribution
        seed: Random seed for reproducibility
        params: QUBO parameters
        use_mock: Use mock quantum sampler
        
    Returns:
        Dictionary with experiment results
    """
    # Generate city
    graph = generate_random_city(
        n_nodes=n_nodes,
        priority_ratio=priority_ratio,
        traffic_profile=traffic_profile,
        seed=seed
    )
    
    # Count node types
    n_priority = len([n for n in graph.nodes if n.type.value == "priority"])
    n_normal = n_nodes - n_priority
    
    # Run greedy solver
    greedy_result = greedy_solve(graph)
    
    # Run quantum solver
    quantum_result = quantum_solve(graph, params, use_mock=use_mock)
    
    # Compute metrics
    distance_reduction = compute_distance_reduction(greedy_result, quantum_result)
    time_reduction = compute_time_reduction(greedy_result, quantum_result)
    
    return {
        "timestamp": datetime.now().isoformat(),
        "n_nodes": n_nodes,
        "n_priority": n_priority,
        "n_normal": n_normal,
        "priority_ratio": priority_ratio,
        "traffic_profile": traffic_profile,
        "seed": seed,
        
        # Greedy results
        "greedy_distance": greedy_result.total_distance,
        "greedy_time": greedy_result.travel_time,
        "greedy_solve_ms": greedy_result.solve_time_ms,
        "greedy_feasible": greedy_result.feasible,
        "greedy_priority_satisfied": greedy_result.priority_satisfied,
        
        # Quantum results
        "quantum_distance": quantum_result.total_distance,
        "quantum_time": quantum_result.travel_time,
        "quantum_solve_ms": quantum_result.solve_time_ms,
        "quantum_feasible": quantum_result.feasible,
        "quantum_priority_satisfied": quantum_result.priority_satisfied,
        "quantum_energy": quantum_result.energy,
        
        # Comparison metrics
        "distance_reduction_pct": distance_reduction,
        "time_reduction_pct": time_reduction,
    }


def run_experiment_suite(
    n_values: list[int] = [8, 10, 12, 15],
    traffic_profiles: list[str] = ["low", "mixed", "high"],
    runs_per_config: int = 5,
    output_dir: str = "results",
    use_mock: bool = True,
    params: QUBOParams | None = None
) -> str:
    """
    Run a full suite of experiments and save results to CSV.
    
    Args:
        n_values: List of node counts to test
        traffic_profiles: Traffic profile configurations
        runs_per_config: Number of runs per configuration
        output_dir: Directory to save results
        use_mock: Use mock quantum sampler
        params: QUBO parameters
        
    Returns:
        Path to output CSV file
    """
    # Ensure output directory exists
    Path(output_dir).mkdir(exist_ok=True)
    
    # Create output file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = os.path.join(output_dir, f"experiment_results_{timestamp}.csv")
    
    results = []
    total_experiments = len(n_values) * len(traffic_profiles) * runs_per_config
    
    print(f"Running {total_experiments} experiments...")
    print(f"Output: {output_file}")
    print("-" * 50)
    
    experiment_num = 0
    for n in n_values:
        for traffic in traffic_profiles:
            for run in range(runs_per_config):
                experiment_num += 1
                seed = hash((n, traffic, run)) % (2**31)
                
                print(f"[{experiment_num}/{total_experiments}] n={n}, traffic={traffic}, run={run+1}")
                
                try:
                    result = run_experiment(
                        n_nodes=n,
                        priority_ratio=0.3,
                        traffic_profile=traffic,
                        seed=seed,
                        params=params,
                        use_mock=use_mock
                    )
                    results.append(result)
                    
                    print(f"  → Distance reduction: {result['distance_reduction_pct']:.1f}%")
                    print(f"  → Quantum feasible: {result['quantum_feasible']}")
                    
                except Exception as e:
                    print(f"  → ERROR: {e}")
    
    # Write results to CSV
    if results:
        with open(output_file, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    print("-" * 50)
    print(f"Completed {len(results)} experiments")
    print(f"Results saved to: {output_file}")
    
    # Print summary statistics
    if results:
        print_summary(results)
    
    return output_file


def print_summary(results: list[dict]):
    """Print summary statistics from experiment results."""
    import statistics
    
    print("\n📊 SUMMARY STATISTICS")
    print("=" * 50)
    
    # Group by n_nodes
    by_n = {}
    for r in results:
        n = r["n_nodes"]
        if n not in by_n:
            by_n[n] = []
        by_n[n].append(r)
    
    print(f"\n{'Nodes':<8} {'Avg DR%':<10} {'Q Feasible':<12} {'Q Priority':<12}")
    print("-" * 42)
    
    for n in sorted(by_n.keys()):
        group = by_n[n]
        dr_values = [r["distance_reduction_pct"] for r in group]
        feasible_rate = sum(1 for r in group if r["quantum_feasible"]) / len(group) * 100
        priority_rate = sum(1 for r in group if r["quantum_priority_satisfied"]) / len(group) * 100
        
        avg_dr = statistics.mean(dr_values)
        print(f"{n:<8} {avg_dr:>8.1f}%  {feasible_rate:>10.0f}%  {priority_rate:>10.0f}%")
    
    # Overall stats
    print("\n" + "=" * 50)
    all_dr = [r["distance_reduction_pct"] for r in results]
    all_feasible = sum(1 for r in results if r["quantum_feasible"]) / len(results) * 100
    all_priority = sum(1 for r in results if r["quantum_priority_satisfied"]) / len(results) * 100
    
    print(f"Overall Distance Reduction: {statistics.mean(all_dr):.1f}% ± {statistics.stdev(all_dr):.1f}%")
    print(f"Overall Feasibility Rate:   {all_feasible:.1f}%")
    print(f"Overall Priority Rate:      {all_priority:.1f}%")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run quantum routing experiments")
    parser.add_argument("--nodes", type=int, nargs="+", default=[8, 10, 12],
                        help="Node counts to test")
    parser.add_argument("--traffic", type=str, nargs="+", default=["low", "mixed", "high"],
                        help="Traffic profiles to test")
    parser.add_argument("--runs", type=int, default=5,
                        help="Runs per configuration")
    parser.add_argument("--output", type=str, default="results",
                        help="Output directory")
    parser.add_argument("--real-quantum", action="store_true",
                        help="Use real D-Wave quantum hardware")
    
    args = parser.parse_args()
    
    run_experiment_suite(
        n_values=args.nodes,
        traffic_profiles=args.traffic,
        runs_per_config=args.runs,
        output_dir=args.output,
        use_mock=not args.real_quantum
    )
