/**
 * Interactive OSM Map - Click to add points, set priorities
 * Uses OSRM for real road routing
 */

import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap, useMapEvents } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import 'leaflet-routing-machine';
import 'leaflet-routing-machine/dist/leaflet-routing-machine.css';
import type { CityGraph, Node, Edge } from '../lib/types';

// Fix for default marker icons
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons
const createIcon = (type: 'priority' | 'normal' | 'depot', label: string, isInRoute: boolean = false) => {
    const colorMap: Record<string, string> = { priority: '#ef4444', normal: '#3b82f6', depot: '#f59e0b' };
    const color = colorMap[type] || '#3b82f6';
    const isDepot = type === 'depot';
    const size = isDepot ? 44 : isInRoute ? 40 : 32;
    const borderRadius = isDepot ? '6px' : '50%';
    return new L.DivIcon({
        className: 'custom-div-icon',
        html: `
            <div style="
                width: ${size}px;
                height: ${size}px;
                background: ${color};
                border-radius: ${borderRadius};
                border: 3px solid ${isInRoute ? '#10b981' : 'white'};
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: bold;
                font-size: ${isDepot ? '16px' : isInRoute ? '14px' : '12px'};
                box-shadow: 0 2px 8px rgba(0,0,0,0.3);
                cursor: pointer;
            ">${isDepot ? 'D' : label}</div>
        `,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
    });
};

interface InteractiveMapProps {
    graph: CityGraph | null;
    route?: string[];
    highlightRoute?: boolean;
    onGraphChange?: (graph: CityGraph) => void;
    editable?: boolean;
}

// City centers
const CITY_CENTERS: Record<string, [number, number]> = {
    'hyderabad': [17.3850, 78.4867],
    'bangalore': [12.9716, 77.5946],
    'mumbai': [19.0760, 72.8777],
    'delhi': [28.6139, 77.2090],
    'default': [17.3850, 78.4867],
};

// Click handler component
const MapClickHandler: React.FC<{
    onMapClick: (latlng: L.LatLng) => void;
    enabled: boolean;
}> = ({ onMapClick, enabled }) => {
    useMapEvents({
        click: (e) => {
            if (enabled) {
                onMapClick(e.latlng);
            }
        },
    });
    return null;
};

// Auto fit bounds
const FitBounds: React.FC<{ bounds: L.LatLngBounds | null }> = ({ bounds }) => {
    const map = useMap();
    useEffect(() => {
        if (bounds && bounds.isValid()) {
            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 15 });
        }
    }, [map, bounds]);
    return null;
};

// OSRM Routing component - fetches real road routes
const OSRMRoute: React.FC<{
    waypoints: [number, number][];
    color?: string;
}> = ({ waypoints, color = '#10b981' }) => {
    useMap();
    const [routeCoords, setRouteCoords] = useState<[number, number][]>([]);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (waypoints.length < 2) {
            setRouteCoords([]);
            return;
        }

        // Use OSRM API directly for cleaner integration
        let cancelled = false;
        const fetchRoute = async () => {
            setLoading(true);

            try {
                // Build OSRM URL - coordinates are lng,lat format
                const coords = waypoints.map(wp => `${wp[1]},${wp[0]}`).join(';');
                const url = `https://router.project-osrm.org/route/v1/driving/${coords}?overview=full&geometries=geojson`;

                const response = await fetch(url);
                const data = await response.json();

                if (cancelled) return;

                if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
                    // OSRM returns coordinates as [lng, lat], we need [lat, lng] for Leaflet
                    const coordinates = data.routes[0].geometry.coordinates.map(
                        (coord: [number, number]) => [coord[1], coord[0]] as [number, number]
                    );
                    setRouteCoords(coordinates);
                } else {
                    // Fallback to straight lines
                    setRouteCoords(waypoints);
                }
            } catch (err) {
                if (cancelled) return;
                console.error('OSRM routing error:', err);
                // Fallback to straight lines
                setRouteCoords(waypoints);
            } finally {
                if (!cancelled) setLoading(false);
            }
        };

        fetchRoute();

        return () => { cancelled = true; };
    }, [waypoints]);

    if (routeCoords.length < 2) return null;

    return (
        <>
            <Polyline
                positions={routeCoords}
                color={color}
                weight={5}
                opacity={0.8}
            />
            {/* Route direction arrows */}
            {routeCoords.length > 10 && (
                <Polyline
                    positions={routeCoords}
                    color={color}
                    weight={5}
                    opacity={0.8}
                    dashArray="15, 20"
                />
            )}
            {loading && (
                <div style={{
                    position: 'absolute',
                    top: 10,
                    right: 10,
                    background: 'rgba(0,0,0,0.7)',
                    color: 'white',
                    padding: '5px 10px',
                    borderRadius: 4,
                    zIndex: 1000,
                }}>
                    Loading route...
                </div>
            )}
        </>
    );
};

export const InteractiveMap: React.FC<InteractiveMapProps> = ({
    graph,
    route = [],
    highlightRoute = false,
    onGraphChange,
    editable = true,
}) => {
    const [nodes, setNodes] = useState<Node[]>(graph?.nodes || []);
    const [edges, setEdges] = useState<Edge[]>(graph?.edges || []);
    const [selectedNodeType, setSelectedNodeType] = useState<'priority' | 'normal' | 'depot'>('priority');
    const [editMode, setEditMode] = useState<'add' | 'select' | 'delete'>('add');
    const [showRoadRoutes, setShowRoadRoutes] = useState(true);
    const cityCenter = CITY_CENTERS.hyderabad;

    // Sync with external graph changes (intentional prop-to-state sync for editable local copy)
    /* eslint-disable react-hooks/set-state-in-effect */
    useEffect(() => {
        if (graph) {
            setNodes(graph.nodes);
            setEdges(graph.edges);
        }
    }, [graph]);
    /* eslint-enable react-hooks/set-state-in-effect */

    // Convert lat/lng to x/y coordinates
    const latLngToXY = useCallback((lat: number, lng: number): { x: number; y: number } => {
        const x = Math.round(((lng - cityCenter[1]) / 0.01 + 5) * 10) / 10;
        const y = Math.round(((lat - cityCenter[0]) / 0.01 + 5) * 10) / 10;
        return { x: Math.max(0, x), y: Math.max(0, y) };
    }, [cityCenter]);

    // Convert x/y to lat/lng
    const xyToLatLng = useCallback((x: number, y: number): [number, number] => {
        return [
            cityCenter[0] + (y - 5) * 0.01,
            cityCenter[1] + (x - 5) * 0.01
        ];
    }, [cityCenter]);

    // Calculate distance between two nodes
    const calculateDistance = (n1: Node, n2: Node): number => {
        return Math.sqrt(Math.pow(n2.x - n1.x, 2) + Math.pow(n2.y - n1.y, 2));
    };

    // Add new node on map click
    const hasDepot = nodes.some(n => n.type === 'depot');

    const handleMapClick = useCallback((latlng: L.LatLng) => {
        if (editMode !== 'add') return;

        // Prevent adding a second depot
        const depotExists = nodes.some(n => n.type === 'depot');
        if (selectedNodeType === 'depot' && depotExists) return;

        const { x, y } = latLngToXY(latlng.lat, latlng.lng);
        const isDepot = selectedNodeType === 'depot';
        const newId = isDepot ? 'D0' : `N${nodes.length + 1}`;

        const newNode: Node = {
            id: newId,
            x,
            y,
            type: selectedNodeType,
            label: isDepot ? 'Depot' : newId,
        };

        // Auto-connect to nearby nodes (within distance of 3)
        const newEdges: Edge[] = [];
        const trafficLevels: Array<'low' | 'medium' | 'high'> = ['low', 'medium', 'high'];

        nodes.forEach(existingNode => {
            const dist = calculateDistance(newNode, existingNode);
            if (dist < 4) { // Connect if within range
                newEdges.push({
                    from: existingNode.id,
                    to: newId,
                    distance: Math.round(dist * 100) / 100,
                    traffic: trafficLevels[Math.floor(Math.random() * 3)],
                });
            }
        });

        const updatedNodes = [...nodes, newNode];
        const updatedEdges = [...edges, ...newEdges];

        setNodes(updatedNodes);
        setEdges(updatedEdges);

        // Notify parent
        if (onGraphChange) {
            onGraphChange({
                nodes: updatedNodes,
                edges: updatedEdges,
                traffic_multipliers: { low: 1.0, medium: 1.5, high: 2.0 }
            });
        }
    }, [editMode, nodes, edges, selectedNodeType, latLngToXY, onGraphChange]);

    // Toggle node type
    const handleNodeClick = useCallback((nodeId: string) => {
        if (editMode === 'select') {
            const depotExists = nodes.some(n => n.type === 'depot');
            const cycleType = (current: string): 'priority' | 'normal' | 'depot' => {
                if (current === 'priority') return 'normal';
                if (current === 'normal' && !depotExists) return 'depot';
                return 'priority';
            };
            const updatedNodes = nodes.map(n =>
                n.id === nodeId
                    ? { ...n, type: cycleType(n.type) } as Node
                    : n
            );
            setNodes(updatedNodes);

            if (onGraphChange) {
                onGraphChange({
                    nodes: updatedNodes,
                    edges,
                    traffic_multipliers: { low: 1.0, medium: 1.5, high: 2.0 }
                });
            }
        } else if (editMode === 'delete') {
            const updatedNodes = nodes.filter(n => n.id !== nodeId);
            const updatedEdges = edges.filter(e => e.from !== nodeId && e.to !== nodeId);
            setNodes(updatedNodes);
            setEdges(updatedEdges);

            if (onGraphChange) {
                onGraphChange({
                    nodes: updatedNodes,
                    edges: updatedEdges,
                    traffic_multipliers: { low: 1.0, medium: 1.5, high: 2.0 }
                });
            }
        }
    }, [editMode, nodes, edges, onGraphChange]);

    // Clear all nodes
    const handleClearAll = () => {
        setNodes([]);
        setEdges([]);
        if (onGraphChange) {
            onGraphChange({
                nodes: [],
                edges: [],
                traffic_multipliers: { low: 1.0, medium: 1.5, high: 2.0 }
            });
        }
    };

    // Compute positions and bounds
    const { nodePositions, bounds } = useMemo(() => {
        const positions = new Map<string, [number, number]>();
        nodes.forEach(node => {
            positions.set(node.id, xyToLatLng(node.x, node.y));
        });

        if (positions.size > 0) {
            const latLngs = Array.from(positions.values()).map(p => L.latLng(p[0], p[1]));
            return { nodePositions: positions, bounds: L.latLngBounds(latLngs) };
        }
        return { nodePositions: positions, bounds: null };
    }, [nodes, xyToLatLng]);

    // Edge lines (keep as straight lines for graph visualization)
    const edgeLines = useMemo(() => {
        return edges.map(edge => {
            const from = nodePositions.get(edge.from);
            const to = nodePositions.get(edge.to);
            if (!from || !to) return null;

            const color = edge.traffic === 'low' ? '#22c55e' :
                edge.traffic === 'medium' ? '#f59e0b' : '#ef4444';

            return { from, to, color };
        }).filter(Boolean);
    }, [edges, nodePositions]);

    // Route waypoints for OSRM
    const routeWaypoints = useMemo(() => {
        if (!highlightRoute || route.length === 0) return [];
        return route.map(nodeId => nodePositions.get(nodeId)).filter(Boolean) as [number, number][];
    }, [route, highlightRoute, nodePositions]);

    return (
        <div className="interactive-map-container">
            {editable && (
                <div className="map-toolbar">
                    <div className="toolbar-group">
                        <span className="toolbar-label">Mode:</span>
                        <button
                            className={`toolbar-btn ${editMode === 'add' ? 'active' : ''}`}
                            onClick={() => setEditMode('add')}
                            title="Click on map to add nodes"
                        >
                            ➕ Add
                        </button>
                        <button
                            className={`toolbar-btn ${editMode === 'select' ? 'active' : ''}`}
                            onClick={() => setEditMode('select')}
                            title="Click nodes to toggle priority"
                        >
                            🔄 Toggle Priority
                        </button>
                        <button
                            className={`toolbar-btn ${editMode === 'delete' ? 'active' : ''}`}
                            onClick={() => setEditMode('delete')}
                            title="Click nodes to delete"
                        >
                            🗑️ Delete
                        </button>
                    </div>

                    {editMode === 'add' && (
                        <div className="toolbar-group">
                            <span className="toolbar-label">Add as:</span>
                            <button
                                className={`toolbar-btn type-btn priority ${selectedNodeType === 'priority' ? 'active' : ''}`}
                                onClick={() => setSelectedNodeType('priority')}
                            >
                                🔴 Priority
                            </button>
                            <button
                                className={`toolbar-btn type-btn normal ${selectedNodeType === 'normal' ? 'active' : ''}`}
                                onClick={() => setSelectedNodeType('normal')}
                            >
                                🔵 Normal
                            </button>
                            <button
                                className={`toolbar-btn type-btn depot ${selectedNodeType === 'depot' ? 'active' : ''}`}
                                onClick={() => setSelectedNodeType('depot')}
                                disabled={hasDepot}
                                title={hasDepot ? 'Only one depot allowed' : 'Add depot/warehouse starting point'}
                            >
                                🟠 Depot
                            </button>
                        </div>
                    )}

                    <div className="toolbar-group">
                        <button
                            className={`toolbar-btn ${showRoadRoutes ? 'active' : ''}`}
                            onClick={() => setShowRoadRoutes(!showRoadRoutes)}
                            title="Toggle real road routing"
                        >
                            🛣️ Road Routes
                        </button>
                    </div>

                    <button className="toolbar-btn danger" onClick={handleClearAll}>
                        🧹 Clear All
                    </button>
                </div>
            )}

            <div className="map-info">
                <span>📍 {nodes.length} nodes</span>
                <span>🔴 {nodes.filter(n => n.type === 'priority').length} priority</span>
                <span>🔵 {nodes.filter(n => n.type === 'normal').length} normal</span>
                {hasDepot && <span>🟠 1 depot</span>}
                <span>🔗 {edges.length} connections</span>
                {showRoadRoutes && routeWaypoints.length > 1 && (
                    <span>🛣️ Real roads</span>
                )}
            </div>

            <MapContainer
                center={cityCenter}
                zoom={14}
                style={{ height: '600px', width: '100%' }}
                scrollWheelZoom={true}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <MapClickHandler onMapClick={handleMapClick} enabled={editMode === 'add'} />
                <FitBounds bounds={bounds} />

                {/* Edge lines (graph connections) */}
                {edgeLines.map((edge, i) => edge && (
                    <Polyline
                        key={`edge-${i}`}
                        positions={[edge.from, edge.to]}
                        color={edge.color}
                        weight={2}
                        opacity={0.4}
                        dashArray="5, 5"
                    />
                ))}

                {/* Route path - use OSRM for real roads or straight lines */}
                {routeWaypoints.length > 1 && (
                    showRoadRoutes ? (
                        <OSRMRoute waypoints={routeWaypoints} color="#10b981" />
                    ) : (
                        <Polyline
                            positions={routeWaypoints}
                            color="#10b981"
                            weight={4}
                            opacity={0.9}
                        />
                    )
                )}

                {/* Node markers */}
                {nodes.map((node, idx) => {
                    const pos = nodePositions.get(node.id);
                    if (!pos) return null;

                    const routeIdx = route.indexOf(node.id);
                    const isInRoute = routeIdx >= 0;
                    const label = isInRoute ? `${routeIdx + 1}` : `${idx + 1}`;

                    const typeLabel = node.type === 'depot' ? '🟠 Depot' : node.type === 'priority' ? '🔴 Priority' : '🔵 Normal';

                    return (
                        <Marker
                            key={node.id}
                            position={pos}
                            icon={createIcon(node.type as 'priority' | 'normal' | 'depot', label, isInRoute)}
                            eventHandlers={{
                                click: () => handleNodeClick(node.id),
                            }}
                        >
                            <Popup>
                                <div style={{ textAlign: 'center' }}>
                                    <strong>{node.id}</strong><br />
                                    Type: {typeLabel}<br />
                                    Position: ({node.x.toFixed(1)}, {node.y.toFixed(1)})
                                    {isInRoute && <><br />Route #: {routeIdx + 1}</>}
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>

            <div className="map-legend">
                <div className="legend-item"><span className="legend-dot priority"></span> Priority (visit first)</div>
                <div className="legend-item"><span className="legend-dot normal"></span> Normal</div>
                <div className="legend-item"><span className="legend-dot" style={{background: '#f59e0b'}}></span> Depot (start)</div>
                <div className="legend-item"><span className="legend-line low"></span> Low traffic</div>
                <div className="legend-item"><span className="legend-line medium"></span> Medium traffic</div>
                <div className="legend-item"><span className="legend-line high"></span> High traffic</div>
                {showRoadRoutes && <div className="legend-item"><span className="legend-line" style={{background: '#10b981'}}></span> OSRM Road Route</div>}
            </div>
        </div>
    );
};
