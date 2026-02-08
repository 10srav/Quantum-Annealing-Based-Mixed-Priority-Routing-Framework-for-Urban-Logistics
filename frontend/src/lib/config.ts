/**
 * API configuration
 */

export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const API_KEY = import.meta.env.VITE_API_KEY || 'test';

export const API_ENDPOINTS = {
    health: '/health',
    solve: '/solve',
    compare: '/compare',
    generateCity: '/generate-city',
    graphs: '/graphs',
} as const;

export const DEFAULT_QUBO_PARAMS = {
    A: 100,
    B: 500,
    Bp: 1000,
    C: 1,
};

export const TRAFFIC_COLORS = {
    low: '#22c55e',     // green
    medium: '#eab308',  // yellow
    high: '#ef4444',    // red
};

export const NODE_COLORS = {
    priority: '#ef4444',  // red
    normal: '#3b82f6',    // blue
    depot: '#f59e0b',     // amber
};
