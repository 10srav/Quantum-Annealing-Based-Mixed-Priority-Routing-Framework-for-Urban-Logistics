/**
 * ResultsHistory - Track and export solver results
 */

import React, { useState, useCallback } from 'react';
import type { SolverResponse } from '../lib/types';

interface HistoryEntry {
    id: number;
    timestamp: Date;
    graphSize: number;
    solver: string;
    result: SolverResponse;
}

interface ResultsHistoryProps {
    onLoadResult?: (result: SolverResponse) => void;
}

export const ResultsHistory: React.FC<ResultsHistoryProps> = ({ onLoadResult }) => {
    const [history, setHistory] = useState<HistoryEntry[]>([]);
    const [nextId, setNextId] = useState(1);

    const addToHistory = useCallback((result: SolverResponse, graphSize: number) => {
        const entry: HistoryEntry = {
            id: nextId,
            timestamp: new Date(),
            graphSize,
            solver: result.solver_used,
            result,
        };
        setHistory(prev => [entry, ...prev].slice(0, 50)); // Keep last 50
        setNextId(prev => prev + 1);
    }, [nextId]);

    const clearHistory = useCallback(() => {
        setHistory([]);
    }, []);

    const exportToCsv = useCallback(() => {
        if (history.length === 0) return;

        const headers = [
            'ID', 'Timestamp', 'Graph Size', 'Solver',
            'Route', 'Distance', 'Travel Time',
            'Feasible', 'Priority Satisfied', 'Solve Time (ms)'
        ];

        const rows = history.map(entry => [
            entry.id,
            entry.timestamp.toISOString(),
            entry.graphSize,
            entry.solver,
            entry.result.route.join(' → '),
            entry.result.total_distance,
            entry.result.travel_time,
            entry.result.feasible,
            entry.result.priority_satisfied,
            entry.result.solve_time_ms,
        ]);

        const csv = [
            headers.join(','),
            ...rows.map(row => row.map(cell => `"${cell}"`).join(','))
        ].join('\n');

        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `quantum_router_results_${new Date().toISOString().slice(0, 10)}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }, [history]);

    // Expose addToHistory for parent component
    React.useEffect(() => {
        (window as any).__addToHistory = addToHistory;
        return () => {
            delete (window as any).__addToHistory;
        };
    }, [addToHistory]);

    return (
        <div className="results-history">
            <div className="history-header">
                <h3>📋 Results History</h3>
                <div className="history-actions">
                    <button
                        className="btn btn-sm"
                        onClick={exportToCsv}
                        disabled={history.length === 0}
                    >
                        📥 Export CSV
                    </button>
                    <button
                        className="btn btn-sm btn-danger"
                        onClick={clearHistory}
                        disabled={history.length === 0}
                    >
                        🗑️ Clear
                    </button>
                </div>
            </div>

            {history.length === 0 ? (
                <div className="history-empty">
                    <p>No results yet. Run a solver to see history.</p>
                </div>
            ) : (
                <div className="history-table-wrapper">
                    <table className="history-table">
                        <thead>
                            <tr>
                                <th>#</th>
                                <th>Time</th>
                                <th>Nodes</th>
                                <th>Solver</th>
                                <th>Distance</th>
                                <th>✓</th>
                            </tr>
                        </thead>
                        <tbody>
                            {history.map(entry => (
                                <tr
                                    key={entry.id}
                                    onClick={() => onLoadResult?.(entry.result)}
                                    className="history-row"
                                >
                                    <td>{entry.id}</td>
                                    <td>{entry.timestamp.toLocaleTimeString()}</td>
                                    <td>{entry.graphSize}</td>
                                    <td>
                                        <span className={`solver-badge ${entry.solver.includes('quantum') ? 'quantum' : 'greedy'}`}>
                                            {entry.solver.includes('quantum') ? '⚛️' : '🔢'}
                                        </span>
                                    </td>
                                    <td>{entry.result.total_distance.toFixed(1)}</td>
                                    <td>
                                        {entry.result.feasible && entry.result.priority_satisfied ? '✅' : '❌'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};
