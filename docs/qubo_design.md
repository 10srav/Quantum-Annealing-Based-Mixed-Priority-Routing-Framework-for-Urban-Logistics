# QUBO Design Document

## Variable Encoding

We use **permutation/TSP-style encoding** where binary variables represent node-position assignments.

### Variable Definition

$$x_{i,p} \in \{0, 1\}$$

Where:
- $x_{i,p} = 1$ if node $i$ is assigned to route position $p$
- $x_{i,p} = 0$ otherwise

For a graph with $n$ nodes, we have $n^2$ binary variables.

### Variable Naming Convention

```
x_{node_id}_{position}

Examples:
- x_N1_0: Node N1 at position 0
- x_N2_1: Node N2 at position 1
```

---

## Core Constraints

### Constraint 1: Each Position Has Exactly One Node

Every route position must be occupied by exactly one node.

$$H_{pos} = A \sum_{p=0}^{n-1} \left(1 - \sum_{i \in V} x_{i,p}\right)^2$$

**Expanded form:**
$$H_{pos} = A \sum_{p} \left(1 - 2\sum_{i} x_{i,p} + \sum_{i}\sum_{j} x_{i,p} x_{j,p}\right)$$

### Constraint 2: Each Node Appears Exactly Once

Every node must appear in exactly one position.

$$H_{node} = A \sum_{i \in V} \left(\sum_{p=0}^{n-1} x_{i,p} - 1\right)^2$$

**Combined One-Hot Constraint:**
These form the standard TSP one-hot constraint ensuring a valid permutation.

---

## Priority-Before-Normal Constraints

### Priority Zone Definition

Let $k$ = number of priority nodes.
- **Priority zone:** positions $0, 1, ..., k-1$
- **Normal zone:** positions $k, k+1, ..., n-1$

### Constraint 3: Priority Node Position Restriction

Priority nodes must not appear in normal zone positions.

$$H_{priority\_pos} = B \sum_{i \in P} \sum_{p=k}^{n-1} x_{i,p}$$

### Constraint 4: Normal Node Position Restriction

Normal nodes must not appear in priority zone positions.

$$H_{normal\_pos} = B \sum_{j \in N} \sum_{p=0}^{k-1} x_{j,p}$$

### Constraint 5: All Priority Nodes Must Be Visited

Ensure every priority node appears somewhere in the route.

$$H_{visit} = B_p \sum_{i \in P} \left(1 - \sum_{p=0}^{n-1} x_{i,p}\right)^2$$

---

## Traffic-Weighted Objective Function

Minimize total travel time considering traffic conditions.

$$H_{objective} = C \sum_{p=0}^{n-2} \sum_{u \in V} \sum_{v \in V} d_{u,v}^{traffic} \cdot x_{u,p} \cdot x_{v,p+1}$$

### Traffic-Weighted Distance

$$d_{u,v}^{traffic} = d_{u,v}^{base} \times m_{traffic}$$

| Traffic Level | Multiplier ($m$) |
|---------------|------------------|
| Low | 1.0 |
| Medium | 1.5 |
| High | 2.0 |

---

## Complete Hamiltonian

$$H_{total} = H_{one-hot} + H_{priority} + H_{visit} + H_{objective}$$

$$H_{total} = A \cdot H_{pos} + A \cdot H_{node} + B \cdot (H_{priority\_pos} + H_{normal\_pos}) + B_p \cdot H_{visit} + C \cdot H_{objective}$$

---

## Penalty Coefficients (A, B, Bp, C)

### Parameter Roles

| Coefficient | Purpose | Recommended Range |
|-------------|---------|-------------------|
| **A** | One-hot constraint (valid permutation) | 50–200 |
| **B** | Priority ordering (zone enforcement) | 200–1000 |
| **B_p** | Priority coverage (visit all priorities) | 500–2000 |
| **C** | Objective weight (distance minimization) | 0.5–2.0 |

### Default Values

```python
A = 100.0   # One-hot penalty
B = 500.0   # Priority ordering
Bp = 1000.0 # Priority coverage
C = 1.0     # Objective weight
```

### Tuning Guidelines

1. **Start with defaults** and observe feasibility
2. **Infeasible solutions?** → Increase A (one-hot violations)
3. **Priority violations?** → Increase B and B_p
4. **Poor route quality?** → Decrease constraint penalties or increase C
5. **Energy scale issues?** → Ensure penalties >> objective contributions

### Penalty Hierarchy

For guaranteed constraint satisfaction:

$$A > \text{max edge weight}$$
$$B > A$$
$$B_p > B$$

---

## Implementation Notes

### QUBO Matrix Size

For $n$ nodes: matrix size is $n^2 \times n^2$

| Nodes | Variables | QUBO terms |
|-------|-----------|------------|
| 8 | 64 | ~4,096 |
| 10 | 100 | ~10,000 |
| 15 | 225 | ~50,625 |

### Solver Considerations

- **Small graphs (≤12 nodes):** Direct QPU embedding possible
- **Large graphs (>12 nodes):** Hybrid sampler recommended
- **Very large graphs (>50 nodes):** Consider classical heuristics

### Route Decoding

After solving, decode route from sample:

```python
def decode_route(sample, node_ids):
    route = [None] * len(node_ids)
    for var, value in sample.items():
        if value == 1 and var.startswith("x_"):
            parts = var.split("_")
            node_id = "_".join(parts[1:-1])
            position = int(parts[-1])
            route[position] = node_id
    return [n for n in route if n is not None]
```

### Validation Checks

1. **Feasibility:** Route length == number of nodes
2. **Priority Satisfaction:** All priority nodes in first k positions
3. **No duplicates:** Each node appears exactly once
