# QUBO Mathematical Specification

## Variable Encoding

Using **permutation/TSP-style encoding**:

$$x_{i,p} = 1 \text{ if node } i \text{ is at route position } p, \text{ else } 0$$

Where:
- $n$ = total number of nodes
- $k$ = number of priority nodes
- Route length $L = n$
- Priority nodes must occupy positions $0, 1, ..., k-1$

## QUBO Hamiltonian

The total Hamiltonian consists of constraint terms and an objective term:

$$H = A \cdot H_{one-hot} + B \cdot H_{priority} + B_p \cdot H_{visit} + C \cdot H_{objective}$$

### Constraint 1: Each Position Has Exactly One Node

$$H_{pos} = \sum_{p=0}^{n-1} \left(1 - \sum_{i=1}^{n} x_{i,p}\right)^2$$

Expanded for QUBO:
$$H_{pos} = \sum_{p=0}^{n-1} \left(1 - 2\sum_{i} x_{i,p} + \sum_{i}\sum_{j} x_{i,p} x_{j,p}\right)$$

### Constraint 2: Each Node Appears Exactly Once

$$H_{node} = \sum_{i=1}^{n} \left(\sum_{p=0}^{n-1} x_{i,p} - 1\right)^2$$

### Constraint 3: Priority Ordering

For priority nodes $i \in P$ and normal nodes $j \in N$:
- Priority nodes cannot be in positions $\geq k$
- Normal nodes cannot be in positions $< k$

$$H_{priority} = \sum_{i \in P} \sum_{p=k}^{n-1} x_{i,p} + \sum_{j \in N} \sum_{p=0}^{k-1} x_{j,p}$$

### Constraint 4: All Priority Nodes Must Be Visited

$$H_{visit} = \sum_{i \in P} \left(1 - \sum_{p=0}^{n-1} x_{i,p}\right)^2$$

### Objective: Minimize Traffic-Weighted Distance

$$H_{objective} = \sum_{p=0}^{n-2} \sum_{u=1}^{n} \sum_{v=1}^{n} d_{u,v}^{traffic} \cdot x_{u,p} \cdot x_{v,p+1}$$

Where:
$$d_{u,v}^{traffic} = d_{u,v}^{base} \times m_{traffic}$$

Traffic multipliers:
- $m_{low} = 1.0$
- $m_{medium} = 1.5$  
- $m_{high} = 2.0$

## Penalty Coefficients

| Coefficient | Purpose | Recommended Range |
|-------------|---------|-------------------|
| $A$ | One-hot constraint enforcement | 50-200 |
| $B$ | Priority ordering constraint | 200-1000 |
| $B_p$ | Missing priority penalty | 500-2000 |
| $C$ | Objective weight | 0.5-2.0 |

### Tuning Guidelines

1. Start with $A = 100$, $B = 500$, $B_p = 1000$, $C = 1$
2. If infeasible solutions appear, increase $A$ and $B$
3. If priority violations occur, increase $B$ and $B_p$
4. If solution quality is poor, decrease $A$/$B$ slightly or increase $C$

## QUBO Matrix Construction

For a graph with $n$ nodes, the QUBO has $n^2$ binary variables.

The Q matrix is constructed as:
$$Q_{(i,p)(j,q)} = \text{coefficient from } x_{i,p} \cdot x_{j,q} \text{ terms}$$

### Example: 4-Node Problem (2 Priority, 2 Normal)

Variables: $x_{1,0}, x_{1,1}, x_{1,2}, x_{1,3}, x_{2,0}, ..., x_{4,3}$

Matrix size: $16 \times 16$
