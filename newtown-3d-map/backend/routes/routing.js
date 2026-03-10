import express from 'express';
import { calculateEmergencyRoute } from '../services/routingService.js';

const router = express.Router();

router.post('/emergency-path', (req, res) => {
    try {
        const { startLon, startLat, endLon, endLat } = req.body;

        if (startLon === undefined || startLat === undefined || endLon === undefined || endLat === undefined) {
            return res.status(400).json({ error: "Start and End coordinates required." });
        }

        const geojsonRoute = calculateEmergencyRoute(startLon, startLat, endLon, endLat);

        if (!geojsonRoute) {
            return res.status(404).json({ error: "No navigable route found." });
        }

        res.json(geojsonRoute);
    } catch (error) {
        console.error("[Routing Endpoint Error]", error);
        res.status(500).json({ error: "Failed to calculate highly efficient route." });
    }
});

export default router;
