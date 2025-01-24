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

    'Night': L.tileLayer('https://map1.vis.earthdata.nasa.gov/wmts-webmerc/VIIRS_CityLights_2012/default/{time}/{tilematrixset}{maxZoom}/{z}/{y}/{x}.{format}', {
        attribution: 'Imagery provided by services from the Global Imagery Browse Services (GIBS), operated by the NASA/GSFC/Earth Science Data and Information System.',
        bounds: [[-85.0511287776, -179.999999975], [85.0511287776, 179.999999975]],
        minZoom: 1,
        maxZoom: 8,
        format: 'jpg',
        time: '',
        tilematrixset: 'GoogleMapsCompatible_Level'
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

function saveStatsToLocalStorage(properties, type) {
    localStorage.setItem('currentStats', JSON.stringify({
        properties,
        type,
        timestamp: Date.now()
    }));
}

function clearStatsFromLocalStorage() {
    localStorage.removeItem('currentStats');
}

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
})

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
})

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

const customLayers = {};

function createLayerControls(layer) {
    const controlsDiv = document.createElement('div');
    controlsDiv.className = 'layer-controls hidden p-2 bg-gray-50 rounded mt-1';
    controlsDiv.id = `controls-${layer.id}`;

    // Style controls
    const styleControls = `
        <div class="space-y-2">
            <div>
                <label class="text-xs">Fill Color</label>
                <input type="color" class="w-full"
                       data-style="fillColor"
                       value="#3388ff">
            </div>
            <div>
                <label class="text-xs">Border Color</label>
                <input type="color" class="w-full"
                       data-style="color"
                       value="#666666">
            </div>
            <div>
                <label class="text-xs">Fill Opacity</label>
                <input type="range" class="w-full"
                       data-style="fillOpacity"
                       min="0" max="1" step="0.1" value="0.7">
            </div>
            <div>
                <label class="text-xs">Border Width</label>
                <input type="range" class="w-full"
                       data-style="weight"
                       min="1" max="5" step="0.5" value="2">
            </div>
        </div>
        <div class="flex space-x-2 mt-2">
            <button class="download-btn bg-green-500 text-white px-2 py-1 rounded text-xs">
                Download
            </button>
            <button class="delete-btn bg-red-500 text-white px-2 py-1 rounded text-xs">
                Delete
            </button>
        </div>
    `;

    controlsDiv.innerHTML = styleControls;

    // Add event listeners for style controls
    controlsDiv.querySelectorAll('input').forEach(input => {
        input.addEventListener('change', () => {
            updateLayerStyle(layer.id);
        });
    });

    // Add download handler
    controlsDiv.querySelector('.download-btn').addEventListener('click', () => {
        downloadLayer(layer.id, layer.name);
    });

    // Add delete handler
    controlsDiv.querySelector('.delete-btn').addEventListener('click', () => {
        deleteLayer(layer.id);
    });

    return controlsDiv;
}

function updateLayerStyle(layerId) {
    const controls = document.getElementById(`controls-${layerId}`);
    const styleInputs = controls.querySelectorAll('input[data-style]');
    const style = {};

    styleInputs.forEach(input => {
        style[input.dataset.style] = input.type === 'range' ? parseFloat(input.value) : input.value;
    });

    if (customLayers[layerId]) {
        const newStyle = {
            fillColor: style.fillColor || '#3388ff',
            color: style.color || '#666666',
            weight: style.weight || 2,
            opacity: 1,
            fillOpacity: style.fillOpacity || 0.7,
            dashArray: '3'
        };

        customLayers[layerId].style = newStyle;

        customLayers[layerId].layer.eachLayer(function(layer) {
            layer.defaultStyle = {...newStyle};
            if (layer instanceof L.CircleMarker) {
                // Handle point features
                layer.setStyle({
                    fillColor: newStyle.fillColor,
                    color: newStyle.color,
                    weight: newStyle.weight,
                    fillOpacity: newStyle.fillOpacity
                });
            } else {
                // Handle path features
                layer.setStyle(newStyle);
            }
        });
    }
}

function downloadLayer(layerId, layerName) {
    fetch(`/api/layers/${layerId}`)
        .then(response => response.json())
        .then(data => {
            // Create downloadable file
            const dataStr = "data:text/json;charset=utf-8," +
                           encodeURIComponent(JSON.stringify(data));
            const downloadAnchorNode = document.createElement('a');
            downloadAnchorNode.setAttribute("href", dataStr);
            downloadAnchorNode.setAttribute("download", `${layerName}.geojson`);
            document.body.appendChild(downloadAnchorNode);
            downloadAnchorNode.click();
            downloadAnchorNode.remove();
        });
}

function deleteLayer(layerId) {
    if (confirm('Are you sure you want to delete this layer?')) {
        fetch(`/api/layers/${layerId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.message) {
                removeLayer(layerId);
                loadAvailableLayers(); // Refresh layer list
            }
        });
    }
}

function loadAvailableLayers() {
    fetch('/api/layers')
        .then(response => response.json())
        .then(layers => {
            const layersList = document.getElementById('layersList');
            layersList.innerHTML = '';

            layers.forEach(layer => {
                const layerContainer = document.createElement('div');
                layerContainer.className = 'layer-item mb-2 border rounded';

                const layerHeader = document.createElement('div');
                layerHeader.className = 'flex items-center justify-between p-2 cursor-pointer hover:bg-gray-50';

                const leftSection = document.createElement('div');
                leftSection.className = 'flex items-center space-x-2';

                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.id = `layer-${layer.id}`;
                checkbox.className = 'form-checkbox h-4 w-4 text-blue-600';

                const label = document.createElement('label');
                label.htmlFor = `layer-${layer.id}`;
                label.className = 'text-sm text-gray-700';
                label.textContent = layer.name;

                const toggleButton = document.createElement('button');
                toggleButton.className = 'text-gray-500 hover:text-gray-700';
                toggleButton.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path></svg>';

                leftSection.appendChild(checkbox);
                leftSection.appendChild(label);
                layerHeader.appendChild(leftSection);
                layerHeader.appendChild(toggleButton);

                const controls = createLayerControls(layer);

                layerContainer.appendChild(layerHeader);
                layerContainer.appendChild(controls);

                //  Add a tooltip to the layer if it has a description
                if (layer.description) {
                    label.title = layer.description;
                }

                // Toggle controls visibility
                toggleButton.addEventListener('click', () => {
                    controls.classList.toggle('hidden');
                    toggleButton.querySelector('svg').style.transform =
                        controls.classList.contains('hidden') ? '' : 'rotate(180deg)';
                });

                checkbox.addEventListener('change', function() {
                    if (this.checked) {
                        loadLayer(layer.id, layer.name);
                    } else {
                        removeLayer(layer.id);
                    }
                });

                layersList.appendChild(layerContainer);
            });
        })
        .catch(error => {
            console.error('Error loading layers:', error);
        });
}

function loadLayer(layerId, layerName) {
    fetch(`/api/layers/${layerId}`)
        .then(response => response.json())
        .then(data => {
            const controls = document.getElementById(`controls-${layerId}`);
            const style = {};

            controls.querySelectorAll('input[data-style]').forEach(input => {
                style[input.dataset.style] = input.type === 'range' ?
                    parseFloat(input.value) : input.value;
            });

            const baseStyle = {
                fillColor: style.fillColor || '#3388ff',
                color: style.color || '#666666',
                weight: style.weight || 2,
                opacity: 1,
                fillOpacity: style.fillOpacity || 0.7,
                dashArray: '3'
            };

            const newLayer = L.geoJSON(data, {
                pointToLayer: function(feature, latlng) {
                    // Handle point features
                    return L.circleMarker(latlng, {
                        radius: 8,
                        fillColor: baseStyle.fillColor,
                        color: baseStyle.color,
                        weight: baseStyle.weight,
                        opacity: baseStyle.opacity,
                        fillOpacity: baseStyle.fillOpacity
                    });
                },
                style: function(feature) {
                    // Style for line and polygon features
                    return {...baseStyle};
                },
                onEachFeature: function(feature, layer) {
                    layer.defaultStyle = {...baseStyle};

                    layer.on({
                        mouseover: function(e) {
                            const layer = e.target;
                            if (feature.geometry.type === 'Point') {
                                // Handle point feature highlighting
                                layer.setRadius(12);
                                layer.setStyle({
                                    fillOpacity: Math.min(baseStyle.fillOpacity + 0.2, 1),
                                    weight: baseStyle.weight + 1
                                });
                            } else {
                                // Handle path feature highlighting
                                const highlightStyle = {
                                    ...layer.defaultStyle,
                                    weight: layer.defaultStyle.weight + 1,
                                    fillOpacity: Math.min(layer.defaultStyle.fillOpacity + 0.2, 1)
                                };
                                layer.setStyle(highlightStyle);
                            }
                            layer.bringToFront();
                            updateCustomLayerStatistics(feature.properties);
                        },
                        mouseout: function(e) {
                            const layer = e.target;
                            if (feature.geometry.type === 'Point') {
                                // Reset point feature style
                                layer.setRadius(8);
                                layer.setStyle({
                                    fillOpacity: baseStyle.fillOpacity,
                                    weight: baseStyle.weight
                                });
                            } else {
                                // Reset path feature style
                                layer.setStyle(layer.defaultStyle);
                            }
                        },
                        click: function(e) {
                            if (feature.geometry.type === 'Point') {
                                map.setView(e.target.getLatLng(), map.getZoom());
                            } else {
                                map.fitBounds(e.target.getBounds());
                            }
                            updateCustomLayerStatistics(feature.properties);
                        }
                    });
                }
            }).addTo(map);

            customLayers[layerId] = {
                layer: newLayer,
                style: baseStyle
            };
            overlayMaps[layerName] = newLayer;
        })
        .catch(error => {
            console.error('Error loading layer:', error);
        });
}

function removeLayer(layerId) {
    if (customLayers[layerId]) {
        map.removeLayer(customLayers[layerId].layer);
        delete customLayers[layerId];
    }
}

function displayStatistics(properties, type) {
    const statsDiv = document.getElementById('attributes');
        const clearButton = document.getElementById('clearStats');
        clearButton.classList.remove('hidden');

        let html = `
            <div class="relative overflow-x-auto">
                <table class="w-full text-sm text-left">
                    <thead class="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>`;

    let rowData = [];

    if (type === 'incident') {
        rowData = [
            ['Fire Name', properties.IncidentName || 'Unknown'],
            ['Status', properties.IncidentStatus || 'Unknown'],
            ['Size', `${properties.DailyAcres ? properties.DailyAcres.toLocaleString() : 'Unknown'} acres`],
            ['Discovered', properties.FireDiscoveryDateTime ? new Date(properties.FireDiscoveryDateTime).toLocaleString() : 'Unknown'],
            ['Containment', `${properties.PercentContained || '0'}%`],
            ['Cause', properties.FireCause || 'Unknown'],
            ['Complex', properties.ComplexName || 'N/A'],
            ['Agency', properties.POOProtectingAgency || 'Unknown']
        ];
    } else if (type === 'perimeter') {
        rowData = [
            ['Fire Name', properties.IncidentName || 'Unknown'],
            ['Total Area', `${properties.GISAcres ? properties.GISAcres.toLocaleString() : 'Unknown'} acres`],
            ['Containment', `${properties.PercentContained || '0'}%`],
            ['Updated', properties.CreateDate ? new Date(properties.CreateDate).toLocaleString() : 'Unknown'],
            ['Complex', properties.ComplexName || 'N/A'],
            ['Type', properties.IncidentTypeCategory || 'Unknown']
        ];
    } else {
        // Custom layer statistics
        rowData = Object.entries(properties).map(([key, value]) => [key, value || 'N/A']);
    }

    // Add headers
    rowData.forEach(([key]) => {
        html += `
            <th scope="col" class="px-6 py-3 whitespace-nowrap">
                ${key}
            </th>`;
    });

    html += `
                </tr>
            </thead>
            <tbody>
                <tr class="bg-white border-b">`;

    // Add values
    rowData.forEach(([_, value]) => {
        html += `
            <td class="px-6 py-4 whitespace-nowrap">
                ${value}
            </td>`;
    });

    html += `
                </tr>
            </tbody>
        </table>
    </div>`;

    statsDiv.innerHTML = html;
}

function updateFireStatistics(properties, type) {
    saveStatsToLocalStorage(properties, type);
    displayStatistics(properties, type);
}

function updateCustomLayerStatistics(properties) {
    saveStatsToLocalStorage(properties, 'custom');
    displayStatistics(properties, 'custom');
}

function clearStatistics() {
    const statsDiv = document.getElementById('attributes');
        const clearButton = document.getElementById('clearStats');
        statsDiv.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                No feature selected
            </div>
        `;
        clearButton.classList.add('hidden');
    clearStatsFromLocalStorage();
}

function checkStoredStatistics() {
    const storedStats = localStorage.getItem('currentStats');
    if (storedStats) {
        const { properties, type, timestamp } = JSON.parse(storedStats);
        clearStatsFromLocalStorage();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    loadAvailableLayers();
    checkStoredStatistics();
    const clearButton = document.getElementById('clearStats');
    clearButton.addEventListener('click', clearStatistics);
});