import axios from 'axios';
import fs from 'fs/promises';
import path from 'path';
import { overpassUrl } from '../config/apiKeys.js';
import { getRedisClient } from '../config/database.js';

const DATA_DIR = path.join(process.cwd(), 'data');

/**
 * Fetch data from Overpass API
 * @param {string} bbox "minLat,minLon,maxLat,maxLon" - Overpass uses this format
 */
export const fetchOverpassData = async (bbox = "22.56,88.45,22.60,88.49") => {
    const cacheKey = `osm_data_${bbox}`;
    const redis = getRedisClient();

    // 1. Try Redis
    if (redis) {
        const cached = await redis.get(cacheKey);
        if (cached) return JSON.parse(cached);
    }

    // 2. Try local file fallback (good for dev)
    const filePath = path.join(DATA_DIR, 'newtown-osm-cache.json');
    try {
        const fileData = await fs.readFile(filePath, 'utf8');
        console.log('[OSM Service] Serving from local file cache');
        return JSON.parse(fileData);
    } catch (e) {
        // File doesn't exist, proceed to fetch
    }

    console.log('[OSM Service] Fetching from Overpass API...');

    // Convert generic lon,lat to lat,lon for Overpass
    // standard bbox is usually minLon,minLat,maxLon,maxLat
    // Overpass expects minLat,minLon,maxLat,maxLon

    const query = `
        [out:json][timeout:30];
        (
          way["building"](${bbox});
          relation["building"](${bbox});
          way["highway"](${bbox});
          node["amenity"](${bbox});
          way["landuse"](${bbox});
          way["natural"](${bbox});
          way["water"](${bbox});
          way["leisure"](${bbox});
        );
        out body;
        >;
        out skel qt;
    `;

    try {
        const response = await axios.post(overpassUrl, `data=${encodeURIComponent(query)}`, {
            headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });

        // Save to Redis and File
        if (redis) await redis.setEx(cacheKey, 86400, JSON.stringify(response.data)); // 24h cache

        await fs.mkdir(DATA_DIR, { recursive: true });
        await fs.writeFile(filePath, JSON.stringify(response.data));

        return response.data;
    } catch (error) {
        console.error('[OSM Service] Error fetching from Overpass', error.message);
        throw error;
    }
};
