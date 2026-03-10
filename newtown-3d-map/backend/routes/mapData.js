import express from 'express';
import { fetchOverpassData } from '../services/osmService.js';

const router = express.Router();

// Get raw OSM data for a bounding box
router.get('/osm', async (req, res) => {
    try {
        const { bbox } = req.query; // Expecting e.g. "22.56,88.45,22.60,88.49"
        if (!bbox) return res.status(400).json({ error: 'Bounding box (bbox) required' });

        const data = await fetchOverpassData(bbox);
        res.json(data);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to fetch map data' });
    }
});

export default router;
