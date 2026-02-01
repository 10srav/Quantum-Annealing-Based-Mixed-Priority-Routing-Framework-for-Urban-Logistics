/**
 * React hook for solver operations
 */

import { useState, useCallback } from 'react';
import { solveRoute, compareSolvers, generateCity, checkHealth } from '../lib/api';
import type {
    CityGraph,
    SolverResponse,
    ComparisonResponse,
    SolverType,
    QUBOParams,
    HealthResponse,
} from '../lib/types';

interface UseSolverState {
    loading: boolean;
    error: string | null;
    quantumResult: SolverResponse | null;
    greedyResult: SolverResponse | null;
    comparison: ComparisonResponse | null;
}

export function useSolver() {
    const [state, setState] = useState<UseSolverState>({
        loading: false,
        error: null,
        quantumResult: null,
        greedyResult: null,
        comparison: null,
    });

    const solve = useCallback(async (
        graph: CityGraph,
        solver: SolverType,
        params?: QUBOParams
    ): Promise<SolverResponse | null> => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const result = await solveRoute({ graph, solver, params });

            setState(prev => ({
                ...prev,
                loading: false,
                [solver === 'quantum' ? 'quantumResult' : 'greedyResult']: result,
            }));

            return result;
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setState(prev => ({ ...prev, loading: false, error: message }));
            return null;
        }
    }, []);

    const compare = useCallback(async (graph: CityGraph): Promise<ComparisonResponse | null> => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const result = await compareSolvers(graph);

            setState(prev => ({
                ...prev,
                loading: false,
                quantumResult: result.quantum,
                greedyResult: result.greedy,
                comparison: result,
            }));

            return result;
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setState(prev => ({ ...prev, loading: false, error: message }));
            return null;
        }
    }, []);

    const clear = useCallback(() => {
        setState({
            loading: false,
            error: null,
            quantumResult: null,
            greedyResult: null,
            comparison: null,
        });
    }, []);

    return {
        ...state,
        solve,
        compare,
        clear,
    };
}

interface UseCityGraphState {
    graph: CityGraph | null;
    loading: boolean;
    error: string | null;
}

export function useCityGraph() {
    const [state, setState] = useState<UseCityGraphState>({
        graph: null,
        loading: false,
        error: null,
    });

    const generate = useCallback(async (
        nNodes: number = 10,
        priorityRatio: number = 0.3,
        trafficProfile: string = 'mixed'
    ): Promise<CityGraph | null> => {
        setState(prev => ({ ...prev, loading: true, error: null }));

        try {
            const graph = await generateCity(nNodes, priorityRatio, trafficProfile);
            setState({ graph, loading: false, error: null });
            return graph;
        } catch (err) {
            const message = err instanceof Error ? err.message : 'Unknown error';
            setState(prev => ({ ...prev, loading: false, error: message }));
            return null;
        }
    }, []);

    const setGraph = useCallback((graph: CityGraph) => {
        setState({ graph, loading: false, error: null });
    }, []);

    return {
        ...state,
        generate,
        setGraph,
    };
}

export function useHealth() {
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [loading, setLoading] = useState(false);

    const check = useCallback(async () => {
        setLoading(true);
        try {
            const result = await checkHealth();
            setHealth(result);
        } catch (err) {
            setHealth(null);
        }
        setLoading(false);
    }, []);

    return { health, loading, check };
}
