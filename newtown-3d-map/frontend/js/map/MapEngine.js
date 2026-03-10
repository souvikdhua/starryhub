export default class MapEngine {
    constructor(containerId, config) {
        this.containerId = containerId;
        this.config = config;
        this.viewer = null;
        this.buildingsLayer = null;
        this.routeEntity = null; // Stores the drawn route
        this.routingMode = false;
        this.routePoints = []; // [startLngLat, endLngLat]
        this.isDayMode = true;
    }

    async init() {
        console.log("Initializing CesiumJS MapEngine...");

        // Setup base Cesium Viewer
        // Uses default Cesium Ion token if not provided. In production, provide one via config.
        Cesium.Ion.defaultAccessToken = this.config.cesiumIonToken || Cesium.Ion.defaultAccessToken;

        // Set base Imagery Provider to High-Contrast CartoDB Dark Matter for that professional GIS look
        const imageryProvider = new Cesium.UrlTemplateImageryProvider({
            url: 'https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png',
            credit: 'Map tiles by Carto, under CC BY 3.0. Data by OpenStreetMap, under ODbL.'
        });

        this.viewer = new Cesium.Viewer(this.containerId, {
            terrainProvider: await Cesium.createWorldTerrainAsync().catch(e => {
                console.warn("Cesium Ion Terrain failed (token required). Falling back to flat terrain.");
                return new Cesium.EllipsoidTerrainProvider();
            }),
            imageryProvider: imageryProvider,
            baseLayerPicker: false,
            geocoder: false,
            homeButton: false,
            sceneModePicker: false,
            navigationHelpButton: false,
            animation: false,
            timeline: false,
            fullscreenButton: false,
            infoBox: false,
            selectionIndicator: false,
            skyAtmosphere: new Cesium.SkyAtmosphere(),
            shadows: true,
        });

        const scene = this.viewer.scene;
        scene.globe.enableLighting = true;
        scene.sun.show = true;

        // Add custom 100% open source 3D buildings from our OsmService backend
        await this.loadCustomOSMBuildings();

        // Fly to New Town, Kolkata
        // Coordinates: 22.58, 88.47
        this.flyToNewTown();

        // Setup interaction
        this.setupInteractions();
    }

    async loadCustomOSMBuildings() {
        try {
            console.log("Fetching custom 3D buildings from open source backend...");
            const url = `${this.config.backendUrl}/buildings/3d?bbox=${this.config.bbox}`;

            const dataSource = await Cesium.GeoJsonDataSource.load(url, {
                stroke: Cesium.Color.BLACK,
                fill: Cesium.Color.DARKGRAY,
                strokeWidth: 1,
            });

            const entities = dataSource.entities.values;

            for (let i = 0; i < entities.length; i++) {
                const entity = entities[i];
                if (entity.polygon) {
                    const height = entity.properties.extrudedHeight ? entity.properties.extrudedHeight.getValue() : 10;
                    const colorString = entity.properties.color ? entity.properties.color.getValue() : '#aaaaaa';
                    const name = entity.properties.name ? entity.properties.name.getValue() : '';

                    entity.polygon.extrudedHeight = height;
                    entity.polygon.material = Cesium.Color.fromCssColorString('#141414').withAlpha(0.6); // Flat dark panel color
                    entity.polygon.outline = true;
                    entity.polygon.outlineColor = Cesium.Color.fromCssColorString('#333333'); // Subtle flat border

                    // Add tactical floating labels for known buildings
                    if (name && height > 15) {
                        entity.position = entity.polygon.hierarchy.getValue(Cesium.JulianDate.now()).positions[0]; // approximate center
                        entity.label = {
                            text: ` ${name.toUpperCase()} `,
                            font: '600 12px "Inter", sans-serif',
                            fillColor: Cesium.Color.fromCssColorString('#e0e0e0'),
                            outlineColor: Cesium.Color.fromCssColorString('#141414'),
                            outlineWidth: 4,
                            showBackground: true,
                            backgroundColor: Cesium.Color.fromCssColorString('#141414').withAlpha(0.8),
                            backgroundPadding: new Cesium.Cartesian2(7, 5),
                            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
                            pixelOffset: new Cesium.Cartesian2(0, -20),
                            heightReference: Cesium.HeightReference.RELATIVE_TO_GROUND
                        };
                    }
                }
            }

            this.buildingsLayer = await this.viewer.dataSources.add(dataSource);
        } catch (error) {
            console.error('Failed to load custom OSM Buildings:', error);
        }
    }

    flyToNewTown() {
        this.viewer.camera.flyTo({
            destination: Cesium.Cartesian3.fromDegrees(88.47, 22.58, 1500),
            orientation: {
                heading: Cesium.Math.toRadians(0.0), // North
                pitch: Cesium.Math.toRadians(-45.0),
                roll: 0.0
            }
        });
    }

    toggleBuildings(show) {
        if (this.buildingsLayer) {
            this.buildingsLayer.show = show;
        }
    }

    toggleDayNight() {
        this.isDayMode = !this.isDayMode;
        if (this.isDayMode) {
            this.viewer.clock.currentTime = Cesium.JulianDate.fromDate(new Date("2024-01-01T12:00:00Z"));
        } else {
            this.viewer.clock.currentTime = Cesium.JulianDate.fromDate(new Date("2024-01-01T22:00:00Z"));
        }
    }

    searchLocation(query) {
        console.log(`Searching for: ${query} (Mock implemented)`);
        // We'd hit Nominatim or Google Geocoding here and fly to the result
    }

    toggleRoutingMode() {
        this.routingMode = !this.routingMode;
        this.routePoints = [];
        const btn = document.getElementById('btnCalculateRoute');

        if (this.routingMode) {
            btn.style.background = 'var(--primary-color)';
            btn.style.color = '#fff';
            btn.textContent = 'SELECT START POINT...';
            this.viewer.container.style.cursor = 'crosshair';
            if (this.routeEntity) {
                this.viewer.entities.remove(this.routeEntity);
                this.routeEntity = null;
            }
        } else {
            btn.style.background = 'rgba(0,0,0,0.5)';
            btn.style.color = 'var(--primary-color)';
            btn.textContent = 'CALCULATE EVOC ROUTE';
            this.viewer.container.style.cursor = 'default';
        }
    }

    async calculateAndDrawRoute() {
        if (this.routePoints.length !== 2) return;

        document.getElementById('btnCalculateRoute').textContent = 'CALCULATING...';

        try {
            const reqBody = {
                startLon: this.routePoints[0].lon,
                startLat: this.routePoints[0].lat,
                endLon: this.routePoints[1].lon,
                endLat: this.routePoints[1].lat
            };

            const response = await fetch(`${this.config.backendUrl}/routing/emergency-path`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(reqBody)
            });

            if (!response.ok) throw new Error("Route calculation failed.");

            const geojson = await response.json();

            // Draw route on map
            const coordinates = geojson.geometry.coordinates;
            const cesiumCoords = [];
            coordinates.forEach(coord => {
                cesiumCoords.push(coord[0], coord[1], 5); // 5m elevated so it doesn't clip into roads
            });

            this.routeEntity = this.viewer.entities.add({
                name: 'EVOC Route',
                polyline: {
                    positions: Cesium.Cartesian3.fromDegreesArrayHeights(cesiumCoords),
                    width: 5,
                    material: new Cesium.PolylineGlowMaterialProperty({
                        glowPower: 0.1,
                        taperPower: 0.1,
                        color: Cesium.Color.fromCssColorString('#2e66ff') // Professional blue instead of bright pink
                    })
                }
            });

            const distance = geojson.properties.totalDistanceMeters;
            console.log(`Route drawn. Total distance: ${distance}m.`);

            this.toggleRoutingMode(); // turn off mode
            document.getElementById('btnCalculateRoute').textContent = `ROUTE SET (${distance}m)`;
            setTimeout(() => {
                document.getElementById('btnCalculateRoute').textContent = 'CALCULATE EVOC ROUTE';
            }, 5000);

            // Fly camera to encompass route
            this.viewer.zoomTo(this.routeEntity);

        } catch (error) {
            console.error(error);
            this.toggleRoutingMode();
            alert("Routing error. Node might be un-routable.");
        }
    }

    setupInteractions() {
        const handler = new Cesium.ScreenSpaceEventHandler(this.viewer.scene.canvas);

        // Click to identify building or set route points
        handler.setInputAction((movement) => {
            const cartesian = this.viewer.camera.pickEllipsoid(movement.position, this.viewer.scene.globe.ellipsoid);

            // Check Routing Mode first
            if (this.routingMode && cartesian) {
                const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
                const lon = Cesium.Math.toDegrees(cartographic.longitude);
                const lat = Cesium.Math.toDegrees(cartographic.latitude);

                this.routePoints.push({ lon, lat });

                if (this.routePoints.length === 1) {
                    document.getElementById('btnCalculateRoute').textContent = 'SELECT DESTINATION...';
                } else if (this.routePoints.length === 2) {
                    this.calculateAndDrawRoute();
                }
                return; // skip building selection
            }

            const pickedFeature = this.viewer.scene.pick(movement.position);

            if (Cesium.defined(pickedFeature) && pickedFeature.id instanceof Cesium.Entity) {
                // Ignore CCTV markers (handled by CCTVManager)
                if (pickedFeature.id.properties && pickedFeature.id.properties.isCCTV) return;

                // Show modal for buildings
                this.showInfoModal(pickedFeature.id);
            } else {
                this.hideInfoModal();
            }
        }, Cesium.ScreenSpaceEventType.LEFT_CLICK);

        // Update Bottom Bar coordinates on mouse move
        handler.setInputAction((movement) => {
            const cartesian = this.viewer.camera.pickEllipsoid(movement.endPosition, this.viewer.scene.globe.ellipsoid);
            if (cartesian) {
                const cartographic = Cesium.Cartographic.fromCartesian(cartesian);
                const longitudeString = Cesium.Math.toDegrees(cartographic.longitude).toFixed(5);
                const latitudeString = Cesium.Math.toDegrees(cartographic.latitude).toFixed(5);
                const heightString = this.viewer.camera.positionCartographic.height.toFixed(0);

                const coordsDiv = document.getElementById('coordsDisplay');
                if (coordsDiv) {
                    coordsDiv.innerHTML = `Lng: ${longitudeString}, Lat: ${latitudeString}, Alt: ${heightString}m`;
                }
            }
        }, Cesium.ScreenSpaceEventType.MOUSE_MOVE);
    }

    showInfoModal(entity) {
        document.getElementById('infoModal').classList.remove('hidden');

        // GeoJSON Building metadata extraction
        const props = entity.properties;
        const name = props && props.name ? props.name.getValue() : 'UNIDENTIFIED STRUCTURE';
        const type = props && props.type ? props.type.getValue() : 'UNKNOWN';
        const height = props && props.height ? props.height.getValue() : '0';
        const levels = props && props['building:levels'] ? props['building:levels'].getValue() : '0';

        // Mock intelligence data generation based on entity ID/Position
        const threatLevel = Math.random() > 0.8 ? '<span style="color:var(--danger-color); font-weight:600;">ELEVATED</span>' : '<span style="color:var(--text-color)">NOMINAL</span>';
        const occLevel = Math.floor(Math.random() * 80) + 10;

        document.getElementById('infoTitle').textContent = `INSPECTOR: ${name.toUpperCase()}`;
        document.getElementById('infoBody').innerHTML = `
            <div style="font-size: 0.85rem; color: var(--text-color); line-height: 1.6;">
                <p><strong>[ CLASS ]</strong> <span style="text-transform:uppercase;">${type}</span></p>
                <p><strong>[ Z-INDEX ]</strong> ${levels} FLRS / ${height} M TRU</p>
                <p><strong>[ THREAT ]</strong> ${threatLevel}</p>
                <p><strong>[ THERMAL ]</strong> ${occLevel}% CAPACITY OBSERVED</p>
                
                <hr style="border:0; border-bottom: 1px solid var(--panel-border); margin: 10px 0;">
                
                <p style="font-size: 0.7rem; color: var(--text-muted);">SYS.DIAGNOSTIC.TRACE</p>
                <p style="font-family: var(--font-mono); font-size: 0.75rem;">HASH: 0x${Math.random().toString(16).substr(2, 8).toUpperCase()}</p>
            </div>
        `;

        document.getElementById('closeInfoModal').onclick = () => this.hideInfoModal();
    }

    hideInfoModal() {
        document.getElementById('infoModal').classList.add('hidden');
    }
}
