// Initialize the map
const map = L.map('map').setView([39.8283, -98.5795], 4); // Center on US

// Add the tile layer
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
}).addTo(map);

// ... (previous map initialization code remains the same)

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

// Load and display state boundaries
let statesLayer;
fetch('/api/states')
    .then(response => response.json())
    .then(data => {
        statesLayer = L.geoJSON(data, {
            style: getStateStyle,
            onEachFeature: onEachFeature
        }).addTo(map);
    })
    .catch(error => console.error('Error loading state data:', error));

// Update the statistics panel
function updateStatistics(properties) {
    const statsDiv = document.getElementById('statistics');
    statsDiv.innerHTML = `
        <p class="mb-2"><strong>State:</strong> ${properties.name || 'N/A'}</p>
    `;
}

// Add event listeners
document.getElementById('dataset-select').addEventListener('change', function(e) {
    // Handle dataset change
    console.log('Dataset changed:', e.target.value);
});

document.getElementById('filter-range').addEventListener('input', function(e) {
    // Handle filter change
    console.log('Filter changed:', e.target.value);
});