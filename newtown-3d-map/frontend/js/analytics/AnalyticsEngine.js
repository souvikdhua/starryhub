export default class AnalyticsEngine {
    constructor(mapEngine, config) {
        this.mapEngine = mapEngine;
        this.config = config;
        this.heatmapDataSource = null;
    }

    async init() {
        console.log("[Analytics] Ready to generate spatial layers.");
    }

    async showHeatmap() {
        try {
            console.log("[Analytics] Fetching live density anomalies...");
            document.getElementById('toggleAnalytics').disabled = true;

            const res = await fetch(`${this.config.backendUrl}/analytics/heatmap`);
            const geojson = await res.json();

            // Render as glowing heat zones
            this.heatmapDataSource = await Cesium.GeoJsonDataSource.load(geojson);

            const entities = this.heatmapDataSource.entities.values;
            entities.forEach(entity => {
                if (entity.billboard) {
                    // Remove default pin
                    entity.billboard = undefined;

                    const isCritical = entity.properties.type.getValue() === 'CRITICAL_ANOMALY';
                    const weight = entity.properties.weight.getValue();

                    entity.ellipse = new Cesium.EllipseGraphics({
                        semiMinorAxis: weight * 15,
                        semiMajorAxis: weight * 15,
                        material: new Cesium.ColorMaterialProperty(
                            isCritical ? Cesium.Color.RED.withAlpha(0.6) : Cesium.Color.ORANGE.withAlpha(0.4)
                        ),
                        height: 5,
                        outline: true,
                        outlineColor: isCritical ? Cesium.Color.RED : Cesium.Color.ORANGE
                    });
                }
            });

            this.mapEngine.viewer.dataSources.add(this.heatmapDataSource);
            document.getElementById('toggleAnalytics').disabled = false;

        } catch (error) {
            console.error("[Analytics] Error:", error);
            document.getElementById('toggleAnalytics').disabled = false;
        }
    }

    hideHeatmap() {
        if (this.heatmapDataSource) {
            this.mapEngine.viewer.dataSources.remove(this.heatmapDataSource);
            this.heatmapDataSource = null;
        }
    }
}
