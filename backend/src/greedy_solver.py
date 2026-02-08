"""
Greedy Solver for Routing (No Priority Awareness).

Implements a plain nearest-neighbor heuristic that only minimizes distance.
It does NOT consider node priority — serves as a baseline to show the
quantum solver's advantage in handling mixed-priority constraints.
"""

import time
import math

from .data_models import CityGraph, NodeType, SolverResponse
from .qubo_builder import count_priority_violations, compute_efficiency_ratio


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Compute Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def greedy_solve(graph: CityGraph) -> SolverResponse:
    """
    Solve routing problem using plain nearest-neighbor (no priority awareness).

    Algorithm:
    1. Start from the first node
    2. Always visit the nearest unvisited node regardless of priority type

    This serves as a baseline — it optimizes distance only, ignoring priority
    constraints entirely. The quantum solver should outperform this by
    satisfying priority ordering while also optimizing distance.

    Args:
        graph: City graph to solve

    Returns:
        SolverResponse with route and metrics
    """
    start_time = time.time()

    nodes = graph.nodes
    node_map = {n.id: n for n in nodes}

    route: list[str] = []
    total_distance = 0.0
    travel_time = 0.0

    def get_weighted_distance(from_id: str, to_id: str) -> tuple[float, float]:
        """Get base distance and traffic-weighted time between two nodes."""
        for edge in graph.edges:
            if (edge.from_node == from_id and edge.to_node == to_id) or \
               (edge.from_node == to_id and edge.to_node == from_id):
                base_dist = edge.distance
                multiplier = graph.traffic_multipliers.get(edge.traffic.value, 1.0)
                return base_dist, base_dist * multiplier

        # Fall back to Euclidean distance
        n1, n2 = node_map[from_id], node_map[to_id]
        dist = euclidean_distance(n1.x, n1.y, n2.x, n2.y)
        return dist, dist

    # Start from the depot (if present), otherwise the first node
    depot = graph.depot_node
    unvisited = list(nodes)
    if depot:
        # Remove depot from unvisited delivery candidates
        unvisited = [n for n in unvisited if n.id != depot.id]
        current = depot
    else:
        current = unvisited.pop(0)
    route.append(current.id)

    # Always pick the nearest unvisited node — no priority logic
    while unvisited:
        best_id = None
        best_time = float('inf')

        for candidate in unvisited:
            _, weighted_time = get_weighted_distance(current.id, candidate.id)
            if weighted_time < best_time:
                best_time = weighted_time
                best_id = candidate.id

        if best_id is None:
            break

        dist, weighted = get_weighted_distance(current.id, best_id)
        total_distance += dist
        travel_time += weighted
        route.append(best_id)
        current = node_map[best_id]
        unvisited = [n for n in unvisited if n.id != best_id]

    solve_time_ms = (time.time() - start_time) * 1000

    # Check if priority nodes ended up first (they usually won't)
    priority_ids = set(n.id for n in nodes if n.type == NodeType.PRIORITY)
    k = len(priority_ids)

    if k > 0:
        priority_positions = [i for i, node_id in enumerate(route) if node_id in priority_ids]
        priority_satisfied = max(priority_positions) < k if priority_positions else False
    else:
        priority_satisfied = True

    feasible = len(route) == len(nodes) and len(set(route)) == len(route)

    # Compute evaluation metrics
    rounded_distance = round(total_distance, 2)
    rounded_time = round(travel_time, 2)
    violation_count = count_priority_violations(route, graph)
    efficiency_ratio = compute_efficiency_ratio(route, rounded_distance, graph) if feasible else None
    traffic_ratio = round(rounded_time / rounded_distance, 4) if feasible and rounded_distance > 0 else None

    return SolverResponse(
        route=route,
        total_distance=rounded_distance,
        travel_time=rounded_time,
        feasible=feasible,
        priority_satisfied=priority_satisfied,
        solve_time_ms=round(solve_time_ms, 3),
        energy=None,
        solver_used="greedy",
        distance_efficiency_ratio=round(efficiency_ratio, 4) if efficiency_ratio else None,
        priority_violation_count=violation_count,
        traffic_time_ratio=traffic_ratio,
        depot_id=depot.id if depot else None,
    )
