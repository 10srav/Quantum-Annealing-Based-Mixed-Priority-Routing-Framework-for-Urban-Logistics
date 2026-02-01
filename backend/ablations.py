"""
Ablation Experiments for QUBO Constraint Analysis.

This module runs systematic ablation studies to understand
the impact of each constraint on solution quality.
"""

import csv
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from typing import Literal

from src.data_models import QUBOParams, CityGraph
from src.simulator import generate_random_city
from src.d_wave_solver import quantum_solve
from src.greedy_solver import greedy_solve


@dataclass
class AblationConfig:
    """Configuration for ablation experiment."""
    name: str
    description: str
    params: QUBOParams


# Define ablation configurations
ABLATION_CONFIGS = [
    AblationConfig(
        name="full_model",
        description="All constraints enabled (baseline)",
        params=QUBOParams(A=100, B=500, Bp=1000, C=1.0)
    ),
    AblationConfig(
        name="no_priority_ordering",
        description="Priority ordering constraint disabled (B=0)",
        params=QUBOParams(A=100, B=0, Bp=1000, C=1.0)
    ),
    AblationConfig(
        name="no_priority_coverage",
        description="Priority coverage constraint disabled (Bp=0)",
        params=QUBOParams(A=100, B=500, Bp=0, C=1.0)
    ),
    AblationConfig(
        name="no_priority_constraints",
        description="All priority constraints disabled (B=0, Bp=0)",
        params=QUBOParams(A=100, B=0, Bp=0, C=1.0)
    ),
    AblationConfig(
        name="weak_one_hot",
        description="Weaker one-hot constraint (A=50)",
        params=QUBOParams(A=50, B=500, Bp=1000, C=1.0)
    ),
    AblationConfig(
        name="strong_one_hot",
        description="Stronger one-hot constraint (A=200)",
        params=QUBOParams(A=200, B=500, Bp=1000, C=1.0)
    ),
    AblationConfig(
        name="weak_objective",
        description="Weaker distance objective (C=0.1)",
        params=QUBOParams(A=100, B=500, Bp=1000, C=0.1)
    ),
    AblationConfig(
        name="strong_objective",
        description="Stronger distance objective (C=5.0)",
        params=QUBOParams(A=100, B=500, Bp=1000, C=5.0)
    ),
    AblationConfig(
        name="high_all_constraints",
        description="All constraints at high values",
        params=QUBOParams(A=200, B=1000, Bp=2000, C=1.0)
    ),
    AblationConfig(
        name="balanced_config",
        description="Balanced constraint weights",
        params=QUBOParams(A=100, B=300, Bp=600, C=1.5)
    ),
]


@dataclass
class AblationResult:
    """Result from a single ablation configuration."""
    config: AblationConfig
    n_runs: int
    feasibility_rate: float
    priority_rate: float
    avg_distance: float
    avg_time: float
    avg_solve_ms: float
    greedy_wins: int
    quantum_wins: int


def run_ablation_experiment(
    config: AblationConfig,
    graphs: list[CityGraph],
    use_mock: bool = True
) -> AblationResult:
    """
    Run ablation experiment for a single configuration.
    
    Args:
        config: Ablation configuration to test
        graphs: Test graphs
        use_mock: Use mock sampler
        
    Returns:
        AblationResult with aggregated metrics
    """
    n = len(graphs)
    feasible = 0
    priority_sat = 0
    distances = []
    times = []
    solve_times = []
    greedy_wins = 0
    quantum_wins = 0
    
    for graph in graphs:
        try:
            qr = quantum_solve(graph, config.params, use_mock=use_mock)
            gr = greedy_solve(graph)
            
            if qr.feasible:
                feasible += 1
                distances.append(qr.total_distance)
                times.append(qr.travel_time)
                
                if qr.total_distance < gr.total_distance:
                    quantum_wins += 1
                else:
                    greedy_wins += 1
                    
            if qr.priority_satisfied:
                priority_sat += 1
                
            solve_times.append(qr.solve_time_ms)
            
        except Exception as e:
            print(f"Error in {config.name}: {e}")
    
    return AblationResult(
        config=config,
        n_runs=n,
        feasibility_rate=feasible / n if n > 0 else 0,
        priority_rate=priority_sat / n if n > 0 else 0,
        avg_distance=sum(distances) / len(distances) if distances else 0,
        avg_time=sum(times) / len(times) if times else 0,
        avg_solve_ms=sum(solve_times) / len(solve_times) if solve_times else 0,
        greedy_wins=greedy_wins,
        quantum_wins=quantum_wins
    )


def run_full_ablation_study(
    n_nodes: int = 10,
    n_graphs: int = 20,
    traffic_profile: Literal["low", "mixed", "high"] = "mixed",
    configs: list[AblationConfig] | None = None,
    output_dir: str = "results",
    use_mock: bool = True
) -> list[AblationResult]:
    """
    Run full ablation study across all configurations.
    
    Args:
        n_nodes: Nodes per graph
        n_graphs: Number of test graphs
        traffic_profile: Traffic distribution
        configs: Ablation configurations (defaults to ABLATION_CONFIGS)
        output_dir: Output directory
        use_mock: Use mock sampler
        
    Returns:
        List of AblationResult for each configuration
    """
    if configs is None:
        configs = ABLATION_CONFIGS
    
    # Generate test graphs
    print(f"Generating {n_graphs} test graphs with {n_nodes} nodes...")
    graphs = [
        generate_random_city(
            n_nodes=n_nodes,
            priority_ratio=0.3,
            traffic_profile=traffic_profile,
            seed=i * 77
        )
        for i in range(n_graphs)
    ]
    
    print(f"\nRunning {len(configs)} ablation configurations...")
    print("=" * 70)
    
    results = []
    for i, config in enumerate(configs):
        print(f"\n[{i+1}/{len(configs)}] {config.name}")
        print(f"   {config.description}")
        print(f"   A={config.params.A}, B={config.params.B}, Bp={config.params.Bp}, C={config.params.C}")
        
        result = run_ablation_experiment(config, graphs, use_mock)
        results.append(result)
        
        print(f"   → Feasibility: {result.feasibility_rate*100:.0f}%, Priority: {result.priority_rate*100:.0f}%")
        print(f"   → Quantum wins: {result.quantum_wins}, Greedy wins: {result.greedy_wins}")
    
    # Save results
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"{output_dir}/ablation_study_{timestamp}.csv"
    
    with open(output_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Configuration", "Description", "A", "B", "Bp", "C",
            "Feasibility%", "Priority%", "AvgDistance", "AvgTime",
            "AvgSolveMs", "QuantumWins", "GreedyWins"
        ])
        for r in results:
            writer.writerow([
                r.config.name,
                r.config.description,
                r.config.params.A,
                r.config.params.B,
                r.config.params.Bp,
                r.config.params.C,
                f"{r.feasibility_rate*100:.1f}",
                f"{r.priority_rate*100:.1f}",
                f"{r.avg_distance:.2f}",
                f"{r.avg_time:.2f}",
                f"{r.avg_solve_ms:.1f}",
                r.quantum_wins,
                r.greedy_wins
            ])
    
    print("\n" + "=" * 70)
    print(f"Results saved to: {output_file}")
    
    # Print summary
    print_ablation_summary(results)
    
    return results


def print_ablation_summary(results: list[AblationResult]):
    """Print ablation study summary."""
    print("\n" + "=" * 70)
    print("ABLATION STUDY SUMMARY")
    print("=" * 70)
    
    # Find best configurations
    best_feasibility = max(results, key=lambda r: r.feasibility_rate)
    best_wins = max(results, key=lambda r: r.quantum_wins)
    
    print(f"\n🏆 Highest Feasibility: {best_feasibility.config.name} ({best_feasibility.feasibility_rate*100:.0f}%)")
    print(f"🏆 Most Quantum Wins:   {best_wins.config.name} ({best_wins.quantum_wins} wins)")
    
    # Key findings
    print("\n📊 KEY FINDINGS:")
    
    # Compare with vs without priority ordering
    full = next((r for r in results if r.config.name == "full_model"), None)
    no_order = next((r for r in results if r.config.name == "no_priority_ordering"), None)
    if full and no_order:
        diff = full.priority_rate - no_order.priority_rate
        print(f"   → Priority ordering (B) increases priority satisfaction by {diff*100:.0f}%")
    
    # Compare constraint strengths
    weak = next((r for r in results if r.config.name == "weak_one_hot"), None)
    strong = next((r for r in results if r.config.name == "strong_one_hot"), None)
    if weak and strong:
        diff = strong.feasibility_rate - weak.feasibility_rate
        print(f"   → Stronger one-hot (A) changes feasibility by {diff*100:+.0f}%")
    
    print("=" * 70)


def generate_ablation_report(results: list[AblationResult]) -> str:
    """Generate markdown report from ablation results."""
    report = "# Ablation Study Report\n\n"
    report += f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    report += f"**Configurations Tested:** {len(results)}\n\n"
    
    report += "## Results Table\n\n"
    report += "| Configuration | A | B | Bp | C | Feasibility | Priority | Q Wins |\n"
    report += "|---------------|---|---|----|----|-------------|----------|--------|\n"
    
    for r in results:
        report += f"| {r.config.name} | {r.config.params.A} | {r.config.params.B} | "
        report += f"{r.config.params.Bp} | {r.config.params.C} | "
        report += f"{r.feasibility_rate*100:.0f}% | {r.priority_rate*100:.0f}% | "
        report += f"{r.quantum_wins} |\n"
    
    report += "\n## Key Insights\n\n"
    
    best = max(results, key=lambda r: r.feasibility_rate + r.priority_rate + r.quantum_wins/10)
    report += f"**Best Overall Configuration:** `{best.config.name}`\n"
    report += f"- Parameters: A={best.config.params.A}, B={best.config.params.B}, "
    report += f"Bp={best.config.params.Bp}, C={best.config.params.C}\n"
    report += f"- Feasibility: {best.feasibility_rate*100:.0f}%\n"
    report += f"- Priority Satisfaction: {best.priority_rate*100:.0f}%\n"
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run QUBO ablation study")
    parser.add_argument("--nodes", type=int, default=10, help="Nodes per graph")
    parser.add_argument("--graphs", type=int, default=20, help="Number of test graphs")
    parser.add_argument("--traffic", choices=["low", "mixed", "high"], default="mixed")
    parser.add_argument("--output", type=str, default="results")
    
    args = parser.parse_args()
    
    results = run_full_ablation_study(
        n_nodes=args.nodes,
        n_graphs=args.graphs,
        traffic_profile=args.traffic,
        output_dir=args.output
    )
    
    # Generate and save report
    report = generate_ablation_report(results)
    report_file = f"{args.output}/ablation_report.md"
    with open(report_file, "w") as f:
        f.write(report)
    print(f"\nReport saved to: {report_file}")
