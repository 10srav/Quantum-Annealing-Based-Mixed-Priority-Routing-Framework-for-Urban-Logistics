/**
 * MapView - Interactive graph visualization component
 */

import React, { useMemo } from 'react';
import type { CityGraph } from '../lib/types';
import { NODE_COLORS, TRAFFIC_COLORS } from '../lib/config';

interface MapViewProps {
    graph: CityGraph | null;
    route?: string[];
    highlightRoute?: boolean;
}

const SCALE = 60;
const PADDING = 40;

export const MapView: React.FC<MapViewProps> = ({ graph, route = [], highlightRoute = false }) => {
    const { width, height, scaledNodes, edges } = useMemo(() => {
        if (!graph) {
            return { width: 400, height: 300, scaledNodes: [], edges: [] };
        }

        const maxX = Math.max(...graph.nodes.map(n => n.x));
        const maxY = Math.max(...graph.nodes.map(n => n.y));

        const w = maxX * SCALE + PADDING * 2;
        const h = maxY * SCALE + PADDING * 2;

        const scaled = graph.nodes.map(n => ({
            ...n,
            cx: n.x * SCALE + PADDING,
            cy: h - (n.y * SCALE + PADDING), // Flip Y axis
        }));

        const nodeMap = new Map(scaled.map(n => [n.id, n]));

        const e = graph.edges.map(edge => ({
            ...edge,
            from_node: nodeMap.get(edge.from),
            to_node: nodeMap.get(edge.to),
        }));

        return { width: Math.max(w, 400), height: Math.max(h, 300), scaledNodes: scaled, edges: e };
    }, [graph]);

    const routeSet = useMemo(() => new Set(route), [route]);

    const routeEdges = useMemo(() => {
        if (!highlightRoute || route.length < 2) return [];

        const result = [];
        for (let i = 0; i < route.length - 1; i++) {
            result.push({ from: route[i], to: route[i + 1], order: i + 1 });
        }
        return result;
    }, [route, highlightRoute]);

    if (!graph) {
        return (
            <div className="map-view map-view--empty">
                <p>No graph loaded. Generate a city or load a sample.</p>
            </div>
        );
    }

    return (
        <div className="map-view">
            <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
                {/* Background */}
                <rect width={width} height={height} fill="#1a1a2e" rx="8" />

                {/* Edges */}
                {edges.map((edge, i) => {
                    if (!edge.from_node || !edge.to_node) return null;

                    const isInRoute = highlightRoute && routeEdges.some(
                        re => (re.from === edge.from && re.to === edge.to) ||
                            (re.from === edge.to && re.to === edge.from)
                    );

                    return (
                        <line
                            key={i}
                            x1={edge.from_node.cx}
                            y1={edge.from_node.cy}
                            x2={edge.to_node.cx}
                            y2={edge.to_node.cy}
                            stroke={isInRoute ? '#10b981' : TRAFFIC_COLORS[edge.traffic]}
                            strokeWidth={isInRoute ? 3 : 1.5}
                            strokeOpacity={isInRoute ? 1 : 0.5}
                        />
                    );
                })}

                {/* Route arrows */}
                {highlightRoute && routeEdges.map((re, i) => {
                    const fromNode = scaledNodes.find(n => n.id === re.from);
                    const toNode = scaledNodes.find(n => n.id === re.to);
                    if (!fromNode || !toNode) return null;

                    const midX = (fromNode.cx + toNode.cx) / 2;
                    const midY = (fromNode.cy + toNode.cy) / 2;

                    return (
                        <g key={`route-${i}`}>
                            <circle cx={midX} cy={midY} r="10" fill="#10b981" />
                            <text
                                x={midX}
                                y={midY + 4}
                                textAnchor="middle"
                                fill="white"
                                fontSize="10"
                                fontWeight="bold"
                            >
                                {re.order}
                            </text>
                        </g>
                    );
                })}

                {/* Nodes */}
                {scaledNodes.map(node => {
                    const isInRoute = routeSet.has(node.id);
                    const routePosition = route.indexOf(node.id) + 1;

                    return (
                        <g key={node.id}>
                            <circle
                                cx={node.cx}
                                cy={node.cy}
                                r={isInRoute ? 18 : 15}
                                fill={NODE_COLORS[node.type]}
                                stroke={isInRoute ? '#10b981' : 'white'}
                                strokeWidth={isInRoute ? 3 : 2}
                            />
                            <text
                                x={node.cx}
                                y={node.cy + 4}
                                textAnchor="middle"
                                fill="white"
                                fontSize="10"
                                fontWeight="bold"
                            >
                                {node.id.replace('N', '')}
                            </text>
                            {isInRoute && routePosition > 0 && (
                                <text
                                    x={node.cx + 20}
                                    y={node.cy - 10}
                                    fill="#10b981"
                                    fontSize="12"
                                    fontWeight="bold"
                                >
                                    #{routePosition}
                                </text>
                            )}
                        </g>
                    );
                })}
            </svg>

            <div className="map-legend">
                <div className="legend-item">
                    <span className="legend-dot legend-dot--priority"></span>
                    Priority
                </div>
                <div className="legend-item">
                    <span className="legend-dot legend-dot--normal"></span>
                    Normal
                </div>
                <div className="legend-item">
                    <span className="legend-line legend-line--low"></span>
                    Low Traffic
                </div>
                <div className="legend-item">
                    <span className="legend-line legend-line--medium"></span>
                    Medium
                </div>
                <div className="legend-item">
                    <span className="legend-line legend-line--high"></span>
                    High
                </div>
            </div>
        </div>
    );
};
