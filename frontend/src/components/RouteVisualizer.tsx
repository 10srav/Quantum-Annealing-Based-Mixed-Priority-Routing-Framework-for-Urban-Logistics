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
    const depotId = result.depot_id;
    const numPriority = priorityIds.size;

    return (
        <div className="route-visualizer">
            <h4>{title}</h4>
            <div className="route-stops">
                {result.route.map((nodeId, index) => {
                    const isDepot = nodeId === depotId;
                    const isPriority = priorityIds.has(nodeId);
                    const node = graph.nodes.find(n => n.id === nodeId);
                    // When depot is present, priority zone starts after depot
                    const priorityZoneStart = depotId ? 1 : 0;
                    const isInPriorityZone = !isDepot && index >= priorityZoneStart && index < priorityZoneStart + numPriority;

                    return (
                        <React.Fragment key={nodeId}>
                            {index > 0 && <span className="route-arrow">→</span>}
                            <div
                                className={`route-stop ${isDepot ? 'depot' : isPriority ? 'priority' : 'normal'} ${isInPriorityZone ? 'in-zone' : ''
                                    }`}
                                title={node?.label || nodeId}
                            >
                                <span className="stop-id">{nodeId}</span>
                                <span className="stop-order">#{index + 1}</span>
                                {isDepot && <span className="depot-badge">D</span>}
                                {!isDepot && isPriority && <span className="priority-badge">P</span>}
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
