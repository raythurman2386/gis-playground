// Initialize the map
const map = L.map('map').setView([39.8283, -98.5795], 4); // Center on US

// Add the tile layer (you can change this to any tile provider you prefer)
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    maxZoom: 18
}).addTo(map);

// Add event listeners
document.getElementById('dataset-select').addEventListener('change', function(e) {
    // Handle dataset change
    console.log('Dataset changed:', e.target.value);
});

document.getElementById('filter-range').addEventListener('input', function(e) {
    // Handle filter change
    console.log('Filter changed:', e.target.value);
});

// Function to update statistics panel
function updateStatistics(properties) {
    const statsDiv = document.getElementById('statistics');
    statsDiv.innerHTML = `
        <p>Region: ${properties?.name || 'N/A'}</p>
        <p>Value: ${properties?.value || 'N/A'}</p>
    `;
}