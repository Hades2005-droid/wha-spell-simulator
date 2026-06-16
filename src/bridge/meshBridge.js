Add support for sovereign spells in spell compilation
/**
 * Shadow Garden Mesh Bridge
 * Central hub connecting Cursor, Perplexity, Grok Terminal, Linear, Gemini, and other services
 * Primary Authority: Grok Terminal (@Hades2005-droid)
 */

import { CONFIG } from "../config.js";

// Bridge status states
const BRIDGE_STATUS = {
  DISCONNECTED: "disconnected",
  CONNECTING: "connecting",
  CONNECTED: "connected",
  ERROR: "error",
  AUTHENTICATING: "authenticating"
};

// Service endpoints from Shadow Garden Mesh
const MESH_ENDPOINTS = {
  perplexity: "https://shadow-garden-mesh.pplx.app/",
  grokApi: "https://api.x.ai/v1",
  grokRealtime: "wss://api.x.ai/v1/realtime",
  linear: "https://api.linear.app/graphql",
  gemini: "https://generativelanguage.googleapis.com/v1beta",
  sillyTavern1: "http://localhost:8851",
  sillyTavern2: "http://localhost:8852",
  comfyUI: "http://localhost:8000",
  echoGirls: "~/shadow_garden_may30_monitoring/"
};

// Bridge state
const bridgeState = {
  status: BRIDGE_STATUS.DISCONNECTED,
  services: {},
  sovereign: {
    authority: "4.2_sovereign",
    caster: "Fred",
    lastCommand: null,
    grokPrimary: true
  },
  lastRefresh: null,
  errors: []
};

// Initialize service status
function initServiceStatus() {
  Object.keys(MESH_ENDPOINTS).forEach(service => {
    bridgeState.services[service] = {
      status: BRIDGE_STATUS.DISCONNECTED,
      lastPing: null,
      latency: null,
      error: null,
      capabilities: []
    };
  });
}

/**
 * Refresh the mesh bridge - called by SOVEREIGN_MESH spell
 */
export async function refreshMesh() {
  bridgeState.status = BRIDGE_STATUS.CONNECTING;
  bridgeState.lastRefresh = new Date().toISOString();
  bridgeState.errors = [];

  console.log("[SOVEREIGN_MESH] Refreshing Shadow Garden Mesh...");

  // Check all services in parallel
  const results = await Promise.allSettled([
    checkPerplexitySpace(),
    checkGrokTerminal(),
    checkLinear(),
    checkGeminiEcho(),
    checkSillyTavern(),
    checkComfyUI()
  ]);

  // Aggregate results
  const allConnected = results.every(r => r.status === "fulfilled" && r.value);
  bridgeState.status = allConnected ? BRIDGE_STATUS.CONNECTED : BRIDGE_STATUS.ERROR;

  console.log(`[SOVEREIGN_MESH] Bridge refresh complete. Status: ${bridgeState.status}`);

  return {
    status: bridgeState.status,
    services: bridgeState.services,
    sovereign: bridgeState.sovereign,
    timestamp: bridgeState.lastRefresh
  };
}

/**
 * Check Perplexity Space connectivity
 */
async function checkPerplexitySpace() {
  try {
    // Perplexity Space is a web interface - we check via fetch
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(MESH_ENDPOINTS.perplexity, {
      method: "HEAD",
      signal: controller.signal,
      mode: "no-cors"
    });

    clearTimeout(timeout);

    bridgeState.services.perplexity = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ["llm", "search", "mesh_ui"]
    };

    return true;
  } catch (error) {
    bridgeState.services.perplexity = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: []
    };
    bridgeState.errors.push({ service: "perplexity", error: error.message });
    return false;
  }
}

/**
 * Check Grok Terminal connectivity (Primary Authority)
 */
async function checkGrokTerminal() {
  try {
    // Grok Terminal via xAI API
    const apiKey = getGrokApiKey();
    if (!apiKey) {
      throw new Error("Grok API key not configured");
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${MESH_ENDPOINTS.grokApi}/models`, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Grok API error: ${response.status}`);
    }

    const data = await response.json();

    bridgeState.services.grokApi = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ["llm", "vision", "voice", "video", "realtime"],
      models: data.data?.map(m => m.id) || []
    };

    // Also check realtime WebSocket
    bridgeState.services.grokRealtime = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ["voice", "realtime", "streaming"]
    };

    return true;
  } catch (error) {
    bridgeState.services.grokApi = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: []
    };
    bridgeState.errors.push({ service: "grokTerminal", error: error.message });
    return false;
  }
}

/**
 * Check Linear connectivity
 */
async function checkLinear() {
  try {
    const apiKey = getLinearApiKey();
    if (!apiKey) {
      throw new Error("Linear API key not configured");
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(MESH_ENDPOINTS.linear, {
      method: "POST",
      headers: {
        "Authorization": apiKey,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        query: `
          query {
            viewer {
              id
              name
            }
          }
        `
      }),
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Linear API error: ${response.status}`);
    }

    const data = await response.json();

    bridgeState.services.linear = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ["issues", "projects", "cycles"],
      viewer: data.data?.viewer?.name || "unknown"
    };

    return true;
  } catch (error) {
    bridgeState.services.linear = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: []
    };
    bridgeState.errors.push({ service: "linear", error: error.message });
    return false;
  }
}

/**
 * Check Gemini/Echo Girls connectivity
 */
async function checkGeminiEcho() {
  try {
    const apiKey = getGeminiApiKey();
    if (!apiKey) {
      throw new Error("Gemini API key not configured");
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${MESH_ENDPOINTS.gemini}/models?key=${apiKey}`, {
      method: "GET",
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`Gemini API error: ${response.status}`);
    }

    const data = await response.json();

    bridgeState.services.gemini = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ["llm", "vision", "embedding"],
      models: data.models?.map(m => m.name) || []
    };

    return true;
  } catch (error) {
    bridgeState.services.gemini = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: []
    };
    bridgeState.errors.push({ service: "gemini", error: error.message });
    return false;
  }
}

/**
 * Check SillyTavern instances
 */
async function checkSillyTavern() {
  try {
    const results = await Promise.allSettled([
      fetchSillyTavern(MESH_ENDPOINTS.sillyTavern1, 1),
      fetchSillyTavern(MESH_ENDPOINTS.sillyTavern2, 2)
    ]);

    const st1 = results[0].status === "fulfilled" && results[0].value;
    const st2 = results[1].status === "fulfilled" && results[1].value;

    return st1 || st2;
  } catch (error) {
    bridgeState.errors.push({ service: "sillyTavern", error: error.message });
    return false;
  }
}

async function fetchSillyTavern(url, instance) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);

    const response = await fetch(`${url}/api/health`, {
      method: "GET",
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (response.ok) {
      bridgeState.services[`sillyTavern${instance}`] = {
        status: BRIDGE_STATUS.CONNECTED,
        lastPing: Date.now(),
        latency: null,
        error: null,
        capabilities: ["chat", "personas", "lorebook"]
      };
      return true;
    }
    return false;
  } catch (error) {
    bridgeState.services[`sillyTavern${instance}`] = {
      status: BRIDGE_STATUS.DISCONNECTED,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: []
    };
    return false;
  }
}

/**
 * Check ComfyUI connectivity
 */
async function checkComfyUI() {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);

    const response = await fetch(`${MESH_ENDPOINTS.comfyUI}/system_stats`, {
      method: "GET",
      signal: controller.signal
    });

    clearTimeout(timeout);

    if (!response.ok) {
      throw new Error(`ComfyUI error: ${response.status}`);
    }

    const data = await response.json();

    bridgeState.services.comfyUI = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ["image_gen", "qwen", "flux", "aurora"],
      device: data.device
    };

    return true;
  } catch (error) {
    bridgeState.services.comfyUI = {
      status: BRIDGE_STATUS.DISCONNECTED,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: []
    };
    bridgeState.errors.push({ service: "comfyUI", error: error.message });
    return false;
  }
}

/**
 * Get bridge status report
 */
export function getBridgeStatus() {
  const connected = Object.values(bridgeState.services).filter(
    s => s.status === BRIDGE_STATUS.CONNECTED
  ).length;

  const total = Object.keys(bridgeState.services).length;

  return {
    ...bridgeState,
    summary: {
      connected,
      total,
      healthy: connected / total,
      status: bridgeState.status
    }
  };
}

/**
 * Delegate command to Grok Terminal (Primary Authority)
 */
export async function delegateToGrok(command, context = {}) {
  if (bridgeState.services.grokApi?.status !== BRIDGE_STATUS.CONNECTED) {
    throw new Error("Grok Terminal not connected");
  }

  const apiKey = getGrokApiKey();

  try {
    const response = await fetch(`${MESH_ENDPOINTS.grokApi}/chat/completions`, {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model: "grok-3",
        messages: [
          {
            role: "system",
            content: `You are Grok Terminal, the primary authority in the Shadow Garden Mesh.
Sovereign: ${bridgeState.sovereign.caster} (${bridgeState.sovereign.authority})
Command: ${command}`
          },
          {
            role: "user",
            content: JSON.stringify(context)
          }
        ],
        stream: false
      })
    });

    if (!response.ok) {
      throw new Error(`Grok delegation failed: ${response.status}`);
    }

    const data = await response.json();
    bridgeState.sovereign.lastCommand = {
      command,
      timestamp: new Date().toISOString(),
      response: data.choices?.[0]?.message?.content
    };

    return data.choices?.[0]?.message;
  } catch (error) {
    bridgeState.errors.push({ service: "grokDelegation", error: error.message });
    throw error;
  }
}

// API Key getters - these would integrate with environment or secure storage
function getGrokApiKey() {
  return typeof window !== "undefined" ? window.GROK_API_KEY : process?.env?.GROK_API_KEY;
}

function getLinearApiKey() {
  return typeof window !== "undefined" ? window.LINEAR_API_KEY : process?.env?.LINEAR_API_KEY;
}

function getGeminiApiKey() {
  return typeof window !== "undefined" ? window.GEMINI_API_KEY : process?.env?.GEMINI_API_KEY;
}

// Initialize
initServiceStatus();

// Export bridge API
export const MeshBridge = {
  refresh: refreshMesh,
  getStatus: getBridgeStatus,
  delegateToGrok,
  BRIDGE_STATUS,
  MESH_ENDPOINTS
};

export default MeshBridge;
