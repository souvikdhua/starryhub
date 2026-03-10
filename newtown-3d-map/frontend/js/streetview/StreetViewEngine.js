export default class StreetViewEngine {
    constructor(mapEngine, config) {
        this.mapEngine = mapEngine;
        this.config = config;
        this.bindEvents();
    }

    async activate() {
        console.log("Activating Street View/Detailed Map fallback...");

        // 1. Get current camera position from MapEngine
        const camera = this.mapEngine.viewer.camera;
        const cartographic = Cesium.Cartographic.fromCartesian(camera.positionWC);
        const lat = Cesium.Math.toDegrees(cartographic.latitude);
        const lng = Cesium.Math.toDegrees(cartographic.longitude);

        document.getElementById('streetViewModal').classList.remove('hidden');

        const container = document.getElementById('panoContainer');
        // Since Google Street View requires a Paid API Key, we fallback to a detailed OSM embed
        // showing the exact point instead, since there are no truly keyless embeddable street
        // view solutions (even Mapillary requires API credentials).
        container.innerHTML = `
            <iframe
                width="100%"
                height="100%"
                frameborder="0" style="border:0"
                src="https://www.openstreetmap.org/export/embed.html?bbox=${lng - 0.002},${lat - 0.002},${lng + 0.002},${lat + 0.002}&layer=mapnik&marker=${lat},${lng}"
                allowfullscreen>
            </iframe>
            <div style="position:absolute; bottom: 20px; left: 50%; transform: translateX(-50%); color: white; background:var(--glass-bg); padding:10px 20px; border-radius:12px; border: 1px solid var(--glass-border); text-align:center;">
                <p><strong>Open Source Mode</strong></p>
                <p>Interactive 360° Street View requires paid API credentials.</p>
                <p>Displaying detailed OpenStreetMap local view instead.</p>
                <p style="margin-top:5px; font-family:monospace;">Lat: ${lat.toFixed(5)}, Lng: ${lng.toFixed(5)}</p>
            </div>
        `;
    }

    deactivate() {
        document.getElementById('streetViewModal').classList.add('hidden');
        document.getElementById('panoContainer').innerHTML = ''; // Stop frame
    }

    bindEvents() {
        document.getElementById('btnStreetViewMap').addEventListener('click', () => {
            this.activate();
        });

        document.getElementById('closeStreetView').addEventListener('click', () => {
            this.deactivate();
        });
    }
}
