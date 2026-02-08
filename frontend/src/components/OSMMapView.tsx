/**
 * OSM Map View - Real map visualization using OpenStreetMap
 */

import React, { useMemo, useEffect } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import type { CityGraph } from '../lib/types';

// Fix for default marker icons in React-Leaflet
// eslint-disable-next-line @typescript-eslint/no-explicit-any
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom marker icons
const priorityIcon = new L.DivIcon({
    className: 'custom-marker priority-marker',
    html: '<div class="marker-pin priority"><span>P</span></div>',
    iconSize: [30, 42],
    iconAnchor: [15, 42],
    popupAnchor: [0, -42],
});

const normalIcon = new L.DivIcon({
    className: 'custom-marker normal-marker',
    html: '<div class="marker-pin normal"><span>N</span></div>',
    iconSize: [30, 42],
    iconAnchor: [15, 42],
    popupAnchor: [0, -42],
});

const routeStopIcon = (index: number, isPriority: boolean) => new L.DivIcon({
    className: 'custom-marker route-marker',
    html: `<div class="marker-pin ${isPriority ? 'priority' : 'normal'} route-active"><span>${index + 1}</span></div>`,
    iconSize: [36, 48],
    iconAnchor: [18, 48],
    popupAnchor: [0, -48],
});

interface OSMMapViewProps {
    graph: CityGraph | null;
    route?: string[];
    highlightRoute?: boolean;
    centerCity?: string; // City name for centering
}

// Component to auto-fit bounds
const FitBounds: React.FC<{ bounds: L.LatLngBoundsExpression | null }> = ({ bounds }) => {
    const map = useMap();
    useEffect(() => {
        if (bounds) {
            map.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [map, bounds]);
    return null;
};

// Sample city coordinates for realistic demos
const CITY_CENTERS: Record<string, [number, number]> = {
    'hyderabad': [17.3850, 78.4867],
    'bangalore': [12.9716, 77.5946],
    'mumbai': [19.0760, 72.8777],
    'delhi': [28.6139, 77.2090],
    'chennai': [13.0827, 80.2707],
    'default': [17.3850, 78.4867], // Hyderabad as default
};

// Convert graph coordinates to lat/lng
const graphToLatLng = (
    x: number,
    y: number,
    cityCenter: [number, number],
    scale: number = 0.01 // ~1km per unit
): [number, number] => {
    return [
        cityCenter[0] + (y - 5) * scale,
        cityCenter[1] + (x - 5) * scale
    ];
};

export const OSMMapView: React.FC<OSMMapViewProps> = ({
    graph,
    route = [],
    highlightRoute = false,
    centerCity = 'hyderabad'
}) => {
    const cityCenter = CITY_CENTERS[centerCity.toLowerCase()] || CITY_CENTERS.default;

    const { markers, routePath, bounds } = useMemo(() => {
        if (!graph) {
            return { markers: [], routePath: [], bounds: null };
        }

        // Convert nodes to lat/lng
        const nodePositions = new Map<string, [number, number]>();
        const markerList: Array<{
            id: string;
            position: [number, number];
            type: string;
            label: string;
            routeIndex: number;
        }> = [];

        graph.nodes.forEach(node => {
            const pos = graphToLatLng(node.x, node.y, cityCenter);
            nodePositions.set(node.id, pos);

            const routeIdx = route.indexOf(node.id);
            markerList.push({
                id: node.id,
                position: pos,
                type: node.type,
                label: node.label || node.id,
                routeIndex: routeIdx,
            });
        });

        // Build route path
        const path: [number, number][] = [];
        if (highlightRoute && route.length > 0) {
            route.forEach(nodeId => {
                const pos = nodePositions.get(nodeId);
                if (pos) path.push(pos);
            });
        }

        // Calculate bounds
        const positions = Array.from(nodePositions.values());
        const latLngBounds = positions.length > 0
            ? L.latLngBounds(positions.map(p => L.latLng(p[0], p[1])))
            : null;

        return { markers: markerList, routePath: path, bounds: latLngBounds };
    }, [graph, route, highlightRoute, cityCenter]);

    // Edge lines
    const edgeLines = useMemo(() => {
        if (!graph) return [];

        const nodePositions = new Map<string, [number, number]>();
        graph.nodes.forEach(node => {
            nodePositions.set(node.id, graphToLatLng(node.x, node.y, cityCenter));
        });

        return graph.edges.map(edge => {
            const from = nodePositions.get(edge.from);
            const to = nodePositions.get(edge.to);
            if (!from || !to) return null;

            const color = edge.traffic === 'low' ? '#22c55e' :
                edge.traffic === 'medium' ? '#eab308' : '#ef4444';

            return {
                positions: [from, to] as [number, number][],
                color,
                weight: 2,
                opacity: 0.4,
            };
        }).filter(Boolean);
    }, [graph, cityCenter]);

    if (!graph) {
        return (
            <div className="osm-map osm-map--empty">
                <p>No graph loaded. Generate a city to see the map.</p>
            </div>
        );
    }

    return (
        <div className="osm-map">
            <MapContainer
                center={cityCenter}
                zoom={14}
                style={{ height: '100%', width: '100%', minHeight: '600px' }}
                scrollWheelZoom={true}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                />

                <FitBounds bounds={bounds} />

                {/* Road edges */}
                {edgeLines.map((edge, i) => edge && (
                    <Polyline
                        key={`edge-${i}`}
                        positions={edge.positions}
                        color={edge.color}
                        weight={edge.weight}
                        opacity={edge.opacity}
                        dashArray="5, 10"
                    />
                ))}

                {/* Route path */}
                {highlightRoute && routePath.length > 1 && (
                    <Polyline
                        positions={routePath}
                        color="#10b981"
                        weight={5}
                        opacity={0.9}
                    />
                )}

                {/* Markers */}
                {markers.map(marker => {
                    const isInRoute = marker.routeIndex >= 0;
                    const icon = isInRoute
                        ? routeStopIcon(marker.routeIndex, marker.type === 'priority')
                        : (marker.type === 'priority' ? priorityIcon : normalIcon);

                    return (
                        <Marker
                            key={marker.id}
                            position={marker.position}
                            icon={icon}
                        >
                            <Popup>
                                <div className="marker-popup">
                                    <strong>{marker.label}</strong>
                                    <br />
                                    Type: {marker.type === 'priority' ? '🔴 Priority' : '🔵 Normal'}
                                    {isInRoute && (
                                        <>
                                            <br />
                                            Route Position: #{marker.routeIndex + 1}
                                        </>
                                    )}
                                </div>
                            </Popup>
                        </Marker>
                    );
                })}
            </MapContainer>

            <div className="map-legend osm-legend">
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
