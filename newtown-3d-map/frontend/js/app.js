import MapEngine from './map/MapEngine.js';
import CCTVManager from './cctv/CCTVManager.js';
import StreetViewEngine from './streetview/StreetViewEngine.js';
import AnalyticsEngine from './analytics/AnalyticsEngine.js';

class App {
    constructor() {
        this.config = {
            backendUrl: 'http://localhost:3000/api',
            cesiumIonToken: '', // Provided via proxy or env if needed
            bbox: '22.56,88.45,22.60,88.49' // New Town BBOX approx
        };

        this.mapEngine = new MapEngine('cesiumContainer', this.config);
        this.cctvManager = new CCTVManager(this.mapEngine, this.config);
        this.streetViewEngine = new StreetViewEngine(this.mapEngine, this.config);
        this.analyticsEngine = new AnalyticsEngine(this.mapEngine, this.config);
    }

    async init() {
        console.log("Starting New Town Smart Map Application...");

        // Initialize Core Map
        await this.mapEngine.init();

        // Initialize Subsystems
        await this.cctvManager.init();
        await this.analyticsEngine.init();

        this.bindEvents();
    }

    bindEvents() {
        document.getElementById('btnCalculateRoute').addEventListener('click', () => {
            this.mapEngine.toggleRoutingMode();
        });

        document.getElementById('toggleAnalytics').addEventListener('change', (e) => {
            if (e.target.checked) {
                this.analyticsEngine.showHeatmap();
            } else {
                this.analyticsEngine.hideHeatmap();
            }
        });

        document.getElementById('toggleBuildings').addEventListener('change', (e) => {
            this.mapEngine.toggleBuildings(e.target.checked);
        });

        document.getElementById('toggleCctv').addEventListener('change', (e) => {
            this.cctvManager.toggleMarkers(e.target.checked);
        });

        document.getElementById('btnDayNight').addEventListener('click', () => {
            this.mapEngine.toggleDayNight();
        });

        document.getElementById('btnResetView').addEventListener('click', () => {
            this.mapEngine.flyToNewTown();
        });
    }
}

// Boot application
const app = new App();
app.init();
