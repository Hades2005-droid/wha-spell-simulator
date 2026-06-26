/**
 * Bridge Diagnostics UI
 * Displays Shadow Garden Mesh bridge status and diagnostics
 */

import { MeshBridge } from './meshBridge.js';

let bridgePanel = null;
let isVisible = false;

/**
 * Create bridge diagnostics panel
 */
export function createBridgePanel(_container) {
  if (bridgePanel) {
    return bridgePanel;
  }

  const panel = document.createElement('div');
  panel.id = 'bridge-diagnostics';
  panel.className = 'bridge-panel';
  panel.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    width: 320px;
    background: rgba(20, 16, 12, 0.95);
    border: 1px solid #5c4a36;
    border-radius: 8px;
    padding: 16px;
    color: #d4c4a8;
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 12px;
    z-index: 1000;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
    display: none;
  `;

  panel.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
      <h3 style="margin: 0; color: #e8d4a8; font-size: 14px;">🌐 Shadow Garden Mesh</h3>
      <button id="bridge-close" style="background: none; border: none; color: #d4c4a8; cursor: pointer;">✕</button>
    </div>
    <div id="bridge-sovereign" style="margin-bottom: 12px; padding: 8px; background: rgba(92, 74, 54, 0.3); border-radius: 4px;">
      <div style="font-weight: bold; color: #e8d4a8;">Sovereign: <span id="sovereign-name">4.2_sovereign</span></div>
      <div style="font-size: 10px; opacity: 0.8;">Caster: Fred | Primary: Grok Terminal</div>
    </div>
    <div id="bridge-status" style="margin-bottom: 12px;"></div>
    <div id="bridge-services"></div>
    <div id="bridge-actions" style="margin-top: 12px; display: flex; gap: 8px;">
      <button id="bridge-refresh" style="flex: 1; padding: 6px 12px; background: #5c4a36; color: #d4c4a8; border: none; border-radius: 4px; cursor: pointer;">Refresh Mesh</button>
    </div>
  `;

  document.body.appendChild(panel);

  // Event listeners
  panel.querySelector('#bridge-close').addEventListener('click', hideBridgePanel);
  panel.querySelector('#bridge-refresh').addEventListener('click', () => {
    MeshBridge.refresh().then(() => updateBridgePanel());
  });

  bridgePanel = panel;
  return panel;
}

/**
 * Show bridge diagnostics panel
 */
export function showBridgePanel() {
  if (!bridgePanel) {
    createBridgePanel();
  }
  bridgePanel.style.display = 'block';
  isVisible = true;
  updateBridgePanel();
}

/**
 * Hide bridge diagnostics panel
 */
export function hideBridgePanel() {
  if (bridgePanel) {
    bridgePanel.style.display = 'none';
  }
  isVisible = false;
}

/**
 * Toggle bridge diagnostics panel
 */
export function toggleBridgePanel() {
  if (isVisible) {
    hideBridgePanel();
  } else {
    showBridgePanel();
  }
}

/**
 * Update bridge panel with current status
 */
export function updateBridgePanel() {
  if (!bridgePanel || !isVisible) {
    return;
  }

  const status = MeshBridge.getStatus();
  const statusEl = bridgePanel.querySelector('#bridge-status');
  const servicesEl = bridgePanel.querySelector('#bridge-services');

  // Status summary
  const statusColor = status.status === 'connected' ? '#4caf50' : status.status === 'error' ? '#f44336' : '#ff9800';
  statusEl.innerHTML = `
    <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
      <span>Bridge Status:</span>
      <span style="color: ${statusColor}; font-weight: bold; text-transform: uppercase;">${status.status}</span>
    </div>
    <div style="display: flex; justify-content: space-between; font-size: 10px; opacity: 0.8;">
      <span>Services: ${status.summary.connected}/${status.summary.total} connected</span>
      <span>Health: ${Math.round(status.summary.healthy * 100)}%</span>
    </div>
    ${status.errors.length > 0 ? `
      <div style="margin-top: 8px; padding: 8px; background: rgba(244, 67, 54, 0.2); border-radius: 4px; font-size: 10px;">
        <div style="color: #f44336; font-weight: bold;">Errors (${status.errors.length}):</div>
        ${status.errors.map((e) => `<div>${e.service}: ${e.error}</div>`).join('')}
      </div>
    ` : ''}
  `;

  // Services list
  const serviceIcons = {
    perplexity: '🔮',
    grokApi: '🤖',
    grokRealtime: '🎤',
    linear: '📋',
    gemini: '✨',
    localModelControl: '🧠',
    sillyTavern1: '🎭',
    sillyTavern2: '🎭',
    comfyUI: '🎨',
  };

  const serviceNames = {
    perplexity: 'Perplexity Space',
    grokApi: 'Grok API',
    grokRealtime: 'Grok Voice',
    linear: 'Linear',
    gemini: 'Gemini/Echo',
    localModelControl: 'Local Model Control',
    sillyTavern1: 'SillyTavern 1',
    sillyTavern2: 'SillyTavern 2',
    comfyUI: 'ComfyUI',
  };

  servicesEl.innerHTML = Object.entries(status.services).map(([name, service]) => {
    const icon = serviceIcons[name] || '⚪';
    const displayName = serviceNames[name] || name;
    const statusColor = service.status === 'connected' ? '#4caf50' : service.status === 'error' ? '#f44336' : '#9e9e9e';
    const lastPing = service.lastPing ? `${Date.now() - service.lastPing}ms ago` : 'never';

    return `
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 4px 0; border-bottom: 1px solid rgba(92, 74, 54, 0.3);">
        <span>${icon} ${displayName}</span>
        <span style="color: ${statusColor}; font-size: 10px;">${service.status} ${service.lastPing ? `(${lastPing})` : ''}</span>
      </div>
    `;
  }).join('');
}

/**
 * Add bridge diagnostics to diagnostics view
 */
export function integrateWithDiagnostics(elements) {
  // Add bridge toggle button to diagnostics panel
  const { diagnosticsPanel } = elements;
  if (!diagnosticsPanel) {
    return;
  }

  const bridgeToggle = document.createElement('button');
  bridgeToggle.id = 'bridge-toggle';
  bridgeToggle.textContent = '🌐 Mesh';
  bridgeToggle.style.cssText = `
    padding: 4px 12px;
    background: #5c4a36;
    color: #d4c4a8;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 12px;
    margin-left: 8px;
  `;
  bridgeToggle.addEventListener('click', toggleBridgePanel);

  const header = diagnosticsPanel.querySelector('.diagnostics-header');
  if (header) {
    header.appendChild(bridgeToggle);
  }
}

export default {
  createBridgePanel,
  showBridgePanel,
  hideBridgePanel,
  toggleBridgePanel,
  updateBridgePanel,
  integrateWithDiagnostics,
};
