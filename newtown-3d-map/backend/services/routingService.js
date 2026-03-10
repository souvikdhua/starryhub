import axios from 'axios';
import createGraph from 'ngraph.graph';
import path from 'ngraph.path';
import * as turf from '@turf/turf';

let roadGraph = null;
let nodeMap = new Map(); // OSM Node ID to coords

// Bounding box for New Town
const BBOX = "22.56,88.45,22.60,88.49";

/**
 * Initializes the routing graph by pulling highway data from OpenStreetMap.
 * Assigns random "traffic congestion" weights to simulate real-world routing.
 */
export const initRoutingEngine = async () => {
    console.log("[Routing] Initializing Emergency Routing Engine...");

    // Fetch roads (highways) within the bounding box
    const query = `
        [out:json][timeout:25];
        way["highway"~"primary|secondary|tertiary|residential"](${BBOX});
        (._;>;);
        out body;
    `;

    try {
        const response = await axios.get('https://overpass-api.de/api/interpreter', {
            params: { data: query }
        });

        const elements = response.data.elements;
        roadGraph = createGraph();

        // 1. Build Node Map
        elements.forEach(el => {
            if (el.type === 'node') {
                nodeMap.set(el.id, [el.lon, el.lat]);
                roadGraph.addNode(el.id, { lon: el.lon, lat: el.lat });
            }
        });

        // 2. Build Edges (Ways) with simulated traffic weights
        elements.forEach(el => {
            if (el.type === 'way' && el.nodes) {
                for (let i = 0; i < el.nodes.length - 1; i++) {
                    const nodeA = el.nodes[i];
                    const nodeB = el.nodes[i + 1];

                    const coordA = nodeMap.get(nodeA);
                    const coordB = nodeMap.get(nodeB);

                    if (coordA && coordB) {
                        const distance = turf.distance(coordA, coordB, { units: 'meters' });
                        // Random congestion weight (1.0 = clear, 5.0 = heavy traffic) 
                        const trafficWeight = 1.0 + (Math.random() * 4);
                        const cost = distance * trafficWeight;

                        roadGraph.addLink(nodeA, nodeB, { weight: cost });
                        roadGraph.addLink(nodeB, nodeA, { weight: cost }); // Assume bidirectional for simplicity
                    }
                }
            }
        });

        console.log(`[Routing] Engine Ready. Nodes: ${roadGraph.getNodesCount()}, Links: ${roadGraph.getLinksCount()}`);
    } catch (error) {
        console.error("[Routing] Failed to initialize map graph:", error.message);
    }
};

/**
 * Finds the closest OSM node to a given coordinate.
 */
const findClosestNode = (lon, lat) => {
    const point = turf.point([lon, lat]);
    let closestId = null;
    let minDistance = Infinity;

    nodeMap.forEach((coords, id) => {
        const dist = turf.distance(point, turf.point(coords), { units: 'meters' });
        if (dist < minDistance) {
            minDistance = dist;
            closestId = id;
        }
    });

    return closestId;
};

/**
 * Calculates optimal path using A*
 */
export const calculateEmergencyRoute = (startLon, startLat, endLon, endLat) => {
    if (!roadGraph) throw new Error("Routing engine not initialized.");

    const startNode = findClosestNode(startLon, startLat);
    const endNode = findClosestNode(endLon, endLat);

    if (!startNode || !endNode) throw new Error("Could not snap coordinates to road network.");

    // Define A* pathfinder with heuristic (Euclidean distance)
    const pathfinder = path.aStar(roadGraph, {
        distance(fromNode, toNode, link) {
            return link.data.weight; // Use simulated traffic cost
        },
        heuristic(fromNode, toNode) {
            // Straight-line distance between nodes
            return turf.distance(
                [fromNode.data.lon, fromNode.data.lat],
                [toNode.data.lon, toNode.data.lat],
                { units: 'meters' }
            );
        }
    });

    const route = pathfinder.find(startNode, endNode);

    if (!route || route.length === 0) return null;

    // Convert route into a GeoJSON LineString
    const coordinates = route.map(n => [n.data.lon, n.data.lat]).reverse();

    return {
        type: "Feature",
        properties: {
            isEmergencyRoute: true,
            totalDistanceMeters: turf.length(turf.lineString(coordinates), { units: 'meters' }).toFixed(2)
        },
        geometry: {
            type: "LineString",
            coordinates: coordinates
        }
    };
};
