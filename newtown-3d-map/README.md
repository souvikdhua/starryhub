# New Town 3D Interactive Map System

A fully functional, real-life 3D interactive map of New Town, Kolkata with simulated CCTV integration, Street View capabilities, and dynamic 3D building rendering based on OpenStreetMap data.

## Features

- **3D Buildings & Terrain:** Live loading of OSM building data extruded into 3D.
- **CCTV Integration:** Dashboard for monitoring (simulated) RTSP/HTTP camera feeds from the map.
- **Street View:** Immersive street-level panoramas integrated using Google Maps API.
- **Real-Time Overlays:** Traffic and weather layers (optional via API keys).

## Architecture

* **Backend:** Node.js/Express, providing a REST API and WebSocket streaming for CCTV, caching data via Redis.
* **Frontend:** Plain HTML/CSS/JS architecture prioritizing performance. Uses **CesiumJS** for powerful 3D globe rendering and handling 3D Tiles and GeoJSON cleanly.

## Setup

1. Copy `.env.example` to `.env` and fill in your API keys. Minimum required: `GOOGLE_MAPS_API_KEY`.
2. Install Backend dependencies:
   ```bash
   cd backend
   npm install
   ```
3. Install Frontend dependencies:
   ```bash
   cd frontend
   npm install
   ```
4. Start development using Docker:
   ```bash
   docker-compose up
   ```
   *Note: Frontend serves at http://localhost:8080, Backend serves at http://localhost:3000*
