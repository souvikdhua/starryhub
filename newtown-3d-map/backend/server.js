import express from 'express';
import http from 'http';
import cors from 'cors';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import { WebSocketServer } from 'ws';
import 'dotenv/config';

// Import Route Handlers
import mapDataRoutes from './routes/mapData.js';
import cctvFeedsRoutes from './routes/cctvFeeds.js';
import buildingsRoutes from './routes/buildings.js';
import streetViewRoutes from './routes/streetView.js';
import trafficRoutes from './routes/traffic.js';
import weatherRoutes from './routes/weather.js';
import routingRoutes from './routes/routing.js';
import analyticsRoutes from './routes/analytics.js';

import { initRoutingEngine } from './services/routingService.js';

// Setup Express application
const app = express();
const server = http.createServer(app);

// Use Middlewares
app.use(cors());
app.use(compression());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(express.static('public'));

// Rate Limiter
const apiLimiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100, // Limit each IP to 100 requests per windowMs
    standardHeaders: true,
    legacyHeaders: false,
});
app.use('/api', apiLimiter);

// API Routes
app.use('/api/map-data', mapDataRoutes);
app.use('/api/cctv', cctvFeedsRoutes);
app.use('/api/buildings', buildingsRoutes);
app.use('/api/street-view', streetViewRoutes);
app.use('/api/traffic', trafficRoutes);
app.use('/api/weather', weatherRoutes);
app.use('/api/routing', routingRoutes);
app.use('/api/analytics', analyticsRoutes);

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ status: 'ok', timestamp: new Date().toISOString() });
});

// Setup WebSocket server for Real-Time CCTV Streaming
const wss = new WebSocketServer({ server });

wss.on('connection', (ws) => {
    console.log('New WebSocket client connected for CCTV streaming');
    // We will hook this up to the CCTV stream manager later
    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

// Start Server
const PORT = process.env.PORT || 3000;
server.listen(PORT, async () => {
    console.log(`[Backend Server] listening on port ${PORT}`);

    // Initialize expensive GIS engines over time
    await initRoutingEngine();
});

export { app, server, wss };
