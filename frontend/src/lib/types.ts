/**
 * TypeScript types for Quantum Priority Router API
 */

// Node Types
export type NodeType = 'priority' | 'normal' | 'depot';
export type TrafficLevel = 'low' | 'medium' | 'high';
export type SolverType = 'quantum' | 'greedy';

// Data Models
export interface Node {
  id: string;
  x: number;
  y: number;
  type: NodeType;
  label?: string;
}

export interface Edge {
  from: string;
  to: string;
  distance: number;
  traffic: TrafficLevel;
}

export interface TrafficMultipliers {
  low: number;
  medium: number;
  high: number;
}

export interface CityGraph {
  nodes: Node[];
  edges: Edge[];
  traffic_multipliers: TrafficMultipliers;
  metadata?: {
    name?: string;
    description?: string;
    priority_count?: number;
    normal_count?: number;
  };
}

// QUBO Parameters
export interface QUBOParams {
  A: number;  // One-hot constraint
  B: number;  // Priority ordering
  Bp: number; // Missing priority
  C: number;  // Objective weight
}

// API Request/Response
export interface SolverRequest {
  graph: CityGraph;
  solver: SolverType;
  params?: QUBOParams;
}

export interface SolverResponse {
  route: string[];
  total_distance: number;
  travel_time: number;
  feasible: boolean;
  priority_satisfied: boolean;
  solve_time_ms: number;
  energy: number | null;
  solver_used: string;
  distance_efficiency_ratio: number | null;
  priority_violation_count: number;
  traffic_time_ratio: number | null;
  depot_id: string | null;
}

export interface ComparisonResponse {
  quantum: SolverResponse;
  greedy: SolverResponse;
  distance_reduction_pct: number;
  time_reduction_pct: number;
  traffic_time_comparison: { quantum: number | null; greedy: number | null } | null;
}

// Graph Info
export interface GraphInfo {
  name: string;
  path: string;
}

export interface GraphListResponse {
  graphs: GraphInfo[];
}

// Health Check
export interface HealthDependency {
  name: string;
  status: string;
  details: {
    qiskit_available?: boolean;
    qiskit_components?: string;
    sampler_init?: string;
    message?: string;
    error?: string;
  };
}

export interface HealthResponse {
  status: string;
  service: string;
  timestamp: string;
  dependencies: HealthDependency[];
}

// UI State
export interface RouteVisualization {
  nodes: Node[];
  edges: Edge[];
  route: string[];
  priorityNodes: Set<string>;
}
