/**
 * Converts raw OSM JSON to GeoJSON with 3D properties 
 * appropriate for CesiumJS or DeckGL
 */

import osmtogeojson from 'osmtogeojson';

export const processBuildingData = (osmData) => {
    const geojson = osmtogeojson(osmData);
    const processedFeatures = [];

    geojson.features.forEach(f => {
        if (!f.properties || !f.properties.building) return;

        let height = 10;
        if (f.properties.height) {
            height = parseFloat(f.properties.height.replace('m', ''));
        } else if (f.properties['building:levels']) {
            height = parseInt(f.properties['building:levels']) * 3;
        }

        // Cesium styling relies on these properties
        f.properties.height = height || 10;
        // Cesium GeoJsonDataSource can use this directly if we map it later
        f.properties.extrudedHeight = f.properties.height;

        let color = '#a2c4c9'; // residential default
        if (f.properties.building === 'commercial') color = '#f6b26b';
        if (f.properties.building === 'retail') color = '#e06666';
        if (f.properties.building === 'office') color = '#9fc5e8';
        if (f.properties.building === 'yes') color = '#cccccc';

        f.properties.color = f.properties['building:colour'] || color;

        // Make sure it's an extruded polygon
        if (f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon') {
            processedFeatures.push(f);
        }
    });

    return {
        type: "FeatureCollection",
        features: processedFeatures
    };
};
