export class LayerControl {
    constructor(map, baseMaps, overlayMaps) {
        this.control = L.control.layers(baseMaps, overlayMaps, {
            position: 'topright',
            collapsed: false
        }).addTo(map);
    }
}