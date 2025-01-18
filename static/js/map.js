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

    'Dark': L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }),

    'Light': L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 19
    }),
};

const map = L.map('map', {
    center: [39.8283, -98.5795],
    zoom: 4,
    layers: [baseMaps['OpenStreetMap']]
});

const wildfireLayer = L.esri.featureLayer({
    url: 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/ArcGIS/rest/services/USA_Wildfires_v1/FeatureServer/0',
    style: function (feature) {
        return {
            color: '#ff0000',
            weight: 1,
            opacity: 1,
            fillOpacity: 0.7
        };
    }
}).on('click mouseover', function(e) {
    const properties = e.layer.feature.properties;
    updateFireStatistics(properties);
}).on('mouseout', function() {
    clearStatistics();
});

// Style function for the states
function getStateStyle(feature) {
    return {
        fillColor: '#3388ff',
        weight: 1,
        opacity: 1,
        color: '#666',
        dashArray: '2',
        fillOpacity: 0.2
    };
}

// Interaction functions
function highlightFeature(e) {
    const layer = e.target;

    layer.setStyle({
        weight: 2,
        color: '#666',
        dashArray: '',
        fillOpacity: 0.5
    });

    layer.bringToFront();
    updateStatistics(layer.feature.properties);
}

function resetHighlight(e) {
    statesLayer.resetStyle(e.target);
}

function onEachFeature(feature, layer) {
    layer.on({
        mouseover: highlightFeature,
        mouseout: resetHighlight,
        click: function(e) {
            map.fitBounds(e.target.getBounds());
            updateStatistics(feature.properties);
        }
    });
}

function updateFireStatistics(properties) {
    const statsDiv = document.getElementById('statistics');
    statsDiv.innerHTML = `
        <div class="space-y-2">
            <p class="font-semibold text-red-600">Wildfire Information</p>
            <p><strong>Fire Name:</strong> ${properties.IncidentName || 'Unknown'}</p>
            <p><strong>Status:</strong> ${properties.IncidentStatus || 'Unknown'}</p>
            <p><strong>Size:</strong> ${properties.DailyAcres ? properties.DailyAcres.toLocaleString() : 'Unknown'} acres</p>
            <p><strong>Reported:</strong> ${properties.CreateDate ? new Date(properties.CreateDate).toLocaleDateString() : 'Unknown'}</p>
            <p><strong>Containment:</strong> ${properties.PercentContained || '0'}%</p>
            ${properties.ComplexName ? `<p><strong>Complex:</strong> ${properties.ComplexName}</p>` : ''}
        </div>
    `;
}

function clearStatistics() {
    const statsDiv = document.getElementById('statistics');
    statsDiv.innerHTML = `
        <p class="text-gray-600">
            Hover over or click a feature to view statistics
        </p>
    `;
}

function updateStatistics(properties) {
    // Check if this is a state feature (has id/name) or a fire feature (has IncidentName)
    if (properties.IncidentName) {
        updateFireStatistics(properties);
    } else {
        const statsDiv = document.getElementById('statistics');
        statsDiv.innerHTML = `
            <div class="space-y-2">
                <p class="font-semibold">Region Information</p>
                <p><strong>Region ID:</strong> ${properties.id || 'N/A'}</p>
                <p><strong>Name:</strong> ${properties.name || 'N/A'}</p>
            </div>
        `;
    }
}

// Load and display state boundaries
let statesLayer;
fetch('/api/states')
    .then(response => response.json())
    .then(data => {
        statesLayer = L.geoJSON(data, {
            style: getStateStyle,
            onEachFeature: onEachFeature
        }).addTo(map);

        // Create overlay layers object
        const overlayMaps = {
            'State Boundaries': statesLayer,
            'Active Wildfires': wildfireLayer,
        };

        // Add layer control
        L.control.layers(baseMaps, overlayMaps, {
            position: 'topright',
            collapsed: false
        }).addTo(map);
    })
    .catch(error => {
        console.error('Error loading state data:', error);
    });

// Add scale control
L.control.scale({
    imperial: true,
    metric: true,
    position: 'bottomleft'
}).addTo(map);