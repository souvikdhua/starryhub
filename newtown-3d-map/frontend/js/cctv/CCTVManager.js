export default class CCTVManager {
    constructor(mapEngine, config) {
        this.mapEngine = mapEngine;
        this.config = config;
        this.cameras = [];
        this.markers = [];
        this.isVisible = true;
    }

    async init() {
        try {
            console.log("Loading CCTV cameras from backend...");
            const res = await fetch(`${this.config.backendUrl}/cctv/cameras`);
            if (!res.ok) throw new Error("Failed to fetch CCTV data");

            const data = await res.json();
            this.cameras = data.cameras;

            this.renderMarkers();
            this.populatePanel();
            this.bindEvents();
        } catch (error) {
            console.error("CCTV Manger Initialization Error:", error);
        }
    }

    renderMarkers() {
        const viewer = this.mapEngine.viewer;

        this.cameras.forEach(cam => {
            // Pin marker
            const entity = viewer.entities.add({
                name: cam.name,
                position: Cesium.Cartesian3.fromDegrees(cam.lon, cam.lat),
                billboard: {
                    image: 'https://upload.wikimedia.org/wikipedia/commons/e/ea/Red_dot.svg', // Simple representation
                    width: 24,
                    height: 24,
                    color: Cesium.Color.RED.withAlpha(0.8),
                },
                properties: {
                    isCCTV: true,
                    cctvId: cam.id
                }
            });
            this.markers.push(entity);
        });

        // Add custom click handler for CCTV markers
        const handler = new Cesium.ScreenSpaceEventHandler(viewer.scene.canvas);
        handler.setInputAction((movement) => {
            const pickedObject = viewer.scene.pick(movement.position);
            if (Cesium.defined(pickedObject) && pickedObject.id && pickedObject.id.properties) {
                const isCCTV = pickedObject.id.properties.isCCTV;
                if (isCCTV) {
                    const id = pickedObject.id.properties.cctvId.getValue();
                    this.openPanel(id);
                }
            }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK); // Wait, MapEngine also uses left click. In real life, we should merge handlers or use priorities.
    }

    toggleMarkers(show) {
        this.isVisible = show;
        this.markers.forEach(m => m.show = show);
    }

    populatePanel() {
        const grid = document.getElementById('cctvGrid');
        grid.innerHTML = ''; // Clear

        this.cameras.forEach(cam => {
            const card = document.createElement('div');
            card.className = 'cctv-card';
            card.id = `card-${cam.id}`;
            card.innerHTML = `
                <div class="cctv-card-header">${cam.name} <span class="status-dot"></span></div>
                <div class="cctv-video-container" id="video-${cam.id}">
                    <iframe width="100%" height="100%" src="${cam.streamUrl}" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen style="border:none;"></iframe>
                    <!-- Analytical Overlays -->
                    <div class="cv-overlay" id="cv-${cam.id}"></div>
                </div>
                <!-- Sophisticated Backend Details -->
                <div style="margin-top: 10px; font-size: 0.75rem; color: #00aa88; line-height: 1.4;">
                    <strong>[ SYS.INFO ]</strong> ${cam.details}<br>
                    <strong>[ LAT/LON ]</strong> ${cam.lat}, ${cam.lon}<br>
                    <strong>[ TYPE ]</strong> <span>${cam.type}</span>
                </div>
            `;
            grid.appendChild(card);

            // Start mock CV simulation for this camera
            this.startCVOverlaySimulation(cam.id);
        });
    }

    startCVOverlaySimulation(camId) {
        const overlay = document.getElementById(`cv-${camId}`);
        if (!overlay) return;

        // Loop to generate random bounding boxes simulating "Vehicle" or "Person" detection
        setInterval(() => {
            // Randomly decide to add a box
            if (Math.random() > 0.6) {
                const box = document.createElement('div');
                box.className = 'cv-box';

                // Random position and size
                const top = Math.random() * 70; // 0-70%
                const left = Math.random() * 80; // 0-80%
                const width = Math.random() * 40 + 20; // 20-60px
                const height = Math.random() * 40 + 20; // 20-60px

                box.style.top = `${top}%`;
                box.style.left = `${left}%`;
                box.style.width = `${width}px`;
                box.style.height = `${height}px`;

                // Set label
                const isVehicle = Math.random() > 0.3;
                const confidence = (Math.random() * 15 + 85).toFixed(1); // 85-99%
                box.setAttribute('data-label', `${isVehicle ? 'VEHICLE' : 'PERSON'} ${confidence}%`);

                overlay.appendChild(box);

                // Remove box after a short delay to simulate movement/loss of tracking
                setTimeout(() => {
                    if (box.parentNode === overlay) {
                        overlay.removeChild(box);
                    }
                }, Math.random() * 2000 + 1000); // 1-3 seconds
            }
        }, 1000);
    }

    openPanel(focusCameraId = null) {
        document.getElementById('cctvPanel').classList.add('open');

        if (focusCameraId) {
            // Scroll to specific camera card in the sidebar
            const card = document.getElementById(`card-${focusCameraId}`);
            if (card) {
                card.scrollIntoView({ behavior: "smooth", block: "center" });
                // Briefly flash the card to highlight (flat style)
                card.style.borderColor = "var(--primary-color)";
                card.style.background = "var(--highlight-bg)";
                setTimeout(() => {
                    card.style.borderColor = "var(--panel-border)";
                    card.style.background = "#0a0a0a";
                }, 2000);
            }
        }
    }

    closePanel() {
        document.getElementById('cctvPanel').classList.remove('open');
    }

    bindEvents() {
        document.getElementById('closeCctvPanel').addEventListener('click', () => {
            this.closePanel();
        });
    }
}
