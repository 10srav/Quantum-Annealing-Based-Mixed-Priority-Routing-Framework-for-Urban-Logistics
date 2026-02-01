/**
 * MetricsTable - Display solver results and comparison metrics
 */

import React from 'react';
import type { SolverResponse, ComparisonResponse } from '../lib/types';

interface MetricsTableProps {
    quantumResult: SolverResponse | null;
    greedyResult: SolverResponse | null;
    comparison: ComparisonResponse | null;
}

export const MetricsTable: React.FC<MetricsTableProps> = ({
    quantumResult,
    greedyResult,
    comparison,
}) => {
    if (!quantumResult && !greedyResult) {
        return (
            <div className="metrics-table metrics-table--empty">
                <p>Run a solver to see results</p>
            </div>
        );
    }

    return (
        <div className="metrics-table">
            <h3>📊 Results</h3>

            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        {quantumResult && <th>⚛️ Quantum</th>}
                        {greedyResult && <th>🔢 Greedy</th>}
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Route</td>
                        {quantumResult && (
                            <td className="route-cell">{quantumResult.route.join(' → ')}</td>
                        )}
                        {greedyResult && (
                            <td className="route-cell">{greedyResult.route.join(' → ')}</td>
                        )}
                    </tr>
                    <tr>
                        <td>Distance (km)</td>
                        {quantumResult && <td>{quantumResult.total_distance.toFixed(2)}</td>}
                        {greedyResult && <td>{greedyResult.total_distance.toFixed(2)}</td>}
                    </tr>
                    <tr>
                        <td>Travel Time</td>
                        {quantumResult && <td>{quantumResult.travel_time.toFixed(2)}</td>}
                        {greedyResult && <td>{greedyResult.travel_time.toFixed(2)}</td>}
                    </tr>
                    <tr>
                        <td>Feasible</td>
                        {quantumResult && (
                            <td className={quantumResult.feasible ? 'status-ok' : 'status-fail'}>
                                {quantumResult.feasible ? '✓' : '✗'}
                            </td>
                        )}
                        {greedyResult && (
                            <td className={greedyResult.feasible ? 'status-ok' : 'status-fail'}>
                                {greedyResult.feasible ? '✓' : '✗'}
                            </td>
                        )}
                    </tr>
                    <tr>
                        <td>Priority Satisfied</td>
                        {quantumResult && (
                            <td className={quantumResult.priority_satisfied ? 'status-ok' : 'status-fail'}>
                                {quantumResult.priority_satisfied ? '✓' : '✗'}
                            </td>
                        )}
                        {greedyResult && (
                            <td className={greedyResult.priority_satisfied ? 'status-ok' : 'status-fail'}>
                                {greedyResult.priority_satisfied ? '✓' : '✗'}
                            </td>
                        )}
                    </tr>
                    <tr>
                        <td>Solve Time (ms)</td>
                        {quantumResult && <td>{quantumResult.solve_time_ms.toFixed(1)}</td>}
                        {greedyResult && <td>{greedyResult.solve_time_ms.toFixed(2)}</td>}
                    </tr>
                    {quantumResult?.energy !== null && (
                        <tr>
                            <td>QUBO Energy</td>
                            <td>{quantumResult?.energy?.toFixed(2) ?? '-'}</td>
                            {greedyResult && <td>-</td>}
                        </tr>
                    )}
                </tbody>
            </table>

            {comparison && (
                <div className="comparison-summary">
                    <h4>📈 Comparison</h4>
                    <div className={`metric-card ${comparison.distance_reduction_pct > 0 ? 'positive' : 'negative'}`}>
                        <span className="metric-value">
                            {comparison.distance_reduction_pct > 0 ? '+' : ''}
                            {comparison.distance_reduction_pct.toFixed(1)}%
                        </span>
                        <span className="metric-label">Distance Reduction</span>
                    </div>
                    <div className={`metric-card ${comparison.time_reduction_pct > 0 ? 'positive' : 'negative'}`}>
                        <span className="metric-value">
                            {comparison.time_reduction_pct > 0 ? '+' : ''}
                            {comparison.time_reduction_pct.toFixed(1)}%
                        </span>
                        <span className="metric-label">Time Reduction</span>
                    </div>
                </div>
            )}
        </div>
    );
};
