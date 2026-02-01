"""
Hyperparameter Tuning Pipeline for QUBO Parameters.

This module provides automated tuning of QUBO penalty coefficients
(A, B, Bp, C) to optimize solver performance.
"""

import itertools
import csv
from datetime import datetime
from pathlib import Path
from typing import Literal
from dataclasses import dataclass, field

from src.data_models import QUBOParams, CityGraph
from src.simulator import generate_random_city
from src.qaoa_solver import quantum_solve
from src.greedy_solver import greedy_solve
from src.metrics import compute_distance_reduction, compute_time_reduction


@dataclass
class TuningResult:
    """Result from a single tuning run."""
    params: QUBOParams
    feasibility_rate: float
    priority_rate: float
    avg_distance_reduction: float
    avg_time_reduction: float
    avg_solve_time_ms: float
    n_runs: int
    score: float = field(init=False)
    
    def __post_init__(self):
        """Compute overall score (higher is better)."""
        # Score: prioritize feasibility, then quality
        self.score = (
            self.feasibility_rate * 0.4 +
            self.priority_rate * 0.3 +
            min(self.avg_distance_reduction / 20, 1.0) * 0.2 +  # Cap at 20%
            min(self.avg_time_reduction / 20, 1.0) * 0.1
        ) * 100


def generate_param_grid(
    A_values: list[float] = [50, 100, 200],
    B_values: list[float] = [200, 500, 1000],
    Bp_values: list[float] = [500, 1000, 2000],
    C_values: list[float] = [0.5, 1.0, 2.0]
) -> list[QUBOParams]:
    """
    Generate grid of QUBO parameter combinations.
    
    Args:
        A_values: One-hot penalty values to try
        B_values: Priority ordering penalty values
        Bp_values: Priority coverage penalty values
        C_values: Objective weight values
        
    Returns:
        List of QUBOParams configurations
    """
    params_list = []
    for A, B, Bp, C in itertools.product(A_values, B_values, Bp_values, C_values):
        params_list.append(QUBOParams(A=A, B=B, Bp=Bp, C=C))
    return params_list


def evaluate_params(
    params: QUBOParams,
    graphs: list[CityGraph],
    use_mock: bool = True
) -> TuningResult:
    """
    Evaluate a parameter configuration across multiple graphs.
    
    Args:
        params: QUBO parameters to evaluate
        graphs: List of test graphs
        use_mock: Use mock sampler
        
    Returns:
        TuningResult with aggregated metrics
    """
    feasible_count = 0
    priority_count = 0
    distance_reductions = []
    time_reductions = []
    solve_times = []
    
    for graph in graphs:
        try:
            # Run quantum solver
            quantum_result = quantum_solve(graph, params, use_mock=use_mock)
            
            if quantum_result.feasible:
                feasible_count += 1
            if quantum_result.priority_satisfied:
                priority_count += 1
            
            solve_times.append(quantum_result.solve_time_ms)
            
            # Compare with greedy
            greedy_result = greedy_solve(graph)
            dr = compute_distance_reduction(greedy_result, quantum_result)
            tr = compute_time_reduction(greedy_result, quantum_result)
            
            if quantum_result.feasible:
                distance_reductions.append(dr)
                time_reductions.append(tr)
                
        except Exception as e:
            print(f"Error with params {params}: {e}")
    
    n = len(graphs)
    return TuningResult(
        params=params,
        feasibility_rate=feasible_count / n if n > 0 else 0,
        priority_rate=priority_count / n if n > 0 else 0,
        avg_distance_reduction=sum(distance_reductions) / len(distance_reductions) if distance_reductions else 0,
        avg_time_reduction=sum(time_reductions) / len(time_reductions) if time_reductions else 0,
        avg_solve_time_ms=sum(solve_times) / len(solve_times) if solve_times else 0,
        n_runs=n
    )


def run_grid_search(
    n_nodes: int = 10,
    n_graphs: int = 10,
    traffic_profile: Literal["low", "mixed", "high"] = "mixed",
    A_values: list[float] = [50, 100, 200],
    B_values: list[float] = [200, 500, 1000],
    Bp_values: list[float] = [500, 1000, 2000],
    C_values: list[float] = [0.5, 1.0, 2.0],
    output_dir: str = "results",
    use_mock: bool = True
) -> list[TuningResult]:
    """
    Run grid search over QUBO parameters.
    
    Args:
        n_nodes: Number of nodes per graph
        n_graphs: Number of test graphs to generate
        traffic_profile: Traffic distribution
        A_values, B_values, Bp_values, C_values: Parameter ranges
        output_dir: Directory for results
        use_mock: Use mock sampler
        
    Returns:
        List of TuningResult sorted by score (best first)
    """
    # Generate test graphs
    print(f"Generating {n_graphs} test graphs with {n_nodes} nodes...")
    graphs = [
        generate_random_city(
            n_nodes=n_nodes,
            priority_ratio=0.3,
            traffic_profile=traffic_profile,
            seed=i * 42
        )
        for i in range(n_graphs)
    ]
    
    # Generate parameter grid
    param_grid = generate_param_grid(A_values, B_values, Bp_values, C_values)
    print(f"Testing {len(param_grid)} parameter combinations...")
    
    results = []
    for i, params in enumerate(param_grid):
        print(f"[{i+1}/{len(param_grid)}] A={params.A}, B={params.B}, Bp={params.Bp}, C={params.C}")
        result = evaluate_params(params, graphs, use_mock)
        results.append(result)
        print(f"  → Score: {result.score:.1f}, Feasibility: {result.feasibility_rate*100:.0f}%")
    
    # Sort by score (best first)
    results.sort(key=lambda r: r.score, reverse=True)
    
    # Save results
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/tuning_results_{timestamp}.csv"
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Rank", "A", "B", "Bp", "C", "Score",
            "Feasibility%", "Priority%", "AvgDistRed%", "AvgTimeRed%", "AvgSolveMs"
        ])
        for i, r in enumerate(results):
            writer.writerow([
                i + 1,
                r.params.A, r.params.B, r.params.Bp, r.params.C,
                f"{r.score:.1f}",
                f"{r.feasibility_rate*100:.0f}",
                f"{r.priority_rate*100:.0f}",
                f"{r.avg_distance_reduction:.1f}",
                f"{r.avg_time_reduction:.1f}",
                f"{r.avg_solve_time_ms:.0f}"
            ])
    
    print(f"\nResults saved to: {output_file}")
    print_summary(results)
    
    return results


def print_summary(results: list[TuningResult], top_n: int = 5):
    """Print summary of top parameter configurations."""
    print("\n" + "=" * 60)
    print(f"TOP {top_n} PARAMETER CONFIGURATIONS")
    print("=" * 60)
    
    for i, r in enumerate(results[:top_n]):
        print(f"\n#{i+1} - Score: {r.score:.1f}")
        print(f"   Params: A={r.params.A}, B={r.params.B}, Bp={r.params.Bp}, C={r.params.C}")
        print(f"   Feasibility: {r.feasibility_rate*100:.0f}% | Priority: {r.priority_rate*100:.0f}%")
        print(f"   Distance Reduction: {r.avg_distance_reduction:.1f}%")
    
    # Best params recommendation
    best = results[0]
    print("\n" + "=" * 60)
    print("RECOMMENDED PARAMETERS:")
    print(f"  A = {best.params.A}")
    print(f"  B = {best.params.B}")
    print(f"  Bp = {best.params.Bp}")
    print(f"  C = {best.params.C}")
    print("=" * 60)


def run_ablation_study(
    base_params: QUBOParams | None = None,
    n_nodes: int = 10,
    n_graphs: int = 10,
    output_dir: str = "results",
    use_mock: bool = True
) -> dict:
    """
    Run ablation study to understand impact of each constraint.
    
    Tests:
    1. Full model (all constraints)
    2. Without priority ordering (B=0)
    3. Without priority coverage (Bp=0)
    4. With minimal objective weight (C=0.1)
    
    Returns:
        Dictionary with ablation results
    """
    if base_params is None:
        base_params = QUBOParams(A=100, B=500, Bp=1000, C=1.0)
    
    # Define ablation configurations
    ablations = {
        "full_model": base_params,
        "no_priority_ordering": QUBOParams(A=base_params.A, B=0, Bp=base_params.Bp, C=base_params.C),
        "no_priority_coverage": QUBOParams(A=base_params.A, B=base_params.B, Bp=0, C=base_params.C),
        "minimal_objective": QUBOParams(A=base_params.A, B=base_params.B, Bp=base_params.Bp, C=0.1),
        "high_constraints": QUBOParams(A=200, B=1000, Bp=2000, C=0.5),
    }
    
    # Generate test graphs
    print(f"Running ablation study on {n_graphs} graphs with {n_nodes} nodes...")
    graphs = [
        generate_random_city(n_nodes=n_nodes, priority_ratio=0.3, seed=i * 123)
        for i in range(n_graphs)
    ]
    
    results = {}
    for name, params in ablations.items():
        print(f"\nEvaluating: {name}")
        result = evaluate_params(params, graphs, use_mock)
        results[name] = result
        print(f"  Score: {result.score:.1f}, Feasibility: {result.feasibility_rate*100:.0f}%")
    
    # Save results
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/ablation_results_{timestamp}.csv"
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Configuration", "A", "B", "Bp", "C", "Score", "Feasibility%", "Priority%"])
        for name, r in results.items():
            writer.writerow([
                name,
                r.params.A, r.params.B, r.params.Bp, r.params.C,
                f"{r.score:.1f}",
                f"{r.feasibility_rate*100:.0f}",
                f"{r.priority_rate*100:.0f}"
            ])
    
    print(f"\nAblation results saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="QUBO parameter tuning")
    parser.add_argument("--mode", choices=["grid", "ablation"], default="grid",
                        help="Tuning mode: grid search or ablation study")
    parser.add_argument("--nodes", type=int, default=10, help="Nodes per graph")
    parser.add_argument("--graphs", type=int, default=10, help="Number of test graphs")
    parser.add_argument("--output", type=str, default="results", help="Output directory")
    
    args = parser.parse_args()
    
    if args.mode == "grid":
        run_grid_search(
            n_nodes=args.nodes,
            n_graphs=args.graphs,
            output_dir=args.output
        )
    else:
        run_ablation_study(
            n_nodes=args.nodes,
            n_graphs=args.graphs,
            output_dir=args.output
        )
