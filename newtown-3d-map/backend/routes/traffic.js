import express from 'express';
import { apiKeys } from '../config/apiKeys.js';
import axios from 'axios';

const router = express.Router();

// Proxy for live traffic flow data
router.get('/flow', async (req, res) => {
    try {
        const { bbox, zoom } = req.query; // Format: "minLon,minLat,maxLon,maxLat"

        if (!apiKeys.tomtom) {
            // Return simulated traffic flow if no api key
            return res.json({
                status: "simulated",
                flow: [
                    { speed: 15, delay: 120, road: "Biswa Bangla Sarani" }
                ]
            });
        }

        res.json({ message: "Traffic data proxy not fully implemented yet." });
    } catch (error) {
        res.status(500).json({ error: 'Failed to fetch traffic data' });
    }
});

export default router;
