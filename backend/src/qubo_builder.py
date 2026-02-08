"""
QUBO Builder for Priority-Constrained Routing.

Constructs a Quadratic Unconstrained Binary Optimization (QUBO) problem
for the mixed-priority traveling salesman problem using D-Wave's dimod.

The QUBO encodes:
1. TSP-style permutation: x_{i,p} = 1 if node i is at position p
2. Priority constraints: priority nodes must occupy first k positions
3. Traffic-weighted objective: minimize total travel time
"""

import numpy as np
from dimod import BinaryQuadraticModel, Vartype
from typing import Any

from .data_models import CityGraph, NodeType, QUBOParams


def build_qubo(
    graph: CityGraph,
    params: QUBOParams | None = None
) -> BinaryQuadraticModel:
    """
    Build a QUBO for the priority-constrained routing problem.
    
    Args:
        graph: City graph with nodes and edges
        params: QUBO penalty coefficients
        
    Returns:
        BinaryQuadraticModel ready for D-Wave sampling
    """
    if params is None:
        params = QUBOParams()
    
    # Exclude depot from QUBO variables — depot is prepended to the route after decoding
    delivery_nodes = graph.delivery_nodes
    n = len(delivery_nodes)
    node_ids = [node.id for node in delivery_nodes]
    depot = graph.depot_node

    # Separate priority and normal nodes (among delivery nodes only)
    priority_ids = [node.id for node in delivery_nodes if node.type == NodeType.PRIORITY]
    normal_ids = [node.id for node in delivery_nodes if node.type == NodeType.NORMAL]
    k = len(priority_ids)  # Number of priority positions
    
    # Create BQM
    bqm = BinaryQuadraticModel(vartype=Vartype.BINARY)
    
    # Variable naming convention: x_{node_id}_{position}
    def var(node_id: str, pos: int) -> str:
        return f"x_{node_id}_{pos}"
    
    # Add all variables
    for node_id in node_ids:
        for p in range(n):
            bqm.add_variable(var(node_id, p), 0.0)
    
    # ============================================================
    # Constraint 1: Each position has exactly one node
    # sum_i(x_{i,p}) = 1 for all p
    # Penalty: A * (1 - sum_i(x_{i,p}))^2 = A * (1 - 2*sum + sum^2)
    # ============================================================
    for p in range(n):
        # Linear terms: -2A for each variable
        for node_id in node_ids:
            bqm.add_linear(var(node_id, p), -2 * params.A)
        
        # Quadratic terms: 2A for each pair (x_i,p * x_j,p where i != j)
        for i, node_i in enumerate(node_ids):
            for j, node_j in enumerate(node_ids):
                if i < j:
                    bqm.add_quadratic(var(node_i, p), var(node_j, p), 2 * params.A)
        
        # Constant term: A (we track this separately if needed)
        bqm.offset += params.A
    
    # ============================================================
    # Constraint 2: Each node appears at most once
    # sum_p(x_{i,p}) <= 1 for all i
    # For TSP we want exactly once, so: (sum_p(x_{i,p}) - 1)^2
    # ============================================================
    for node_id in node_ids:
        # Linear terms: -2A for each variable
        for p in range(n):
            bqm.add_linear(var(node_id, p), -2 * params.A)
        
        # Quadratic terms: 2A for each pair (x_i,p * x_i,q where p != q)
        for p in range(n):
            for q in range(p + 1, n):
                bqm.add_quadratic(var(node_id, p), var(node_id, q), 2 * params.A)
        
        # Constant term: A
        bqm.offset += params.A
    
    # ============================================================
    # Constraint 3: Priority nodes in positions 0..k-1
    # Priority node in position >= k gets penalty B
    # Normal node in position < k gets penalty B
    # ============================================================
    for node_id in priority_ids:
        for p in range(k, n):  # Positions k to n-1 are forbidden for priority
            bqm.add_linear(var(node_id, p), params.B)
    
    for node_id in normal_ids:
        for p in range(k):  # Positions 0 to k-1 are forbidden for normal
            bqm.add_linear(var(node_id, p), params.B)
    
    # ============================================================
    # Constraint 4: All priority nodes must be visited
    # Penalty for missing priority: Bp * (1 - sum_p(x_{i,p}))^2
    # We already enforce sum_p = 1 above, but add extra penalty for priority
    # ============================================================
    for node_id in priority_ids:
        for p in range(n):
            bqm.add_linear(var(node_id, p), -2 * params.Bp)
        
        for p in range(n):
            for q in range(p + 1, n):
                bqm.add_quadratic(var(node_id, p), var(node_id, q), 2 * params.Bp)
        
        bqm.offset += params.Bp
    
    # ============================================================
    # Objective: Minimize traffic-weighted travel distance
    # sum_p(d_{u,v}^traffic * x_{u,p} * x_{v,p+1})
    # ============================================================
    for p in range(n - 1):
        for node_u in node_ids:
            for node_v in node_ids:
                if node_u != node_v:
                    weight = graph.get_edge_weight(node_u, node_v)
                    if weight < float('inf'):
                        bqm.add_quadratic(
                            var(node_u, p),
                            var(node_v, p + 1),
                            params.C * weight
                        )

    # ============================================================
    # Depot bias: Add depot→first-node distance as linear bias
    # on position 0 variables so QAOA prefers nearby first stops.
    # ============================================================
    if depot is not None:
        for node_id in node_ids:
            weight = graph.get_edge_weight(depot.id, node_id)
            if weight < float('inf'):
                bqm.add_linear(var(node_id, 0), params.C * weight)

    return bqm


def decode_route(
    sample: dict[str, int],
    node_ids: list[str],
    depot_id: str | None = None,
) -> list[str]:
    """
    Decode a QUBO sample into an ordered route.

    Args:
        sample: Binary variable assignments from sampler
        node_ids: List of delivery node IDs (excluding depot)
        depot_id: If provided, prepended to the decoded route

    Returns:
        Ordered list of node IDs representing the route
    """
    n = len(node_ids)
    route = [None] * n

    for key, value in sample.items():
        if value == 1 and key.startswith("x_"):
            parts = key.split("_")
            node_id = "_".join(parts[1:-1])  # Handle node IDs with underscores
            pos = int(parts[-1])
            if 0 <= pos < n:
                route[pos] = node_id

    # Remove None values
    decoded = [node_id for node_id in route if node_id is not None]

    # Prepend depot if present
    if depot_id is not None:
        decoded = [depot_id] + decoded

    return decoded


def validate_route(
    route: list[str],
    graph: CityGraph
) -> tuple[bool, bool]:
    """
    Validate a route against constraints.

    Args:
        route: Ordered list of node IDs
        graph: City graph

    Returns:
        Tuple of (feasible, priority_satisfied)
    """
    node_ids = [n.id for n in graph.nodes]
    priority_ids = set(n.id for n in graph.priority_nodes)
    k = len(priority_ids)
    depot = graph.depot_node

    # Check if route covers all nodes
    if set(route) != set(node_ids):
        return False, False

    # Priority ordering is checked among delivery positions only.
    # If depot exists, it occupies position 0 — skip it for priority check.
    delivery_route = route[1:] if depot and route and route[0] == depot.id else route

    priority_positions = [i for i, node_id in enumerate(delivery_route) if node_id in priority_ids]
    if not priority_positions:
        priority_satisfied = True if k == 0 else False
    else:
        max_priority_pos = max(priority_positions)
        priority_satisfied = max_priority_pos < k

    # Route is feasible if it visits all nodes exactly once
    feasible = len(route) == len(node_ids) and len(set(route)) == len(route)

    return feasible, priority_satisfied


def compute_route_metrics(
    route: list[str],
    graph: CityGraph
) -> tuple[float, float]:
    """
    Compute total distance and travel time for a route.
    
    Args:
        route: Ordered list of node IDs
        graph: City graph
        
    Returns:
        Tuple of (total_distance, travel_time)
    """
    total_distance = 0.0
    travel_time = 0.0
    
    for i in range(len(route) - 1):
        from_id, to_id = route[i], route[i + 1]
        
        # Find edge
        edge = None
        for e in graph.edges:
            if (e.from_node == from_id and e.to_node == to_id) or \
               (e.from_node == to_id and e.to_node == from_id):
                edge = e
                break
        
        if edge:
            total_distance += edge.distance
            multiplier = graph.traffic_multipliers.get(edge.traffic.value, 1.0)
            travel_time += edge.distance * multiplier
        else:
            # Use Euclidean distance as fallback
            n1, n2 = graph.get_node(from_id), graph.get_node(to_id)
            if n1 and n2:
                dist = ((n1.x - n2.x) ** 2 + (n1.y - n2.y) ** 2) ** 0.5
                total_distance += dist
                travel_time += dist
    
    return total_distance, travel_time


def count_priority_violations(route: list[str], graph: CityGraph) -> int:
    """
    Count how many priority nodes are NOT in the first k positions.

    Args:
        route: Ordered list of node IDs
        graph: City graph

    Returns:
        Number of priority nodes appearing after position k (0 = fully satisfied)
    """
    priority_ids = set(n.id for n in graph.priority_nodes)
    k = len(priority_ids)

    if k == 0:
        return 0

    # Skip depot at position 0 — priority ordering applies to delivery positions only
    depot = graph.depot_node
    delivery_route = route[1:] if depot and route and route[0] == depot.id else route

    violations = 0
    for i, node_id in enumerate(delivery_route):
        if node_id in priority_ids and i >= k:
            violations += 1

    return violations


def compute_efficiency_ratio(route: list[str], total_distance: float, graph: CityGraph) -> float:
    """
    Compute distance efficiency ratio: actual route distance / straight-line distance.

    A ratio of 1.0 means the route is perfectly straight. Higher values mean
    more detour. Useful for comparing how much extra distance priority
    constraints or traffic avoidance adds.

    Args:
        route: Ordered list of node IDs
        total_distance: Pre-computed total route distance
        graph: City graph

    Returns:
        Efficiency ratio (>=1.0, lower is better). Returns 1.0 for degenerate cases.
    """
    if len(route) < 2 or total_distance <= 0:
        return 1.0

    node_lookup = {n.id: n for n in graph.nodes}
    start = node_lookup.get(route[0])
    end = node_lookup.get(route[-1])

    if not start or not end:
        return 1.0

    euclidean = ((end.x - start.x) ** 2 + (end.y - start.y) ** 2) ** 0.5
    if euclidean <= 0:
        return 1.0

    return total_distance / euclidean
