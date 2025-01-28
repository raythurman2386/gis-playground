import { BaseMap } from './components/BaseMap.js';
import { FireLayers } from './components/FireLayers.js';
import { CustomLayers } from './components/CustomLayers.js';
import { LayerControl } from './components/LayerControl.js';
import { LocalStorageManager } from './utils/LocalStorageManager.js';

document.addEventListener('DOMContentLoaded', () => {
    const baseMap = new BaseMap('map');
    const map = baseMap.getMap();
    const fireLayers = new FireLayers(map);
    const customLayers = new CustomLayers(map, fireLayers);

    new LayerControl(map, baseMap.getBaseMaps(), {...fireLayers.getLayers(), ...customLayers.layers});

    customLayers.loadAvailableLayers();
});