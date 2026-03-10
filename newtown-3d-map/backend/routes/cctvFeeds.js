import express from 'express';
import { cctvSources } from '../config/cctvSources.js';

const router = express.Router();

// Get list of available CCTV cameras
router.get('/cameras', (req, res) => {
    res.json({
        total: cctvSources.length,
        cameras: cctvSources
    });
});

// Get specific camera details
router.get('/cameras/:id', (req, res) => {
    const cam = cctvSources.find(c => c.id === req.params.id);
    if (!cam) return res.status(404).json({ error: 'Camera not found' });
    res.json(cam);
});

export default router;
