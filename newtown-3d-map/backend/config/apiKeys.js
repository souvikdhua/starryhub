import dotenv from 'dotenv';
dotenv.config();

export const apiKeys = {
    googleMaps: process.env.GOOGLE_MAPS_API_KEY || '',
    tomtom: process.env.TRAFFIC_API_KEY || '',
    openWeatherMap: process.env.OPENWEATHERMAP_API_KEY || '',
    cesiumIon: process.env.CESIUM_ION_TOKEN || '',
};

export const overpassUrl = 'https://overpass-api.de/api/interpreter';
