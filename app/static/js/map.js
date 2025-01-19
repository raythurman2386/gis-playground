const baseMaps = {
    'OpenStreetMap': L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }),

    'OpenTopoMap': L.tileLayer('https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', {
        attribution: 'Map data: &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, <a href="http://viewfinderpanoramas.org">SRTM</a> | Map style: &copy; <a href="https://opentopomap.org">OpenTopoMap</a>',
        maxZoom: 17
    }),

    'Satellite': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community',
        maxZoom: 18
    }),

    'Ocean': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/Ocean/World_Ocean_Base/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Sources: GEBCO, NOAA, CHS, OSU, UNH, CSUMB, National Geographic, DeLorme, NAVTEQ, and Esri',
        maxZoom: 18
    }),

    'Physical': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; Source: US National Park Service',
        maxZoom: 8
    }),

    'NatGeo': L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/NatGeo_World_Map/MapServer/tile/{z}/{y}/{x}', {
        attribution: 'Tiles &copy; Esri &mdash; National Geographic, Esri, DeLorme, NAVTEQ, UNEP-WCMC, USGS, NASA, ESA, METI, NRCAN, GEBCO, NOAA, iPC',
        maxZoom: 16
    }),

    'Dark': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }),

    'Light': L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    })
};

const map = L.map('map', {
    center: [39.8283, -98.5795],
    zoom: 4,
    layers: [baseMaps['OpenStreetMap']]
});

// ESRI Fire Layers
const wildfireIncidents = L.esri.featureLayer({
    url: 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/USA_Wildfires_v1/FeatureServer/0',
    pointToLayer: function (feature, latlng) {
        return L.circleMarker(latlng, {
            radius: 24,
            fillColor: "#ff0000",
            color: "#ffffff",
            weight: 2,
            opacity: 1,
            fillOpacity: 0.7
        });
    }
}).on('click mouseover', function(e) {
    updateFireStatistics(e.layer.feature.properties, 'incident');
}).on('mouseout', clearStatistics);

const wildfirePerimeters = L.esri.featureLayer({
    url: 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/USA_Wildfires_v1/FeatureServer/1',
    style: function(feature) {
        return {
            color: "#F44336",
            weight: 2,
            opacity: 0.8,
            fillOpacity: 0.35
        };
    }
}).on('click mouseover', function(e) {
    updateFireStatistics(e.layer.feature.properties, 'perimeter');
}).on('mouseout', clearStatistics);

function updateFireStatistics(properties, type) {
    const statsDiv = document.getElementById('statistics');

    if (type === 'incident') {
        statsDiv.innerHTML = `
            <div class="space-y-2">
                <p class="font-semibold text-red-600">Active Fire Incident</p>
                <p><strong>Fire Name:</strong> ${properties.IncidentName || 'Unknown'}</p>
                <p><strong>Status:</strong> ${properties.IncidentStatus || 'Unknown'}</p>
                <p><strong>Size:</strong> ${properties.DailyAcres ? properties.DailyAcres.toLocaleString() : 'Unknown'} acres</p>
                <p><strong>Discovered:</strong> ${properties.FireDiscoveryDateTime ? new Date(properties.FireDiscoveryDateTime).toLocaleString() : 'Unknown'}</p>
                <p><strong>Containment:</strong> ${properties.PercentContained || '0'}%</p>
                <p><strong>Cause:</strong> ${properties.FireCause || 'Unknown'}</p>
                ${properties.ComplexName ? `<p><strong>Complex:</strong> ${properties.ComplexName}</p>` : ''}
                <p><strong>Agency:</strong> ${properties.POOProtectingAgency || 'Unknown'}</p>
            </div>
        `;
    } else if (type === 'perimeter') {
        statsDiv.innerHTML = `
            <div class="space-y-2">
                <p class="font-semibold text-orange-600">Fire Perimeter</p>
                <p><strong>Fire Name:</strong> ${properties.IncidentName || 'Unknown'}</p>
                <p><strong>Total Area:</strong> ${properties.GISAcres ? properties.GISAcres.toLocaleString() : 'Unknown'} acres</p>
                <p><strong>Containment:</strong> ${properties.PercentContained || '0'}%</p>
                <p><strong>Updated:</strong> ${properties.CreateDate ? new Date(properties.CreateDate).toLocaleString() : 'Unknown'}</p>
                ${properties.ComplexName ? `<p><strong>Complex:</strong> ${properties.ComplexName}</p>` : ''}
                <p><strong>Type:</strong> ${properties.IncidentTypeCategory || 'Unknown'}</p>
            </div>
        `;
    }
}

function clearStatistics() {
    const statsDiv = document.getElementById('statistics');
    statsDiv.innerHTML = `
        <p class="text-gray-600">
            Hover over or click a feature to view statistics
        </p>
    `;
}

// Set up layer control
const overlayMaps = {
    'Fire Incidents': wildfireIncidents,
    'Fire Perimeters': wildfirePerimeters
};

// Add layer controls
L.control.layers(baseMaps, overlayMaps, {
    position: 'topright',
    collapsed: false
}).addTo(map);

// Add scale control
L.control.scale({
    imperial: true,
    metric: true,
    position: 'bottomleft'
}).addTo(map);