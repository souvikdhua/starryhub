import Stream from 'node-rtsp-stream';
import { cctvSources } from '../config/cctvSources.js';

const activeStreams = new Map();

export const initCctvStreams = (wss) => {
    console.log('[CCTV Service] Initializing streams...');

    // In a real environment, node-rtsp-stream requires FFmpeg installed on the system
    // It takes an RTSP URL and streams WebSockets using JSMpeg

    /* 
    cctvSources.forEach(source => {
        if (source.status === 'active') {
            try {
                // Determine port dynamically or run on same WS server
                // node-rtsp-stream usually spins up its own WS server per stream on different ports
                // For a unified approach, we would pipe ffmpeg stdout to our existing wss.
                
                // Mock stream status
                console.log(`[CCTV Service] Registered source: ${source.name}`);
            } catch (err) {
                console.error(`[CCTV Service] Failed to init stream for ${source.id}`);
            }
        }
    }); 
    */

    // Simple WS handler for our single WS server (mocking traffic updates for cams)
    wss.on('connection', (ws) => {
        const interval = setInterval(() => {
            if (ws.readyState === ws.OPEN) {
                ws.send(JSON.stringify({
                    type: "cctv_status",
                    timestamp: Date.now(),
                    activeFeeds: cctvSources.length
                }));
            }
        }, 5000);

        ws.on('close', () => clearInterval(interval));
    });
};
