/**
 * TypeScript types for Quantum Priority Router API
 */

// Node Types
export type NodeType = 'priority' | 'normal';
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
}

export interface ComparisonResponse {
  quantum: SolverResponse;
  greedy: SolverResponse;
  distance_reduction_pct: number;
  time_reduction_pct: number;
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
export interface HealthResponse {
  status: string;
  service: string;
  qaoa_info: {
    qiskit_available: boolean;
    use_mock: boolean;
    qaoa_reps: number;
    qaoa_shots: number;
    qiskit_version?: string;
    error?: string;
  };
}

// UI State
export interface RouteVisualization {
  nodes: Node[];
  edges: Edge[];
  route: string[];
  priorityNodes: Set<string>;
}
