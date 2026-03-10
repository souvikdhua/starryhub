import express from 'express';
import * as turf from '@turf/turf';

const router = express.Router();

/**
 * Generate a randomized spatial heatmap representing "Crowd Density Anomaly" 
 * or "Traffic Congestion Zones" within New Town bbox.
 */
router.get('/heatmap', (req, res) => {
    try {
        const BBOX = [88.45, 22.56, 88.49, 22.60]; // [minX, minY, maxX, maxY]
        const features = [];

        // Generate 15-25 random hotspots
        const numSpots = Math.floor(Math.random() * 10) + 15;

        for (let i = 0; i < numSpots; i++) {
            // Random point in bbox
            const lon = BBOX[0] + Math.random() * (BBOX[2] - BBOX[0]);
            const lat = BBOX[1] + Math.random() * (BBOX[3] - BBOX[1]);

            // Random intensity (1-10)
            const intensity = Math.floor(Math.random() * 10) + 1;

            features.push(turf.point([lon, lat], {
                weight: intensity,
                type: intensity > 8 ? 'CRITICAL_ANOMALY' : 'ELEVATED_DENSITY'
            }));
        }

        const featureCollection = turf.featureCollection(features);
        res.json(featureCollection);
    } catch (error) {
        console.error("[Analytics] Error:", error);
        res.status(500).json({ error: "Failed to fetch analytics heatmap." });
    }
});

export default router;
