import { LocalStorageManager } from '../utils/LocalStorageManager.js';

export class CustomLayers {
    constructor(map) {
        this.map = map;
        this.layers = new Map();
        this.defaultStyle = {
            color: "#3388ff",
            weight: 3,
            opacity: 1,
            fillOpacity: 0.7,
            dashArray: '3'
        };
        this.setupEventListeners();
    }

    async loadAvailableLayers() {
        try {
            const response = await fetch('/api/layers');
            const layers = await response.json();
            this.renderLayersList(layers);
        } catch (error) {
            console.error('Error loading layers:', error);
        }
    }

    renderLayersList(layers) {
        const layersList = document.getElementById('layersList');
        layersList.innerHTML = '';
        layers.forEach(layer => this.addLayerToList(layer));
    }

    addLayerToList(layer) {
        const layersList = document.getElementById('layersList');
        const layerContainer = document.createElement('div');
        layerContainer.className = 'layer-item mb-2 border rounded';

        layerContainer.innerHTML = this.createLayerHTML(layer);
        this.addLayerItemEventListeners(layerContainer, layer);
        layersList.appendChild(layerContainer);
    }

    createLayerHTML(layer) {
        return `
            <div class="flex items-center justify-between p-2 cursor-pointer hover:bg-gray-50">
                <div class="flex items-center space-x-2">
                    <input type="checkbox" id="layer-${layer.id}" 
                           class="form-checkbox h-4 w-4 text-blue-600">
                    <label for="layer-${layer.id}" class="text-sm text-gray-700" 
                           title="${layer.description || ''}">${layer.name}</label>
                </div>
                <button class="text-gray-500 hover:text-gray-700 toggle-controls">
                    <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" 
                              stroke-width="2" d="M19 9l-7 7-7-7"></path>
                    </svg>
                </button>
            </div>
            <div class="layer-controls hidden p-2 bg-gray-50 rounded mt-1" id="controls-${layer.id}">
                <div class="space-y-2">
                    <div>
                        <label class="text-xs">Fill Color</label>
                        <input type="color" class="w-full" data-style="fillColor" value="#3388ff">
                    </div>
                    <div>
                        <label class="text-xs">Border Color</label>
                        <input type="color" class="w-full" data-style="color" value="#666666">
                    </div>
                    <div>
                        <label class="text-xs">Fill Opacity</label>
                        <input type="range" class="w-full" data-style="fillOpacity" 
                               min="0" max="1" step="0.1" value="0.7">
                    </div>
                    <div>
                        <label class="text-xs">Border Width</label>
                        <input type="range" class="w-full" data-style="weight" 
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
            </div>
        `;
    }

    addLayerItemEventListeners(layerContainer, layer) {
        const toggleButton = layerContainer.querySelector('.toggle-controls');
        const controls = layerContainer.querySelector('.layer-controls');
        const checkbox = layerContainer.querySelector(`#layer-${layer.id}`);

        this.setupToggleControls(toggleButton, controls);
        this.setupCheckboxHandler(checkbox, layer);
        this.setupStyleControls(controls, layer.id);
        this.setupActionButtons(controls, layer);
    }

    setupToggleControls(toggleButton, controls) {
        toggleButton.addEventListener('click', () => {
            controls.classList.toggle('hidden');
            toggleButton.querySelector('svg').style.transform = 
                controls.classList.contains('hidden') ? '' : 'rotate(180deg)';
        });
    }

    setupCheckboxHandler(checkbox, layer) {
        checkbox.addEventListener('change', (e) => {
            e.target.checked ? this.loadLayer(layer.id, layer.name) : this.removeLayer(layer.id);
        });
    }

    setupStyleControls(controls, layerId) {
        controls.querySelectorAll('[data-style]').forEach(input => {
            input.addEventListener('change', () => this.updateLayerStyle(layerId));
        });
    }

    setupActionButtons(controls, layer) {
        controls.querySelector('.download-btn').addEventListener('click', () => 
            this.downloadLayer(layer.id, layer.name));
        controls.querySelector('.delete-btn').addEventListener('click', () => 
            this.deleteLayer(layer.id));
    }

    async loadLayer(layerId, layerName) {
        try {
            const response = await fetch(`/api/layers/${layerId}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            
            const geojson = await response.json();
            this.removeExistingLayer(layerId);
            
            const style = this.getLayerStyle(layerId);
            const layer = this.createGeoJSONLayer(geojson, style, layerName);
            
            this.addLayerToMap(layer, layerId);
        } catch (error) {
            this.handleLayerError(error, layerId, layerName);
        }
    }

    removeExistingLayer(layerId) {
        if (this.layers.has(layerId)) {
            this.map.removeLayer(this.layers.get(layerId));
        }
    }

    createGeoJSONLayer(geojson, style, layerName) {
        return L.geoJSON(geojson, {
            style: style,
            onEachFeature: (feature, layer) => this.onEachFeature(feature, layer, style, layerName)
        });
    }

    addLayerToMap(layer, layerId) {
        layer.addTo(this.map);
        this.layers.set(layerId, layer);
        // this.map.fitBounds(layer.getBounds());
    }

    handleLayerError(error, layerId, layerName) {
        console.error('Error loading layer:', error);
        const checkbox = document.querySelector(`#layer-${layerId}`);
        if (checkbox) checkbox.checked = false;
        alert(`Failed to load layer "${layerName}". Please try again later.`);
    }

    onEachFeature(feature, layer, style, layerName) {
        layer.on({
            click: () => this.updateCustomLayerStatistics(feature.properties, layerName),
            mouseover: () => this.highlightFeature(layer, style),
            mouseout: () => layer.setStyle(style)
        });
    }

    highlightFeature(layer, style) {
        layer.setStyle({
            weight: style.weight + 2,
            color: '#666',
            fillOpacity: style.fillOpacity + 0.1
        });
    }

    updateCustomLayerStatistics(properties, layerName) {
        const statsDiv = document.getElementById('attributes');
        const clearButton = document.getElementById('clearStats');
        clearButton.classList.remove('hidden');

        statsDiv.innerHTML = this.createStatisticsHTML(properties, layerName);
        LocalStorageManager.saveStatsToLocalStorage(properties, layerName);
    }

    createStatisticsHTML(properties, layerName) {
        const rows = Object.entries(properties)
            .map(([key, value]) => this.createTableRow(key, value))
            .join('');

        return `
            <div class="relative overflow-x-auto">
                <table class="w-full text-sm text-left">
                    <thead class="text-xs text-gray-700 uppercase bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3">Property</th>
                            <th scope="col" class="px-6 py-3">Value</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${this.createTableRow('Layer Name', layerName)}
                        ${rows}
                    </tbody>
                </table>
            </div>`;
    }

    createTableRow(key, value) {
        return `
            <tr class="bg-white border-b">
                <td class="px-6 py-4 font-medium text-gray-900 whitespace-nowrap">${key}</td>
                <td class="px-6 py-4">${value}</td>
            </tr>`;
    }

    getLayerStyle(layerId) {
        const controls = document.getElementById(`controls-${layerId}`);
        const style = {...this.defaultStyle};
        controls.querySelectorAll('[data-style]').forEach(input => {
            style[input.dataset.style] = input.type === 'range' ? 
                parseFloat(input.value) : input.value;
        });
        return style;
    }

    updateLayerStyle(layerId) {
        if (this.layers.has(layerId)) {
            this.layers.get(layerId).setStyle(this.getLayerStyle(layerId));
        }
    }

    async deleteLayer(layerId) {
        try {
            const response = await fetch(`/api/layers/${layerId}`, { method: 'DELETE' });
            if (response.ok) {
                this.removeLayer(layerId);
                document.querySelector(`.layer-item:has(#layer-${layerId})`).remove();
            }
        } catch (error) {
            console.error('Error deleting layer:', error);
        }
    }

    removeLayer(layerId) {
        if (this.layers.has(layerId)) {
            this.map.removeLayer(this.layers.get(layerId));
            this.layers.delete(layerId);
        }
    }

    downloadLayer(layerId, layerName) {
        if (!this.layers.has(layerId)) return;
        
        const geojson = this.layers.get(layerId).toGeoJSON();
        const dataStr = "data:text/json;charset=utf-8," + 
            encodeURIComponent(JSON.stringify(geojson));
        
        const downloadLink = document.createElement('a');
        downloadLink.href = dataStr;
        downloadLink.download = `${layerName}.geojson`;
        document.body.appendChild(downloadLink);
        downloadLink.click();
        downloadLink.remove();
    }

    setupEventListeners() {
        const clearButton = document.getElementById('clearStats');
        if (clearButton) {
            clearButton.addEventListener('click', () => this.clearStatistics());
        }
    }

    clearStatistics() {
        const statsDiv = document.getElementById('attributes');
        const clearButton = document.getElementById('clearStats');

        statsDiv.innerHTML = '<div class="text-center text-gray-500 py-4">No feature selected</div>';
        clearButton.classList.add('hidden');
        LocalStorageManager.clearStatsFromLocalStorage();
    }
}