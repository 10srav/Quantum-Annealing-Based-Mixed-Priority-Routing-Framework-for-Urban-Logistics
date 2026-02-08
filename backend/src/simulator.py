"""
Synthetic City Graph Generator.

Generates random city graphs for experiments with configurable:
- Number of nodes
- Priority/normal ratio
- Traffic distribution
- Network connectivity
"""

import random
import math
from typing import Literal

from .data_models import Node, Edge, CityGraph, NodeType, TrafficLevel


def generate_random_city(
    n_nodes: int = 10,
    priority_ratio: float = 0.3,
    traffic_profile: Literal["low", "mixed", "high"] = "mixed",
    connectivity: int = 3,
    seed: int | None = None,
    include_depot: bool = False,
) -> CityGraph:
    """
    Generate a random city graph for testing.

    Args:
        n_nodes: Total number of nodes (including depot if requested)
        priority_ratio: Fraction of delivery nodes that are priority (0.0-1.0)
        traffic_profile: Distribution of traffic levels
        connectivity: Average number of edges per node (k-nearest neighbors)
        seed: Random seed for reproducibility
        include_depot: If True, the first node is a depot/warehouse near grid center

    Returns:
        CityGraph with random nodes and edges
    """
    if seed is not None:
        random.seed(seed)

    # Generate node positions in a 10x10 grid
    nodes = []
    positions = []

    # If depot requested, create it first near grid center
    start_idx = 0
    if include_depot:
        dx = random.uniform(4, 6)
        dy = random.uniform(4, 6)
        positions.append((dx, dy))
        nodes.append(Node(
            id="D0",
            x=round(dx, 2),
            y=round(dy, 2),
            type=NodeType.DEPOT,
            label="Depot",
        ))
        start_idx = 1

    n_delivery = n_nodes - start_idx
    for i in range(n_delivery):
        x = random.uniform(0, 10)
        y = random.uniform(0, 10)
        positions.append((x, y))

        # Assign priority based on ratio
        is_priority = random.random() < priority_ratio
        node_type = NodeType.PRIORITY if is_priority else NodeType.NORMAL

        nodes.append(Node(
            id=f"N{i+1}",
            x=round(x, 2),
            y=round(y, 2),
            type=node_type,
            label=f"{'Priority' if is_priority else 'Normal'} {i+1}"
        ))

    # Ensure at least one priority node among delivery nodes
    delivery_nodes = [n for n in nodes if n.type != NodeType.DEPOT]
    if not any(n.type == NodeType.PRIORITY for n in delivery_nodes):
        idx = start_idx  # first delivery node index
        nodes[idx] = Node(
            id=nodes[idx].id,
            x=nodes[idx].x,
            y=nodes[idx].y,
            type=NodeType.PRIORITY,
            label="Priority 1"
        )
    
    # Generate edges using k-nearest neighbors
    edges = []
    seen_edges = set()
    
    for i, (x1, y1) in enumerate(positions):
        # Compute distances to all other nodes
        distances = []
        for j, (x2, y2) in enumerate(positions):
            if i != j:
                dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                distances.append((j, dist))
        
        # Connect to k-nearest neighbors
        distances.sort(key=lambda x: x[1])
        
        for j, dist in distances[:connectivity]:
            edge_key = tuple(sorted([i, j]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                
                # Assign traffic based on profile
                traffic = _get_traffic_level(traffic_profile)
                
                edges.append(Edge(
                    from_node=nodes[i].id,
                    to_node=nodes[j].id,
                    distance=round(dist, 2),
                    traffic=traffic
                ))
    
    # Ensure graph is connected (add edges if necessary)
    edges = _ensure_connectivity(nodes, edges, positions, traffic_profile)
    
    return CityGraph(
        nodes=nodes,
        edges=edges,
        traffic_multipliers={
            "low": 1.0,
            "medium": 1.5,
            "high": 2.0
        }
    )


def _get_traffic_level(profile: str) -> TrafficLevel:
    """Get a random traffic level based on profile."""
    if profile == "low":
        weights = [0.7, 0.2, 0.1]
    elif profile == "high":
        weights = [0.1, 0.2, 0.7]
    else:  # mixed
        weights = [0.33, 0.34, 0.33]
    
    levels = [TrafficLevel.LOW, TrafficLevel.MEDIUM, TrafficLevel.HIGH]
    return random.choices(levels, weights=weights)[0]


def _ensure_connectivity(
    nodes: list[Node],
    edges: list[Edge],
    positions: list[tuple[float, float]],
    traffic_profile: str
) -> list[Edge]:
    """Ensure the graph is connected using union-find."""
    n = len(nodes)
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
            return True
        return False
    
    # Build node ID to index mapping
    id_to_idx = {n.id: i for i, n in enumerate(nodes)}
    
    # Process existing edges
    for edge in edges:
        i, j = id_to_idx[edge.from_node], id_to_idx[edge.to_node]
        union(i, j)
    
    # Add edges to connect components
    edges = list(edges)
    seen = set((edge.from_node, edge.to_node) for edge in edges)
    seen.update((edge.to_node, edge.from_node) for edge in edges)
    
    for i in range(n):
        for j in range(i + 1, n):
            if find(i) != find(j):
                if (nodes[i].id, nodes[j].id) not in seen:
                    x1, y1 = positions[i]
                    x2, y2 = positions[j]
                    dist = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                    
                    edges.append(Edge(
                        from_node=nodes[i].id,
                        to_node=nodes[j].id,
                        distance=round(dist, 2),
                        traffic=_get_traffic_level(traffic_profile)
                    ))
                    seen.add((nodes[i].id, nodes[j].id))
                    union(i, j)
    
    return edges


def generate_experiment_suite(
    n_values: list[int] = [10, 15, 20],
    traffic_profiles: list[str] = ["low", "mixed", "high"],
    runs_per_config: int = 5
) -> list[dict]:
    """
    Generate a suite of experiment configurations.
    
    Returns:
        List of configs with graph and metadata
    """
    configs = []
    
    for n in n_values:
        for traffic in traffic_profiles:
            for run in range(runs_per_config):
                seed = hash((n, traffic, run)) % (2**31)
                graph = generate_random_city(
                    n_nodes=n,
                    traffic_profile=traffic,
                    seed=seed
                )
                
                configs.append({
                    "n_nodes": n,
                    "traffic_profile": traffic,
                    "run": run,
                    "seed": seed,
                    "graph": graph
                })
    
    return configs
