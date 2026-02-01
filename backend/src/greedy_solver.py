"""
Greedy Solver for Priority-Constrained Routing.

Implements a nearest-neighbor heuristic that respects priority constraints:
1. First, visit all priority nodes using nearest-neighbor
2. Then, visit remaining normal nodes using nearest-neighbor
"""

import time
import math

from .data_models import CityGraph, NodeType, SolverResponse


def euclidean_distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """Compute Euclidean distance between two points."""
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def greedy_solve(graph: CityGraph) -> SolverResponse:
    """
    Solve routing problem using greedy nearest-neighbor with priority constraint.
    
    Algorithm:
    1. Start from the first priority node (or first node if no priorities)
    2. Visit all priority nodes first, each time choosing the nearest unvisited
    3. Then visit all normal nodes, each time choosing the nearest unvisited
    
    Args:
        graph: City graph to solve
        
    Returns:
        SolverResponse with route and metrics
    """
    start_time = time.time()
    
    nodes = graph.nodes
    priority_nodes = [n for n in nodes if n.type == NodeType.PRIORITY]
    normal_nodes = [n for n in nodes if n.type == NodeType.NORMAL]
    
    route: list[str] = []
    total_distance = 0.0
    travel_time = 0.0
    
    # Build adjacency info for quick lookups
    node_map = {n.id: n for n in nodes}
    
    def get_weighted_distance(from_id: str, to_id: str) -> tuple[float, float]:
        """Get base distance and traffic-weighted time between two nodes."""
        # Try to find direct edge
        for edge in graph.edges:
            if (edge.from_node == from_id and edge.to_node == to_id) or \
               (edge.from_node == to_id and edge.to_node == from_id):
                base_dist = edge.distance
                multiplier = graph.traffic_multipliers.get(edge.traffic.value, 1.0)
                return base_dist, base_dist * multiplier
        
        # Fall back to Euclidean distance
        n1, n2 = node_map[from_id], node_map[to_id]
        dist = euclidean_distance(n1.x, n1.y, n2.x, n2.y)
        return dist, dist  # No traffic adjustment for non-edges
    
    def find_nearest(current_id: str, candidates: list) -> str:
        """Find the nearest node from candidates using traffic-weighted distance."""
        if not candidates:
            return None
        
        best_id = None
        best_time = float('inf')
        
        for candidate in candidates:
            _, weighted_time = get_weighted_distance(current_id, candidate.id)
            if weighted_time < best_time:
                best_time = weighted_time
                best_id = candidate.id
        
        return best_id
    
    # Phase 1: Visit all priority nodes
    unvisited_priority = list(priority_nodes)
    
    if unvisited_priority:
        # Start with first priority node
        current = unvisited_priority.pop(0)
        route.append(current.id)
        
        while unvisited_priority:
            nearest_id = find_nearest(current.id, unvisited_priority)
            if nearest_id:
                dist, weighted = get_weighted_distance(current.id, nearest_id)
                total_distance += dist
                travel_time += weighted
                route.append(nearest_id)
                current = node_map[nearest_id]
                unvisited_priority = [n for n in unvisited_priority if n.id != nearest_id]
    else:
        current = normal_nodes[0] if normal_nodes else None
        if current:
            route.append(current.id)
    
    # Phase 2: Visit all normal nodes
    unvisited_normal = list(normal_nodes) if priority_nodes else normal_nodes[1:]
    
    while unvisited_normal:
        nearest_id = find_nearest(current.id, unvisited_normal)
        if nearest_id:
            dist, weighted = get_weighted_distance(current.id, nearest_id)
            total_distance += dist
            travel_time += weighted
            route.append(nearest_id)
            current = node_map[nearest_id]
            unvisited_normal = [n for n in unvisited_normal if n.id != nearest_id]
        else:
            break
    
    solve_time_ms = (time.time() - start_time) * 1000
    
    # Validate priority satisfaction
    priority_ids = set(n.id for n in priority_nodes)
    k = len(priority_ids)
    
    if k > 0:
        priority_positions = [i for i, node_id in enumerate(route) if node_id in priority_ids]
        priority_satisfied = max(priority_positions) < k if priority_positions else False
    else:
        priority_satisfied = True
    
    feasible = len(route) == len(nodes) and len(set(route)) == len(route)
    
    return SolverResponse(
        route=route,
        total_distance=round(total_distance, 2),
        travel_time=round(travel_time, 2),
        feasible=feasible,
        priority_satisfied=priority_satisfied,
        solve_time_ms=round(solve_time_ms, 3),
        energy=None,
        solver_used="greedy"
    )
