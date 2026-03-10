import express from 'express';
import { apiKeys } from '../config/apiKeys.js';
import axios from 'axios';

const router = express.Router();

// Proxy to Google Street View Static API to avoid exposing key on frontend
// Or to get metadata about a location
router.get('/metadata', async (req, res) => {
    try {
        const { lat, lon } = req.query;
        if (!lat || !lon) return res.status(400).json({ error: 'Lat and lon required' });

        if (!apiKeys.googleMaps) {
            return res.status(503).json({ error: 'Google Maps API key not configured' });
        }

        const url = `https://maps.googleapis.com/maps/api/streetview/metadata?location=${lat},${lon}&key=${apiKeys.googleMaps}`;
        const response = await axios.get(url);

        res.json(response.data);
    } catch (error) {
        console.error('Street View API Error:', error.message);
        res.status(500).json({ error: 'Failed to fetch Street View data' });
    }
});

export default router;
