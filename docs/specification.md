# Project Specification Document

## Quantum-Annealing Mixed-Priority Routing Framework

**Version:** 1.0  
**Date:** January 2026  
**Status:** Implementation Complete

---

## 1. Executive Summary

This project implements a quantum-classical hybrid routing optimization system for urban logistics. It solves the Mixed-Priority Vehicle Routing Problem (MP-VRP) using D-Wave quantum annealing, with a greedy baseline for comparison.

---

## 2. Problem Statement

### 2.1 Business Context
Urban delivery services must balance:
- **Time-critical deliveries** (priority: medical supplies, perishables)
- **Standard deliveries** (normal: regular packages)
- **Traffic conditions** (variable travel times)

### 2.2 Technical Problem
Given a city graph G = (V, E):
- V = nodes (delivery locations)
- E = edges (roads with traffic-weighted distances)
- P ⊂ V = priority nodes
- N ⊂ V = normal nodes

**Find:** An optimal route visiting all nodes such that:
1. All priority nodes are visited before normal nodes
2. Total travel time (traffic-weighted) is minimized
3. All nodes are visited exactly once

---

## 3. Scenario Inputs

### 3.1 City Graph
| Field | Type | Description |
|-------|------|-------------|
| `nodes` | Array | List of delivery locations |
| `edges` | Array | Road connections with distances |
| `traffic_multipliers` | Object | Speed factors by traffic level |

### 3.2 Node Properties
| Field | Type | Values |
|-------|------|--------|
| `id` | String | Unique identifier (e.g., "N1") |
| `x`, `y` | Float | Geographic coordinates |
| `type` | Enum | "priority" or "normal" |

### 3.3 Edge Properties
| Field | Type | Description |
|-------|------|-------------|
| `from`, `to` | String | Connected node IDs |
| `distance` | Float | Physical distance (km) |
| `traffic` | Enum | "low", "medium", "high" |

### 3.4 Traffic Multipliers
| Level | Default | Effect |
|-------|---------|--------|
| Low | 1.0x | Normal speed |
| Medium | 1.5x | 50% slower |
| High | 2.0x | Twice as slow |

---

## 4. Solution Approach

### 4.1 Quantum Solver
- **Algorithm:** QUBO via D-Wave LeapHybridSampler
- **Encoding:** TSP-style permutation variables
- **Constraints:** Priority ordering, node uniqueness
- **Objective:** Minimize traffic-weighted distance

### 4.2 Greedy Baseline
- **Algorithm:** Nearest-neighbor heuristic
- **Constraint:** Priority-first traversal
- **Purpose:** Baseline comparison

---

## 5. Metrics

### 5.1 Primary Metrics
| Metric | Formula | Target |
|--------|---------|--------|
| Total Distance | Σ d(i, i+1) | Minimize |
| Travel Time | Σ d(i, i+1) × traffic_multiplier | Minimize |
| Feasibility | All nodes visited once | 100% |
| Priority Satisfied | All priority before normal | 100% |

### 5.2 Comparison Metrics
| Metric | Formula |
|--------|---------|
| Distance Reduction | (greedy - quantum) / greedy × 100% |
| Time Reduction | (greedy_time - quantum_time) / greedy_time × 100% |

---

## 6. System Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| QUBO Builder | dimod (Python) | Construct optimization model |
| Quantum Solver | D-Wave Leap | Solve QUBO |
| Greedy Solver | Python | Baseline algorithm |
| REST API | FastAPI | Service interface |
| Frontend | React + TypeScript | User interface |

---

## 7. Deliverables

- [x] QUBO formulation with priority constraints
- [x] D-Wave integration with mock fallback
- [x] Greedy baseline solver
- [x] FastAPI REST endpoints
- [x] React visualization frontend
- [x] Experiment harness with CSV export
- [x] Unit and integration tests
- [x] Documentation (API, setup, architecture)
- [x] Docker deployment configuration

---

## 8. Success Criteria

| Criterion | Target | Status |
|-----------|--------|--------|
| Quantum solver feasibility rate | > 80% | ✅ |
| Priority constraint satisfaction | 100% | ✅ |
| Distance reduction vs greedy | > 0% (when quantum feasible) | ✅ |
| API response time | < 30s | ✅ |
| Frontend usability | Interactive, responsive | ✅ |
