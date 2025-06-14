/**
 * LayerManager - Manages multiple chart layers (natal, transit, etc.)
 * Handles layer visibility, ordering, and state management
 */
class LayerManager {
  constructor() {
    this.layers = new Map();
    this.activeLayer = 'natal';
    this.listeners = new Set();
  }

  /**
   * Add a new layer to the manager
   * @param {string} name - Layer identifier (e.g., 'natal', 'transit')
   * @param {Object} config - Layer configuration
   */
  addLayer(name, config) {
    this.layers.set(name, {
      visible: config.visible || false,
      data: null,
      style: config.style || {},
      subLayers: config.subLayers || {}, // For nested toggles (AC/DC, IC/MC, parans)
      type: config.type || 'astro',
      order: config.order || 0,
      ...config
    });
    
    this.notifyListeners('layerAdded', { name, config });
    return this;
  }

  /**
   * Toggle layer visibility
   * @param {string} name - Layer name
   */
  toggleLayer(name) {
    const layer = this.layers.get(name);
    if (layer) {
      layer.visible = !layer.visible;
      this.notifyListeners('layerToggled', { name, visible: layer.visible });
    }
    return this;
  }

  /**
   * Toggle sub-layer visibility (e.g., AC/DC within transit layer)
   * @param {string} layerName - Parent layer name
   * @param {string} subLayerName - Sub-layer name
   */
  toggleSubLayer(layerName, subLayerName) {
    const layer = this.layers.get(layerName);
    if (layer && layer.subLayers) {
      layer.subLayers[subLayerName] = !layer.subLayers[subLayerName];
      this.notifyListeners('subLayerToggled', { 
        layerName, 
        subLayerName, 
        visible: layer.subLayers[subLayerName] 
      });
    }
    return this;
  }

  /**
   * Set layer data
   * @param {string} name - Layer name
   * @param {Object} data - Layer data
   */
  setLayerData(name, data) {
    const layer = this.layers.get(name);
    if (layer) {
      layer.data = data;
      this.notifyListeners('layerDataChanged', { name, data });
    }
    return this;
  }

  /**
   * Set layer visibility explicitly
   * @param {string} name - Layer name
   * @param {boolean} visible - Visibility state
   */
  setLayerVisible(name, visible) {
    const layer = this.layers.get(name);
    if (layer) {
      layer.visible = visible;
      this.notifyListeners('layerToggled', { name, visible });
    }
    return this;
  }

  /**
   * Get layer configuration
   * @param {string} name - Layer name
   */
  getLayer(name) {
    return this.layers.get(name);
  }

  /**
   * Get all visible layers ordered by display order
   */  getVisibleLayers() {
    return Array.from(this.layers.entries())
      .filter(([, layer]) => layer.visible && layer.data)
      .sort(([, a], [, b]) => a.order - b.order)
      .map(([name, layer]) => ({ name, ...layer }));
  }

  /**
   * Check if a layer is visible
   * @param {string} name - Layer name
   */
  isLayerVisible(name) {
    const layer = this.layers.get(name);
    return layer ? layer.visible : false;
  }

  /**
   * Check if a sub-layer is visible
   * @param {string} layerName - Parent layer name
   * @param {string} subLayerName - Sub-layer name
   */
  isSubLayerVisible(layerName, subLayerName) {
    const layer = this.layers.get(layerName);
    return layer && layer.visible && layer.subLayers[subLayerName];
  }

  /**
   * Get merged data from all visible layers
   */
  getMergedData() {
    const visibleLayers = this.getVisibleLayers();
    let mergedFeatures = [];

    visibleLayers.forEach(layer => {
      if (layer.data && layer.data.features) {
        // Add layer metadata to each feature
        const layerFeatures = layer.data.features.map(feature => ({
          ...feature,
          layerName: layer.name,
          layerStyle: layer.style,
          layerOrder: layer.order
        }));
        mergedFeatures = [...mergedFeatures, ...layerFeatures];
      }
    });

    return { features: mergedFeatures };
  }

  /**
   * Add event listener for layer changes
   * @param {Function} callback - Callback function
   */
  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  /**
   * Notify all listeners of changes
   * @param {string} event - Event type
   * @param {Object} data - Event data
   */
  notifyListeners(event, data) {
    this.listeners.forEach(callback => {
      try {
        callback(event, data);
      } catch (error) {
        console.error('LayerManager listener error:', error);
      }
    });
  }

  /**
   * Clear all layer data
   */
  clearAllData() {
    this.layers.forEach(layer => {
      layer.data = null;
    });
    this.notifyListeners('allDataCleared', {});
    return this;
  }

  /**
   * Get layer names
   */
  getLayerNames() {
    return Array.from(this.layers.keys());
  }
}

export default LayerManager;
