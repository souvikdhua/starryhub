import express from 'express';
import { fetchOverpassData } from '../services/osmService.js';
import { processBuildingData } from '../services/buildingExtruder.js';

const router = express.Router();

// Get processed 3D building data
router.get('/3d', async (req, res) => {
    try {
        const { bbox } = req.query;
        if (!bbox) return res.status(400).json({ error: 'Bounding box (bbox) required' });

        const rawData = await fetchOverpassData(bbox);
        const processed3D = processBuildingData(rawData);

        res.json(processed3D);
    } catch (error) {
        console.error(error);
        res.status(500).json({ error: 'Failed to process building data' });
    }
});

export default router;
