/**
 * RouteVisualizer - Displays route details with priority highlighting
 */

import React from 'react';
import type { CityGraph, SolverResponse } from '../lib/types';

interface RouteVisualizerProps {
    graph: CityGraph | null;
    result: SolverResponse | null;
    title: string;
}

export const RouteVisualizer: React.FC<RouteVisualizerProps> = ({
    graph,
    result,
    title,
}) => {
    if (!result || !graph) {
        return null;
    }

    const priorityIds = new Set(
        graph.nodes.filter(n => n.type === 'priority').map(n => n.id)
    );
    const numPriority = priorityIds.size;

    return (
        <div className="route-visualizer">
            <h4>{title}</h4>
            <div className="route-stops">
                {result.route.map((nodeId, index) => {
                    const isPriority = priorityIds.has(nodeId);
                    const node = graph.nodes.find(n => n.id === nodeId);
                    const isInPriorityZone = index < numPriority;

                    return (
                        <React.Fragment key={nodeId}>
                            {index > 0 && <span className="route-arrow">→</span>}
                            <div
                                className={`route-stop ${isPriority ? 'priority' : 'normal'} ${isInPriorityZone ? 'in-zone' : ''
                                    }`}
                                title={node?.label || nodeId}
                            >
                                <span className="stop-id">{nodeId}</span>
                                <span className="stop-order">#{index + 1}</span>
                                {isPriority && <span className="priority-badge">P</span>}
                            </div>
                        </React.Fragment>
                    );
                })}
            </div>

            <div className="route-stats">
                <div className="stat">
                    <span className="stat-label">Total Stops</span>
                    <span className="stat-value">{result.route.length}</span>
                </div>
                <div className="stat">
                    <span className="stat-label">Priority First</span>
                    <span className={`stat-value ${result.priority_satisfied ? 'ok' : 'fail'}`}>
                        {result.priority_satisfied ? 'Yes ✓' : 'No ✗'}
                    </span>
                </div>
                <div className="stat">
                    <span className="stat-label">Solver</span>
                    <span className="stat-value">{result.solver_used}</span>
                </div>
            </div>
        </div>
    );
};
