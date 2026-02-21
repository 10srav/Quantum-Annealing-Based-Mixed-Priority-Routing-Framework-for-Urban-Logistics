"""
Greedy Solvers for Routing.

Provides two greedy strategies:
1. greedy_solve: Plain nearest-neighbor (no priority awareness) — baseline
2. greedy_priority_solve: Priority-aware nearest-neighbor — visits all priority
   nodes first, then normal nodes, each phase using nearest-neighbor

Both use O(1) edge lookup for performance.
"""

import time
import math

from .data_models import CityGraph, NodeType, SolverResponse
from .qubo_builder import (
    count_priority_violations,
    compute_efficiency_ratio,
    improve_route_2opt,
    _build_edge_lookup,
)


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Compute Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def _get_weighted_distance(
    from_id: str,
    to_id: str,
    edge_lookup: dict,
    node_map: dict,
) -> tuple[float, float]:
    """Get base distance and traffic-weighted time between two nodes using O(1) lookup."""
    key = (from_id, to_id)
    if key in edge_lookup:
        return edge_lookup[key]

    # Euclidean fallback
    n1, n2 = node_map.get(from_id), node_map.get(to_id)
    if n1 and n2:
        dist = euclidean_distance(n1.x, n1.y, n2.x, n2.y)
        return dist, dist
    return float('inf'), float('inf')


def _compute_route_cost(
    route: list[str],
    edge_lookup: dict,
    node_map: dict,
) -> tuple[float, float]:
    """Compute total distance and travel time for a route."""
    total_distance = 0.0
    travel_time = 0.0
    for i in range(len(route) - 1):
        dist, weighted = _get_weighted_distance(
            route[i], route[i + 1], edge_lookup, node_map
        )
        total_distance += dist
        travel_time += weighted
    return total_distance, travel_time


def greedy_solve(graph: CityGraph) -> SolverResponse:
    """
    Solve routing problem using plain nearest-neighbor (no priority awareness).

    Algorithm:
    1. Start from depot (if present), otherwise the first node
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
    edge_lookup = _build_edge_lookup(graph)

    route: list[str] = []
    total_distance = 0.0
    travel_time = 0.0

    # Start from the depot (if present), otherwise the first node
    depot = graph.depot_node
    unvisited = set(n.id for n in nodes)
    if depot:
        unvisited.discard(depot.id)
        current_id = depot.id
    else:
        current_id = nodes[0].id
        unvisited.discard(current_id)
    route.append(current_id)

    # Always pick the nearest unvisited node — no priority logic
    while unvisited:
        best_id = None
        best_time = float('inf')

        for cid in unvisited:
            _, weighted_time = _get_weighted_distance(current_id, cid, edge_lookup, node_map)
            if weighted_time < best_time:
                best_time = weighted_time
                best_id = cid

        if best_id is None:
            break

        dist, weighted = _get_weighted_distance(current_id, best_id, edge_lookup, node_map)
        total_distance += dist
        travel_time += weighted
        route.append(best_id)
        current_id = best_id
        unvisited.discard(best_id)

    solve_time_ms = (time.time() - start_time) * 1000

    # Check if priority nodes ended up first (they usually won't)
    priority_ids = set(n.id for n in nodes if n.type == NodeType.PRIORITY)
    k = len(priority_ids)

    # Priority check: skip depot when evaluating delivery positions
    delivery_route = route[1:] if depot and route and route[0] == depot.id else route
    if k > 0:
        priority_positions = [i for i, node_id in enumerate(delivery_route) if node_id in priority_ids]
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


def greedy_priority_solve(graph: CityGraph) -> SolverResponse:
    """
    Solve routing problem using priority-aware nearest-neighbor + 2-opt.

    Algorithm:
    1. Start from depot (if present)
    2. Visit all priority nodes first using nearest-neighbor among priorities
    3. Visit all normal nodes using nearest-neighbor among normals
    4. Apply 2-opt local search to improve route while preserving priority ordering

    This produces a better baseline than plain greedy by respecting priorities
    and then optimizing within each zone.

    Args:
        graph: City graph to solve

    Returns:
        SolverResponse with route and metrics
    """
    start_time = time.time()

    nodes = graph.nodes
    node_map = {n.id: n for n in nodes}
    edge_lookup = _build_edge_lookup(graph)

    depot = graph.depot_node
    priority_nodes = {n.id for n in nodes if n.type == NodeType.PRIORITY}
    normal_nodes = {n.id for n in nodes if n.type == NodeType.NORMAL}

    route: list[str] = []

    # Start from depot
    if depot:
        current_id = depot.id
        route.append(current_id)
    else:
        # Start from the nearest priority node to origin, or first node
        if priority_nodes:
            current_id = min(priority_nodes, key=lambda nid: node_map[nid].x ** 2 + node_map[nid].y ** 2)
        else:
            current_id = nodes[0].id
        route.append(current_id)

    # Phase 1: Visit all priority nodes using nearest-neighbor
    unvisited_priority = set(priority_nodes)
    if current_id in unvisited_priority:
        unvisited_priority.discard(current_id)

    while unvisited_priority:
        best_id = None
        best_time = float('inf')
        for cid in unvisited_priority:
            _, weighted = _get_weighted_distance(current_id, cid, edge_lookup, node_map)
            if weighted < best_time:
                best_time = weighted
                best_id = cid
        if best_id is None:
            break
        route.append(best_id)
        current_id = best_id
        unvisited_priority.discard(best_id)

    # Phase 2: Visit all normal nodes using nearest-neighbor
    unvisited_normal = set(normal_nodes)
    while unvisited_normal:
        best_id = None
        best_time = float('inf')
        for cid in unvisited_normal:
            _, weighted = _get_weighted_distance(current_id, cid, edge_lookup, node_map)
            if weighted < best_time:
                best_time = weighted
                best_id = cid
        if best_id is None:
            break
        route.append(best_id)
        current_id = best_id
        unvisited_normal.discard(best_id)

    # Phase 3: 2-opt improvement (preserves priority ordering)
    route = improve_route_2opt(route, graph)

    # Compute final metrics
    total_distance, travel_time = _compute_route_cost(route, edge_lookup, node_map)

    solve_time_ms = (time.time() - start_time) * 1000

    # Priority check
    k = len(priority_nodes)
    delivery_route = route[1:] if depot and route and route[0] == depot.id else route
    if k > 0:
        priority_positions = [i for i, nid in enumerate(delivery_route) if nid in priority_nodes]
        priority_satisfied = max(priority_positions) < k if priority_positions else False
    else:
        priority_satisfied = True

    feasible = len(route) == len(nodes) and len(set(route)) == len(route)
    violation_count = count_priority_violations(route, graph)
    rounded_distance = round(total_distance, 2)
    rounded_time = round(travel_time, 2)
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
        solver_used="greedy-priority",
        distance_efficiency_ratio=round(efficiency_ratio, 4) if efficiency_ratio else None,
        priority_violation_count=violation_count,
        traffic_time_ratio=traffic_ratio,
        depot_id=depot.id if depot else None,
    )
