/**
 * API client for Quantum Priority Router
 */

import { API_BASE_URL, API_ENDPOINTS, API_KEY } from './config';
import type {
    CityGraph,
    SolverRequest,
    SolverResponse,
    ComparisonResponse,
    GraphListResponse,
    HealthResponse,
} from './types';

class ApiError extends Error {
    status: number;

    constructor(status: number, message: string) {
        super(message);
        this.name = 'ApiError';
        this.status = status;
    }
}

async function fetchApi<T>(
    endpoint: string,
    options: RequestInit = {}
): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const response = await fetch(url, {
        headers: {
            'Content-Type': 'application/json',
            'X-API-Key': API_KEY,
            ...options.headers,
        },
        ...options,
    });

    if (!response.ok) {
        const errorText = await response.text();
        throw new ApiError(response.status, errorText || 'Request failed');
    }

    return response.json();
}

/**
 * Check API health and D-Wave availability
 */
export async function checkHealth(): Promise<HealthResponse> {
    return fetchApi<HealthResponse>(API_ENDPOINTS.health);
}

/**
 * Solve routing problem with specified solver
 */
export async function solveRoute(request: SolverRequest): Promise<SolverResponse> {
    return fetchApi<SolverResponse>(API_ENDPOINTS.solve, {
        method: 'POST',
        body: JSON.stringify(request),
    });
}

/**
 * Compare quantum and greedy solvers
 */
export async function compareSolvers(graph: CityGraph): Promise<ComparisonResponse> {
    return fetchApi<ComparisonResponse>(API_ENDPOINTS.compare, {
        method: 'POST',
        body: JSON.stringify(graph),
    });
}

/**
 * Generate a random city graph
 */
export async function generateCity(
    nNodes: number = 10,
    priorityRatio: number = 0.3,
    trafficProfile: string = 'mixed',
    seed?: number
): Promise<CityGraph> {
    const body: Record<string, unknown> = {
        n_nodes: nNodes,
        priority_ratio: priorityRatio,
        traffic_profile: trafficProfile,
    };

    if (seed !== undefined) {
        body.seed = seed;
    }

    return fetchApi<CityGraph>(API_ENDPOINTS.generateCity, {
        method: 'POST',
        body: JSON.stringify(body),
    });
}

/**
 * List available sample graphs
 */
export async function listGraphs(): Promise<GraphListResponse> {
    return fetchApi<GraphListResponse>(API_ENDPOINTS.graphs);
}

/**
 * Get a specific sample graph
 */
export async function getGraph(name: string): Promise<CityGraph> {
    return fetchApi<CityGraph>(`${API_ENDPOINTS.graphs}/${name}`);
}

export { ApiError };
