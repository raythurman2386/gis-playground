import { LocalStorageManager } from '../utils/LocalStorageManager.js';

export class FireLayers {
    constructor(map) {
        this.map = map;
        this.initializeLayers();
        this.setupEventListeners();
    }

    initializeLayers() {
        this.wildfireIncidents = L.esri.featureLayer({
            url: 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/USA_Wildfires_v1/FeatureServer/0',
            pointToLayer: (feature, latlng) => this.styleFireIncident(feature, latlng)
        }).on('click mouseover', (e) => this.updateFireStatistics(e.layer.feature.properties, 'incident'));

        this.wildfirePerimeters = L.esri.featureLayer({
            url: 'https://services9.arcgis.com/RHVPKKiFTONKtxq3/arcgis/rest/services/USA_Wildfires_v1/FeatureServer/1',
            style: (feature) => this.styleFirePerimeter(feature)
        }).on('click mouseover', (e) => this.updateFireStatistics(e.layer.feature.properties, 'perimeter'));
    }

    styleFireIncident(feature, latlng) {
        return L.circleMarker(latlng, {
            radius: 8,
            fillColor: "#ff0000",
            color: "#000",
            weight: 1,
            opacity: 1,
            fillOpacity: 0.8
        });
    }

    styleFirePerimeter(feature) {
        return {
            fillColor: "#ff9900",
            weight: 2,
            opacity: 1,
            color: '#ff0000',
            fillOpacity: 0.7
        };
    }

    updateFireStatistics(properties, type) {
        LocalStorageManager.saveStatsToLocalStorage(properties, type);
        this.displayStatistics(properties, type);
    }

    displayStatistics(properties, type) {
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
            rowData = this.getFireIncidentData(properties);
        } else if (type === 'perimeter') {
            rowData = this.getFirePerimeterData(properties);
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

    getFireIncidentData(properties) {
        return [
            ['Fire Name', properties.IncidentName || 'Unknown'],
            ['Status', properties.IncidentStatus || 'Unknown'],
            ['Size', `${properties.DailyAcres ? properties.DailyAcres.toLocaleString() : 'Unknown'} acres`],
            ['Discovered', properties.FireDiscoveryDateTime ? new Date(properties.FireDiscoveryDateTime).toLocaleString() : 'Unknown'],
            ['Containment', `${properties.PercentContained || '0'}%`],
            ['Cause', properties.FireCause || 'Unknown'],
            ['Complex', properties.ComplexName || 'N/A'],
            ['Agency', properties.POOProtectingAgency || 'Unknown']
        ];
    }

    getFirePerimeterData(properties) {
        return [
            ['Fire Name', properties.IncidentName || 'Unknown'],
            ['Total Area', `${properties.GISAcres ? properties.GISAcres.toLocaleString() : 'Unknown'} acres`],
            ['Containment', `${properties.PercentContained || '0'}%`],
            ['Updated', properties.CreateDate ? new Date(properties.CreateDate).toLocaleString() : 'Unknown'],
            ['Complex', properties.ComplexName || 'N/A'],
            ['Type', properties.IncidentTypeCategory || 'Unknown']
        ];
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

        statsDiv.innerHTML = `
            <div class="text-center text-gray-500 py-4">
                No feature selected
            </div>
        `;
        clearButton.classList.add('hidden');

        LocalStorageManager.clearStatsFromLocalStorage();
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleString();
    }

    getLayers() {
        return {
            'Fire Incidents': this.wildfireIncidents,
            'Fire Perimeters': this.wildfirePerimeters
        };
    }
}