/**
 * MetricsChart - Visualization of solver comparison metrics
 */

import React, { useMemo } from 'react';
import type { SolverResponse, ComparisonResponse } from '../lib/types';

interface MetricsChartProps {
    quantumResult: SolverResponse | null;
    greedyResult: SolverResponse | null;
    comparison: ComparisonResponse | null;
}

interface BarProps {
    label: string;
    value: number;
    maxValue: number;
    color: string;
    unit?: string;
}

const Bar: React.FC<BarProps> = ({ label, value, maxValue, color, unit = '' }) => {
    const percentage = Math.min((value / maxValue) * 100, 100);

    return (
        <div className="chart-bar">
            <div className="bar-label">{label}</div>
            <div className="bar-container">
                <div
                    className="bar-fill"
                    style={{
                        width: `${percentage}%`,
                        backgroundColor: color
                    }}
                />
                <span className="bar-value">{value.toFixed(2)}{unit}</span>
            </div>
        </div>
    );
};

export const MetricsChart: React.FC<MetricsChartProps> = ({
    quantumResult,
    greedyResult,
    comparison,
}) => {
    const chartData = useMemo(() => {
        if (!quantumResult && !greedyResult) return null;

        const distances = [
            quantumResult?.total_distance || 0,
            greedyResult?.total_distance || 0,
        ].filter(v => v > 0);

        const times = [
            quantumResult?.travel_time || 0,
            greedyResult?.travel_time || 0,
        ].filter(v => v > 0);

        const solveTimes = [
            quantumResult?.solve_time_ms || 0,
            greedyResult?.solve_time_ms || 0,
        ].filter(v => v > 0);

        const efficiencyRatios = [
            quantumResult?.distance_efficiency_ratio || 0,
            greedyResult?.distance_efficiency_ratio || 0,
        ].filter(v => v > 0);

        return {
            maxDistance: Math.max(...distances) * 1.1,
            maxTime: Math.max(...times) * 1.1,
            maxSolveTime: Math.max(...solveTimes) * 1.1,
            maxEfficiency: efficiencyRatios.length > 0 ? Math.max(...efficiencyRatios) * 1.1 : 2,
        };
    }, [quantumResult, greedyResult]);

    if (!chartData) {
        return (
            <div className="metrics-chart metrics-chart--empty">
                <p>Run solvers to see comparison charts</p>
            </div>
        );
    }

    return (
        <div className="metrics-chart">
            <h3>📈 Performance Comparison</h3>

            <div className="chart-section">
                <h4>Total Distance (km)</h4>
                {quantumResult && (
                    <Bar
                        label="Quantum"
                        value={quantumResult.total_distance}
                        maxValue={chartData.maxDistance}
                        color="#8b5cf6"
                        unit=" km"
                    />
                )}
                {greedyResult && (
                    <Bar
                        label="Greedy"
                        value={greedyResult.total_distance}
                        maxValue={chartData.maxDistance}
                        color="#06b6d4"
                        unit=" km"
                    />
                )}
            </div>

            <div className="chart-section">
                <h4>Travel Time (weighted)</h4>
                {quantumResult && (
                    <Bar
                        label="Quantum"
                        value={quantumResult.travel_time}
                        maxValue={chartData.maxTime}
                        color="#8b5cf6"
                    />
                )}
                {greedyResult && (
                    <Bar
                        label="Greedy"
                        value={greedyResult.travel_time}
                        maxValue={chartData.maxTime}
                        color="#06b6d4"
                    />
                )}
            </div>

            <div className="chart-section">
                <h4>Efficiency Ratio (lower = better)</h4>
                {quantumResult?.distance_efficiency_ratio != null && (
                    <Bar
                        label="Quantum"
                        value={quantumResult.distance_efficiency_ratio}
                        maxValue={chartData.maxEfficiency}
                        color="#8b5cf6"
                        unit="x"
                    />
                )}
                {greedyResult?.distance_efficiency_ratio != null && (
                    <Bar
                        label="Greedy"
                        value={greedyResult.distance_efficiency_ratio}
                        maxValue={chartData.maxEfficiency}
                        color="#06b6d4"
                        unit="x"
                    />
                )}
            </div>

            <div className="chart-section">
                <h4>Solve Time (ms)</h4>
                {quantumResult && (
                    <Bar
                        label="Quantum"
                        value={quantumResult.solve_time_ms}
                        maxValue={chartData.maxSolveTime}
                        color="#8b5cf6"
                        unit=" ms"
                    />
                )}
                {greedyResult && (
                    <Bar
                        label="Greedy"
                        value={greedyResult.solve_time_ms}
                        maxValue={chartData.maxSolveTime}
                        color="#06b6d4"
                        unit=" ms"
                    />
                )}
            </div>

            {comparison && (
                <div className="chart-comparison-badges">
                    <div className={`comparison-badge ${comparison.distance_reduction_pct >= 0 ? 'positive' : 'negative'}`}>
                        <span className="badge-icon">{comparison.distance_reduction_pct >= 0 ? '📉' : '📈'}</span>
                        <span className="badge-value">
                            {comparison.distance_reduction_pct >= 0 ? '+' : ''}
                            {comparison.distance_reduction_pct.toFixed(1)}%
                        </span>
                        <span className="badge-label">Distance</span>
                    </div>
                    <div className={`comparison-badge ${comparison.time_reduction_pct >= 0 ? 'positive' : 'negative'}`}>
                        <span className="badge-icon">{comparison.time_reduction_pct >= 0 ? '⏱️' : '⏰'}</span>
                        <span className="badge-value">
                            {comparison.time_reduction_pct >= 0 ? '+' : ''}
                            {comparison.time_reduction_pct.toFixed(1)}%
                        </span>
                        <span className="badge-label">Time Saved</span>
                    </div>
                    {comparison.traffic_time_comparison && (
                        <div className="comparison-badge">
                            <span className="badge-icon">🚦</span>
                            <span className="badge-value">
                                {comparison.traffic_time_comparison.quantum?.toFixed(2) ?? '-'}x / {comparison.traffic_time_comparison.greedy?.toFixed(2) ?? '-'}x
                            </span>
                            <span className="badge-label">Traffic Impact (Q/G)</span>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};
