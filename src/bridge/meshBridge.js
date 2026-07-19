/**
 * Shadow Garden Mesh Bridge
 * Central hub connecting Cursor, Perplexity, Grok Terminal, Linear, Gemini, and other services
 * Primary Authority: Grok Terminal (@Hades2005-droid)
 */

import { CONFIG } from '../config.js';

// Bridge status states
const BRIDGE_STATUS = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  ERROR: 'error',
  AUTHENTICATING: 'authenticating',
};

// Service endpoints from Shadow Garden Mesh
const MESH_ENDPOINTS = {
  perplexity: 'https://shadow-garden-mesh.pplx.app/',
  perplexityApiBridge: 'http://127.0.0.1:8790/shadowgardencontrol/perplexity',
  grokApi: 'https://api.x.ai/v1',
  grokRealtime: 'wss://api.x.ai/v1/realtime',
  linear: 'https://api.linear.app/graphql',
  gemini: 'https://generativelanguage.googleapis.com/v1beta',
  localModelControl: 'http://127.0.0.1:8790/shadowgardencontrol',
  claudeCode: 'http://127.0.0.1:8790/shadowgardencontrol/claude',
  cometExtension: 'http://127.0.0.1:8790/shadowgardencontrol/extension',
  recursiveNodeBridge: 'http://127.0.0.1:8790/shadowgardencontrol/recursive',
  sillyTavern1: 'http://localhost:8851',
  sillyTavern2: 'http://localhost:8852',
  comfyUI: 'http://localhost:8000',
  echoGirls: '~/shadow_garden_may30_monitoring/',
};

// Bridge state
const bridgeState = {
  status: BRIDGE_STATUS.DISCONNECTED,
  services: {},
  sovereign: {
    authority: '4.2_sovereign',
    caster: 'Fred',
    lastCommand: null,
    grokPrimary: true,
  },
  lastRefresh: null,
  errors: [],
};

// Initialize service status
function initServiceStatus() {
  Object.keys(MESH_ENDPOINTS).forEach((service) => {
    bridgeState.services[service] = {
      status: BRIDGE_STATUS.DISCONNECTED,
      lastPing: null,
      latency: null,
      error: null,
      capabilities: [],
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

  console.log('[SOVEREIGN_MESH] Refreshing Shadow Garden Mesh...');

  // Check all services in parallel
  const results = await Promise.allSettled([
    checkPerplexitySpace(),
    checkPerplexityApiAdapter(),
    checkGrokTerminal(),
    checkLinear(),
    checkGeminiEcho(),
    checkLocalModelControl(),
    checkClaudeCode(),
    checkCometExtensionWorkspace(),
    checkRecursiveNodeBridge(),
    checkSillyTavern(),
    checkComfyUI(),
  ]);

  // Aggregate results
  const allConnected = results.every((r) => r.status === 'fulfilled' && r.value);
  bridgeState.status = allConnected ? BRIDGE_STATUS.CONNECTED : BRIDGE_STATUS.ERROR;

  console.log(`[SOVEREIGN_MESH] Bridge refresh complete. Status: ${bridgeState.status}`);

  return {
    status: bridgeState.status,
    services: bridgeState.services,
    sovereign: bridgeState.sovereign,
    timestamp: bridgeState.lastRefresh,
  };
}

function getConfiguredLocalModelEndpoint() {
  if (typeof window !== 'undefined') {
    return window.SHADOWGARDEN_CONTROL_URL || window.LOCAL_MODEL_CONTROL_URL || MESH_ENDPOINTS.localModelControl;
  }
  return process?.env?.SHADOWGARDEN_CONTROL_URL || process?.env?.LOCAL_MODEL_CONTROL_URL || MESH_ENDPOINTS.localModelControl;
}

function getConfiguredCometExtensionEndpoint() {
  if (typeof window !== 'undefined') {
    return window.SHADOWGARDEN_EXTENSION_STATUS_URL || window.COMET_EXTENSION_STATUS_URL || MESH_ENDPOINTS.cometExtension;
  }
  return process?.env?.SHADOWGARDEN_EXTENSION_STATUS_URL || process?.env?.COMET_EXTENSION_STATUS_URL || MESH_ENDPOINTS.cometExtension;
}

function buildLocalModelProbeUrls() {
  const configured = String(getConfiguredLocalModelEndpoint() || MESH_ENDPOINTS.localModelControl).trim();
  const withoutTrailingSlash = configured.replace(/\/+$/, '');
  const aliases = [withoutTrailingSlash];

  if (withoutTrailingSlash.includes('/shadowgardencontrol')) {
    aliases.push(withoutTrailingSlash.replace('/shadowgardencontrol', '/shadowgardencongrol'));
  }

  try {
    const { origin } = new URL(withoutTrailingSlash);
    aliases.push(origin);
  } catch {
    // keep configured URL only when parsing fails
  }

  const probePaths = ['', '/capabilities', '/models', '/v1/models', '/api/tags'];
  const urls = [];
  for (const base of aliases) {
    for (const path of probePaths) {
      const url = path ? `${base}${path}` : base;
      if (!urls.includes(url)) {
        urls.push(url);
      }
    }
  }
  return urls;
}

async function fetchJsonWithTimeout(url, timeoutMs = 3500) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const startedAt = Date.now();

  try {
    const response = await fetch(url, {
      method: 'GET',
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();
    return {
      data,
      latency: Date.now() - startedAt,
    };
  } finally {
    clearTimeout(timeout);
  }
}

function normalizedArray(value) {
  if (!Array.isArray(value)) {
    return [];
  }
  return value
    .map((item) => (typeof item === 'string' ? item.trim() : ''))
    .filter(Boolean);
}

function extractModelIds(payload) {
  const openAIModels = Array.isArray(payload?.data)
    ? payload.data.map((model) => model?.id).filter(Boolean)
    : [];
  const listedModels = Array.isArray(payload?.models)
    ? payload.models.map((model) => (typeof model === 'string' ? model : model?.id || model?.name)).filter(Boolean)
    : [];
  const taggedModels = Array.isArray(payload?.tags)
    ? payload.tags.map((model) => model?.name || model?.id).filter(Boolean)
    : [];
  return [...new Set([...openAIModels, ...listedModels, ...taggedModels])];
}

function inferCapabilitiesFromModels(modelIds) {
  const capabilities = new Set();
  if (modelIds.length) {
    capabilities.add('llm');
  }

  for (const modelId of modelIds) {
    const id = String(modelId).toLowerCase();
    if (id.includes('vision') || id.includes('vl') || id.includes('multimodal')) {
      capabilities.add('vision');
    }
    if (id.includes('embed')) {
      capabilities.add('embedding');
    }
    if (id.includes('whisper') || id.includes('tts') || id.includes('audio') || id.includes('voice')) {
      capabilities.add('voice');
    }
    if (id.includes('rerank')) {
      capabilities.add('reranking');
    }
  }

  return capabilities;
}

function extractLocalModelCapabilities(payload) {
  const capabilities = new Set([
    ...normalizedArray(payload?.capabilities),
    ...normalizedArray(payload?.features),
    ...normalizedArray(payload?.modalities),
    ...normalizedArray(payload?.tools),
  ]);
  const models = extractModelIds(payload);

  for (const inferred of inferCapabilitiesFromModels(models)) {
    capabilities.add(inferred);
  }

  capabilities.add('local_control');

  return {
    capabilities: [...capabilities].sort(),
    models,
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
      method: 'HEAD',
      signal: controller.signal,
      mode: 'no-cors',
    });

    clearTimeout(timeout);

    bridgeState.services.perplexity = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ['llm', 'search', 'mesh_ui'],
    };

    return true;
  } catch (error) {
    bridgeState.services.perplexity = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: [],
    };
    bridgeState.errors.push({ service: 'perplexity', error: error.message });
    return false;
  }
}

function getConfiguredPerplexityAdapterEndpoint() {
  if (typeof window !== 'undefined') {
    return window.SHADOWGARDEN_PERPLEXITY_URL
      || window.PERPLEXITY_API_BRIDGE_URL
      || MESH_ENDPOINTS.perplexityApiBridge;
  }
  return process?.env?.SHADOWGARDEN_PERPLEXITY_URL
    || process?.env?.PERPLEXITY_API_BRIDGE_URL
    || MESH_ENDPOINTS.perplexityApiBridge;
}

function mapPerplexityAdapterStatus(laneStatus) {
  if (laneStatus === 'ready' || laneStatus === 'dry_run_ready' || laneStatus === 'review_complete') {
    return BRIDGE_STATUS.CONNECTED;
  }
  if (laneStatus === 'dry_run_api_key_missing' || laneStatus === 'blocked_api_key_missing') {
    return BRIDGE_STATUS.AUTHENTICATING;
  }
  return BRIDGE_STATUS.ERROR;
}

function normalizePerplexityAdapterService(data, endpoint, latency = null) {
  const laneStatus = data?.status || 'unknown';
  const serviceStatus = mapPerplexityAdapterStatus(laneStatus);
  return {
    status: serviceStatus,
    lastPing: Date.now(),
    latency,
    error: serviceStatus === BRIDGE_STATUS.CONNECTED || serviceStatus === BRIDGE_STATUS.AUTHENTICATING
      ? null
      : laneStatus,
    endpoint,
    laneStatus,
    apiKeyPresent: data?.api_key_present === true,
    localOnlyHandoff: data?.local_only_handoff !== false,
    browserAutomation: data?.browser_automation === true,
    broadcastToAgents: data?.broadcast_to_agents === true,
    model: data?.model || null,
    guardrails: Array.isArray(data?.guardrails) ? data.guardrails : [],
    capabilities: ['perplexity_api_review', 'local_mesh_context', 'redacted_status'],
  };
}

async function checkPerplexityApiAdapter() {
  const configured = String(getConfiguredPerplexityAdapterEndpoint() || '').replace(/\/+$/, '');
  const base = String(getConfiguredLocalModelEndpoint() || '').replace(/\/+$/, '');
  const probeUrls = [...new Set([
    `${base}/perplexity/status`,
    `${base}/perplexity`,
    configured,
  ].filter(Boolean))];

  let lastError = null;
  for (const url of probeUrls) {
    try {
      const { data, latency } = await fetchJsonWithTimeout(url, 3500);
      bridgeState.services.perplexityApiBridge = normalizePerplexityAdapterService(data, url, latency);
      return bridgeState.services.perplexityApiBridge.status === BRIDGE_STATUS.CONNECTED
        || bridgeState.services.perplexityApiBridge.status === BRIDGE_STATUS.AUTHENTICATING;
    } catch (error) {
      lastError = error;
    }
  }

  bridgeState.services.perplexityApiBridge = {
    status: BRIDGE_STATUS.DISCONNECTED,
    lastPing: null,
    latency: null,
    error: lastError?.message || 'local Perplexity API adapter unavailable',
    endpoint: MESH_ENDPOINTS.perplexityApiBridge,
    capabilities: [],
  };
  bridgeState.errors.push({
    service: 'perplexityApiBridge',
    error: bridgeState.services.perplexityApiBridge.error,
  });
  return false;
}

/**
 * Check Grok Terminal connectivity (Primary Authority)
 */
async function checkGrokTerminal() {
  try {
    // Grok Terminal via xAI API
    const apiKey = getGrokApiKey();
    if (!apiKey) {
      throw new Error('Grok API key not configured');
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 10000);

    const response = await fetch(`${MESH_ENDPOINTS.grokApi}/models`, {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      signal: controller.signal,
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
      capabilities: ['llm', 'vision', 'voice', 'video', 'realtime'],
      models: data.data?.map((m) => m.id) || [],
    };

    // Also check realtime WebSocket
    bridgeState.services.grokRealtime = {
      status: BRIDGE_STATUS.CONNECTED,
      lastPing: Date.now(),
      latency: null,
      error: null,
      capabilities: ['voice', 'realtime', 'streaming'],
    };

    return true;
  } catch (error) {
    bridgeState.services.grokApi = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: [],
    };
    bridgeState.errors.push({ service: 'grokTerminal', error: error.message });
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
      throw new Error('Linear API key not configured');
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(MESH_ENDPOINTS.linear, {
      method: 'POST',
      headers: {
        Authorization: apiKey,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        query: `
          query {
            viewer {
              id
              name
            }
          }
        `,
      }),
      signal: controller.signal,
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
      capabilities: ['issues', 'projects', 'cycles'],
      viewer: data.data?.viewer?.name || 'unknown',
    };

    return true;
  } catch (error) {
    bridgeState.services.linear = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: [],
    };
    bridgeState.errors.push({ service: 'linear', error: error.message });
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
      throw new Error('Gemini API key not configured');
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);

    const response = await fetch(`${MESH_ENDPOINTS.gemini}/models?key=${apiKey}`, {
      method: 'GET',
      signal: controller.signal,
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
      capabilities: ['llm', 'vision', 'embedding'],
      models: data.models?.map((m) => m.name) || [],
    };

    return true;
  } catch (error) {
    bridgeState.services.gemini = {
      status: BRIDGE_STATUS.ERROR,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: [],
    };
    bridgeState.errors.push({ service: 'gemini', error: error.message });
    return false;
  }
}

/**
 * Check local Shadow Garden Control / model capability service
 */
async function checkLocalModelControl() {
  const probeUrls = buildLocalModelProbeUrls();
  let lastError = null;

  for (const url of probeUrls) {
    try {
      const { data, latency } = await fetchJsonWithTimeout(url);
      const { capabilities, models } = extractLocalModelCapabilities(data);

      bridgeState.services.localModelControl = {
        status: BRIDGE_STATUS.CONNECTED,
        lastPing: Date.now(),
        latency,
        error: null,
        endpoint: url,
        capabilities,
        models,
      };

      return true;
    } catch (error) {
      lastError = error;
    }
  }

  bridgeState.services.localModelControl = {
    status: BRIDGE_STATUS.DISCONNECTED,
    lastPing: null,
    latency: null,
    error: lastError?.message || 'local model control endpoint unavailable',
    endpoint: getConfiguredLocalModelEndpoint(),
    capabilities: [],
  };
  bridgeState.errors.push({
    service: 'localModelControl',
    error: bridgeState.services.localModelControl.error,
  });
  return false;
}

/**
 * Check Claude Code Shadow Garden cloud lane connectivity.
 *
 * Reads the local status file emitted by tools/claude_shadowgarden.py through
 * the Shadow Garden Control endpoint. In pure-browser contexts without that
 * endpoint, marks the service as disconnected with a helpful error.
 */
async function checkClaudeCode() {
  const base = String(getConfiguredLocalModelEndpoint() || '').replace(/\/+$/, '');
  const probeUrls = [
    `${base}/claude/status`,
    `${base}/claude`,
    MESH_ENDPOINTS.claudeCode,
  ].filter(Boolean);

  let lastError = null;
  for (const url of probeUrls) {
    try {
      const { data, latency } = await fetchJsonWithTimeout(url, 3500);
      const status = data?.status || 'unknown';
      const capabilities = Array.isArray(data?.capabilities) && data.capabilities.length
        ? data.capabilities
        : ['code', 'tool_use', 'long_context'];

      bridgeState.services.claudeCode = {
        status: status === 'dry_run' || status === 'live_ok'
          ? BRIDGE_STATUS.CONNECTED
          : BRIDGE_STATUS.ERROR,
        lastPing: Date.now(),
        latency,
        error: status.startsWith('blocked') || status === 'live_failed' ? status : null,
        endpoint: url,
        capabilities,
        model: data?.model || null,
        session: data?.session_label || null,
        laneStatus: status,
        dryRun: Boolean(data?.dry_run),
      };
      return bridgeState.services.claudeCode.status === BRIDGE_STATUS.CONNECTED;
    } catch (error) {
      lastError = error;
    }
  }

  bridgeState.services.claudeCode = {
    status: BRIDGE_STATUS.DISCONNECTED,
    lastPing: null,
    latency: null,
    error: lastError?.message || 'claude shadowgarden lane unavailable',
    endpoint: MESH_ENDPOINTS.claudeCode,
    capabilities: [],
  };
  bridgeState.errors.push({
    service: 'claudeCode',
    error: bridgeState.services.claudeCode.error,
  });
  return false;
}

function mapCometExtensionStatus(laneStatus) {
  if (laneStatus === 'ready') {
    return BRIDGE_STATUS.CONNECTED;
  }
  if (laneStatus === 'blocked_lawful_confirmation_required') {
    return BRIDGE_STATUS.AUTHENTICATING;
  }
  if (String(laneStatus || '').startsWith('not_ready')) {
    return BRIDGE_STATUS.DISCONNECTED;
  }
  return BRIDGE_STATUS.ERROR;
}

function buildCometExtensionReviewPrompt(status = {}) {
  const repo = status.repo?.url || 'https://github.com/webLiang/Pornhub-Video-Downloader-Plugin-v3.git';
  const workspace = status.workspace?.path || 'unconfigured';
  const laneStatus = status.status || 'unknown';
  const manager = status.package?.manager || 'unknown';
  return [
    'Perplexity review brief for the Comet browser-extension workspace.',
    `Repository: ${repo}`,
    `Workspace: ${workspace}`,
    `Lane status: ${laneStatus}`,
    `Package manager: ${manager}`,
    'Review Manifest V3 compatibility, Comet/Chromium unpacked loading, permissions, injected scripts, downloads behavior, build/test risks, and lawful-use guardrails.',
    'Boundary: docs-only review; do not generate downloader logic, bypass instructions, or automated download workflows.',
  ].join('\n');
}

function normalizeCometExtensionService(data, endpoint, latency = null) {
  const laneStatus = data?.status || 'unknown';
  const serviceStatus = mapCometExtensionStatus(laneStatus);
  const capabilities = Array.isArray(data?.capabilities) && data.capabilities.length
    ? data.capabilities
    : ['browser_extension', 'comet', 'chromium', 'manifest_v3', 'local_workspace', 'perplexity_review'];
  return {
    status: serviceStatus,
    lastPing: Date.now(),
    latency,
    error: serviceStatus === BRIDGE_STATUS.CONNECTED ? null : laneStatus,
    endpoint,
    capabilities,
    laneStatus,
    workspace: data?.workspace?.path || null,
    distPath: data?.dist?.path || null,
    legalGate: data?.legalGate || null,
    riskFlags: Array.isArray(data?.riskFlags) ? data.riskFlags : [],
    routeHints: Array.isArray(data?.routeHints) ? data.routeHints : [],
    reviewPromptPath: data?.reviewPromptPath || null,
    cometCompatibility: data?.cometCompatibility || null,
    cometVerified: data?.cometCompatibility?.verifiedInComet === true,
    bundledArtifacts: Array.isArray(data?.artifacts?.bundledCrxOrPem)
      ? data.artifacts.bundledCrxOrPem
      : [],
    quarantineRequired: data?.artifacts?.quarantineRequired === true,
    perplexityReviewPrompt: data?.perplexityReviewPrompt || buildCometExtensionReviewPrompt(data),
  };
}

async function checkCometExtensionWorkspace() {
  const configured = String(getConfiguredCometExtensionEndpoint() || '').replace(/\/+$/, '');
  const base = String(getConfiguredLocalModelEndpoint() || '').replace(/\/+$/, '');
  const probeUrls = [
    `${base}/extension/status`,
    `${base}/extension`,
    configured,
  ].filter(Boolean);

  let lastError = null;
  for (const url of [...new Set(probeUrls)]) {
    try {
      const { data, latency } = await fetchJsonWithTimeout(url, 3500);
      bridgeState.services.cometExtension = normalizeCometExtensionService(data, url, latency);
      return bridgeState.services.cometExtension.status === BRIDGE_STATUS.CONNECTED;
    } catch (error) {
      lastError = error;
    }
  }

  bridgeState.services.cometExtension = {
    status: BRIDGE_STATUS.DISCONNECTED,
    lastPing: null,
    latency: null,
    error: lastError?.message || 'comet extension workspace status unavailable',
    endpoint: MESH_ENDPOINTS.cometExtension,
    capabilities: [],
  };
  bridgeState.errors.push({
    service: 'cometExtension',
    error: bridgeState.services.cometExtension.error,
  });
  return false;
}

function mapRecursiveNodeBridgeStatus(laneStatus) {
  if (laneStatus === 'ready' || laneStatus === 'running') {
    return BRIDGE_STATUS.CONNECTED;
  }
  if (laneStatus === 'stopped' || laneStatus === 'blocked') {
    return BRIDGE_STATUS.DISCONNECTED;
  }
  return BRIDGE_STATUS.ERROR;
}

function normalizeRecursiveNodeBridgeService(data, endpoint, latency = null) {
  const laneStatus = data?.status || 'unknown';
  const route = data?.route || {};
  return {
    status: mapRecursiveNodeBridgeStatus(laneStatus),
    lastPing: Date.now(),
    latency,
    error: laneStatus === 'ready' || laneStatus === 'running' ? null : laneStatus,
    endpoint,
    laneStatus,
    localOnly: data?.local_only !== false,
    symbolicOnly: data?.symbolic_only !== false,
    routeName: route.name || data?.config?.route_name || 'local-open-weights',
    routeModel: route.model || data?.config?.route_model || 'deepseek-local',
    routeEnabled: route.enabled === true,
    guardrails: Array.isArray(data?.guardrails) ? data.guardrails : [],
    capabilities: Array.isArray(data?.capabilities) && data.capabilities.length
      ? data.capabilities
      : ['recursive_node_evolution', 'chronology_engine', 'local_open_weights', 'deepseek_metadata'],
  };
}

async function checkRecursiveNodeBridge() {
  const configured = String(
    (typeof window !== 'undefined'
      ? window.SHADOWGARDEN_RECURSIVE_NODE_URL || window.RECURSIVE_NODE_BRIDGE_URL
      : process?.env?.SHADOWGARDEN_RECURSIVE_NODE_URL || process?.env?.RECURSIVE_NODE_BRIDGE_URL)
      || MESH_ENDPOINTS.recursiveNodeBridge,
  ).replace(/\/+$/, '');
  const base = String(getConfiguredLocalModelEndpoint() || '').replace(/\/+$/, '');
  const probeUrls = [...new Set([
    `${base}/recursive/status`,
    `${base}/recursive`,
    configured,
  ].filter(Boolean))];

  let lastError = null;
  for (const url of probeUrls) {
    try {
      const { data, latency } = await fetchJsonWithTimeout(url, 3500);
      bridgeState.services.recursiveNodeBridge = normalizeRecursiveNodeBridgeService(data, url, latency);
      return bridgeState.services.recursiveNodeBridge.status === BRIDGE_STATUS.CONNECTED;
    } catch (error) {
      lastError = error;
    }
  }

  bridgeState.services.recursiveNodeBridge = {
    status: BRIDGE_STATUS.DISCONNECTED,
    lastPing: null,
    latency: null,
    error: lastError?.message || 'recursive node bridge unavailable',
    endpoint: MESH_ENDPOINTS.recursiveNodeBridge,
    capabilities: [],
  };
  bridgeState.errors.push({
    service: 'recursiveNodeBridge',
    error: bridgeState.services.recursiveNodeBridge.error,
  });
  return false;
}

function getClaudeApiKey() {
  if (typeof window !== 'undefined') {
    return window.ANTHROPIC_API_KEY || window.CLAUDE_API_KEY || null;
  }
  return process?.env?.ANTHROPIC_API_KEY || process?.env?.CLAUDE_API_KEY || null;
}

function getAnthropicOAuthToken() {
  if (typeof window !== 'undefined') {
    return window.ANTHROPIC_OAUTH_TOKEN || null;
  }
  return process?.env?.ANTHROPIC_OAUTH_TOKEN || null;
}

function getAnthropicApiKeyId() {
  if (typeof window !== 'undefined') {
    return window.ANTHROPIC_API_KEY_ID || null;
  }
  return process?.env?.ANTHROPIC_API_KEY_ID || null;
}

/**
 * Verify a Claude API key's metadata via the Anthropic Admin API using an
 * OAuth Bearer token. Mirrors:
 *
 *   curl https://api.anthropic.com/v1/organizations/api_keys/$API_KEY_ID \
 *        -H 'anthropic-version: 2023-06-01' \
 *        -H "Authorization: Bearer $ANTHROPIC_OAUTH_TOKEN"
 *
 * Returns a redacted summary; never echoes the token or key value. Also
 * updates bridgeState.services.claudeCode.adminKeyCheck for the diagnostics UI.
 */
export async function verifyClaudeAdminKey({ apiKeyId, oauthToken } = {}) {
  const keyId = apiKeyId || getAnthropicApiKeyId();
  const oauth = oauthToken || getAnthropicOAuthToken();

  if (!keyId || !oauth) {
    const result = {
      checked: false,
      reason: 'ANTHROPIC_OAUTH_TOKEN / ANTHROPIC_API_KEY_ID not set',
    };
    if (bridgeState.services.claudeCode) {
      bridgeState.services.claudeCode.adminKeyCheck = result;
    }
    return result;
  }

  const url = `https://api.anthropic.com/v1/organizations/api_keys/${encodeURIComponent(keyId)}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);

  try {
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'anthropic-version': '2023-06-01',
        Authorization: `Bearer ${oauth}`,
        Accept: 'application/json',
      },
      signal: controller.signal,
    });
    clearTimeout(timeout);

    let payload = {};
    try {
      payload = await response.json();
    } catch {
      payload = {};
    }

    const result = {
      checked: true,
      ok: response.ok,
      httpStatus: response.status,
      keyId: payload?.id || keyId,
      name: payload?.name || null,
      status: payload?.status || null,
      workspaceId: payload?.workspace_id || null,
      createdAt: payload?.created_at || null,
      partialKeyHint: payload?.partial_key_hint || null,
    };

    if (bridgeState.services.claudeCode) {
      bridgeState.services.claudeCode.adminKeyCheck = result;
    }
    return result;
  } catch (error) {
    clearTimeout(timeout);
    const result = { checked: true, ok: false, error: error.message };
    if (bridgeState.services.claudeCode) {
      bridgeState.services.claudeCode.adminKeyCheck = result;
    }
    bridgeState.errors.push({ service: 'claudeAdminKey', error: error.message });
    return result;
  }
}

function buildClaudeSystemPrompt(command, activity) {
  return [
    'You are Claude Code operating inside the Shadow Garden mesh.',
    `Sovereign: ${bridgeState.sovereign.caster} (${bridgeState.sovereign.authority}).`,
    'Grok Terminal remains sovereign for media generation; you are the code /',
    'tool-use authority. Coordinate with the Devin and Perplexity lanes.',
    `Activity: ${activity}`,
    `Command: ${command}`,
    'Boundary: never inline secrets, prefer argv-style command plans, and emit',
    'structured diffs suitable for the mesh bridge diagnostics UI.',
  ].join(' ');
}

/**
 * Delegate a command to the Claude Code cloud environment.
 * Uses the Anthropic Messages API shape by default; the actual endpoint may be
 * fronted by the Shadow Garden Control proxy.
 */
export async function delegateToClaude(command, context = {}) {
  if (bridgeState.services.claudeCode?.status !== BRIDGE_STATUS.CONNECTED) {
    throw new Error('Claude Code shadowgarden lane not connected');
  }

  const apiKey = getClaudeApiKey();
  if (!apiKey) {
    throw new Error('Claude API key not configured (ANTHROPIC_API_KEY / CLAUDE_API_KEY)');
  }

  const activity = detectShadowGardenActivity(command, context);
  const model = context.model
    || bridgeState.services.claudeCode.model
    || (typeof window !== 'undefined' ? window.CLAUDE_MODEL : process?.env?.CLAUDE_MODEL)
    || 'claude-sonnet-4-5';
  const endpoint = context.endpoint
    || (typeof window !== 'undefined' ? window.CLAUDE_ENDPOINT : process?.env?.CLAUDE_ENDPOINT)
    || 'https://api.anthropic.com/v1/messages';
  const normalizedPrompt = normalizeShadowGardenPrompt(
    context.prompt || context.userPrompt || command,
  );

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers: {
        'x-api-key': apiKey,
        'anthropic-version': '2023-06-01',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        max_tokens: context.maxTokens || 4096,
        system: buildClaudeSystemPrompt(command, activity),
        messages: [
          {
            role: 'user',
            content: JSON.stringify({
              ...context,
              prompt: normalizedPrompt,
              promptHandling: { activity, model, normalizedPrompt },
            }),
          },
        ],
      }),
    });

    if (!response.ok) {
      throw new Error(`Claude delegation failed: ${response.status}`);
    }

    const data = await response.json();
    bridgeState.sovereign.lastCommand = {
      command,
      activity,
      provider: 'claudeCode',
      model,
      timestamp: new Date().toISOString(),
      response: data.content?.[0]?.text || null,
    };

    return data;
  } catch (error) {
    bridgeState.errors.push({ service: 'claudeDelegation', error: error.message });
    throw error;
  }
}

/**
 * Check SillyTavern instances
 */
async function checkSillyTavern() {
  try {
    const results = await Promise.allSettled([
      fetchSillyTavern(MESH_ENDPOINTS.sillyTavern1, 1),
      fetchSillyTavern(MESH_ENDPOINTS.sillyTavern2, 2),
    ]);

    const st1 = results[0].status === 'fulfilled' && results[0].value;
    const st2 = results[1].status === 'fulfilled' && results[1].value;

    return st1 || st2;
  } catch (error) {
    bridgeState.errors.push({ service: 'sillyTavern', error: error.message });
    return false;
  }
}

async function fetchSillyTavern(url, instance) {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 3000);

    const response = await fetch(`${url}/api/health`, {
      method: 'GET',
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (response.ok) {
      bridgeState.services[`sillyTavern${instance}`] = {
        status: BRIDGE_STATUS.CONNECTED,
        lastPing: Date.now(),
        latency: null,
        error: null,
        capabilities: ['chat', 'personas', 'lorebook'],
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
      capabilities: [],
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
      method: 'GET',
      signal: controller.signal,
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
      capabilities: ['image_gen', 'qwen', 'flux', 'aurora'],
      device: data.device,
    };

    return true;
  } catch (error) {
    bridgeState.services.comfyUI = {
      status: BRIDGE_STATUS.DISCONNECTED,
      lastPing: null,
      latency: null,
      error: error.message,
      capabilities: [],
    };
    bridgeState.errors.push({ service: 'comfyUI', error: error.message });
    return false;
  }
}

/**
 * Get bridge status report
 */
export function getBridgeStatus() {
  const connected = Object.values(bridgeState.services).filter(
    (s) => s.status === BRIDGE_STATUS.CONNECTED,
  ).length;

  const total = Object.keys(bridgeState.services).length;

  return {
    ...bridgeState,
    summary: {
      connected,
      total,
      healthy: connected / total,
      status: bridgeState.status,
    },
  };
}

function normalizeShadowGardenPrompt(value) {
  return String(value ?? '')
    .replace(/\s+/g, ' ')
    .trim();
}

function getPromptIntentModel(activity, family = 'general') {
  const modelByActivity = {
    text: 'GROK_TEXT_MODEL',
    image: 'GROK_IMAGE_MODEL',
    video: 'GROK_VIDEO_MODEL',
    audio: 'GROK_AUDIO_MODEL',
    voice: 'GROK_VOICE_MODEL',
  };
  const familyByKey = {
    qwen3: 'GROK_QWEN3_MODEL',
    qwen2: 'GROK_QWEN2_MODEL',
    qwen: 'GROK_QWEN_MODEL',
  };
  const key = familyByKey[family] || modelByActivity[activity] || modelByActivity.text;

  if (typeof window !== 'undefined') {
    return window[key] || window.GROK_MODEL || 'grok-3';
  }
  return process?.env?.[key] || process?.env?.GROK_MODEL || 'grok-3';
}

function detectShadowGardenActivity(command, context = {}) {
  const explicit = normalizeShadowGardenPrompt(context.activity || context.mode || '');
  if (['text', 'image', 'video', 'audio', 'voice'].includes(explicit)) {
    return explicit;
  }

  const source = normalizeShadowGardenPrompt([command, context.prompt, context.userPrompt].filter(Boolean).join(' ')).toLowerCase();
  const score = {
    video: 0,
    audio: 0,
    image: 0,
    voice: 0,
  };
  const keywordMap = {
    video: ['video', 'cinematic', 'animation', 'clip', 'trailer', 'scene'],
    audio: ['audio', 'music', 'sfx', 'soundtrack', 'sound design', 'mix'],
    image: ['image', 'illustration', 'render', 'poster', 'visual', 'portrait'],
    voice: ['voice', 'dialogue', 'narration', 'tts', 'spoken'],
  };

  for (const [activity, keywords] of Object.entries(keywordMap)) {
    for (const keyword of keywords) {
      if (source.includes(keyword)) {
        score[activity] += 1;
      }
    }
  }

  const top = Object.entries(score).sort((a, b) => b[1] - a[1])[0];
  return top?.[1] > 0 ? top[0] : 'text';
}

function detectLocalModelFamily(command, context = {}) {
  const source = normalizeShadowGardenPrompt([command, context.prompt, context.userPrompt, context.model].filter(Boolean).join(' ')).toLowerCase();
  if (source.includes('qwen3') || source.includes('qen3')) {
    return 'qwen3';
  }
  if (source.includes('qwen2') || source.includes('qwen 2') || source.includes('2qwen')) {
    return 'qwen2';
  }
  if (source.includes('qwen')) {
    return 'qwen';
  }
  return 'general';
}

function buildPerplexityReviewPrompt(command, activity, family, model) {
  const subject = normalizeShadowGardenPrompt(command);
  const familyLine = family === 'qwen3'
    ? 'Focus on Qwen3 local model behavior, routing, prompt shaping, and output quality.'
    : family === 'qwen2'
      ? 'Focus on Qwen2 local model behavior, routing, prompt shaping, and output quality.'
      : family === 'qwen'
        ? 'Focus on Qwen-family local model behavior, routing, prompt shaping, and output quality.'
        : 'Focus on the current local model process behavior, routing, prompt shaping, and output quality.';

  return [
    'Perplexity review brief for Shadow Garden local-model refinement.',
    `Activity: ${activity}`,
    `Model: ${model}`,
    `Family: ${family}`,
    familyLine,
    'Please analyze plain-text prompt handling, intent detection, model selection, failure modes, and ways to improve image/audio/video/voice generation handoff.',
    'Return actionable recommendations, edge cases, and a short checklist for validation.',
    `Source prompt: ${subject}`,
  ].join('\n');
}

function buildShadowGardenSystemPrompt(command, activity) {
  const activityInstruction = {
    image: 'Convert plain-text user intent into an image generation brief with composition, style, lighting, camera/lens framing, and quality constraints.',
    video: 'Convert plain-text user intent into a video generation brief with timeline beats, shot list, camera motion, transitions, continuity, and quality constraints.',
    audio: 'Convert plain-text user intent into an audio generation brief with sonic palette, timing, layers, pacing, and mastering constraints.',
    voice: 'Convert plain-text user intent into a voice generation brief with persona, delivery, pacing, pronunciation cues, and recording constraints.',
    text: 'Convert plain-text user intent into a structured production brief suitable for downstream generation agents.',
  }[activity] || 'Convert plain-text user intent into a structured production brief.';

  return `You are Grok Terminal, the primary authority in the Shadow Garden Mesh.
Sovereign: ${bridgeState.sovereign.caster} (${bridgeState.sovereign.authority})
Activity: ${activity}
Command: ${command}
Instruction: ${activityInstruction}
Boundary: Consent-safe, non-explicit output; keep tone cinematic and technical.`;
}

/**
 * Delegate command to Grok Terminal (Primary Authority)
 */
export async function delegateToGrok(command, context = {}) {
  if (bridgeState.services.grokApi?.status !== BRIDGE_STATUS.CONNECTED) {
    throw new Error('Grok Terminal not connected');
  }

  const apiKey = getGrokApiKey();
  const activity = detectShadowGardenActivity(command, context);
  const localModelFamily = detectLocalModelFamily(command, context);
  const model = getPromptIntentModel(activity, localModelFamily);
  const normalizedPrompt = normalizeShadowGardenPrompt(context.prompt || context.userPrompt || command);
  const perplexityPrompt = buildPerplexityReviewPrompt(command, activity, localModelFamily, model);

  try {
    const response = await fetch(`${MESH_ENDPOINTS.grokApi}/chat/completions`, {
      method: 'POST',
      headers: {
        Authorization: `Bearer ${apiKey}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: 'system',
            content: buildShadowGardenSystemPrompt(command, activity),
          },
          {
            role: 'user',
            content: JSON.stringify({
              ...context,
              prompt: normalizedPrompt,
              promptHandling: {
                activity,
                localModelFamily,
                model,
                normalizedPrompt,
                perplexityPrompt,
              },
            }),
          },
        ],
        stream: false,
      }),
    });

    if (!response.ok) {
      throw new Error(`Grok delegation failed: ${response.status}`);
    }

    const data = await response.json();
    bridgeState.sovereign.lastCommand = {
      command,
      activity,
      localModelFamily,
      model,
      perplexityPrompt,
      timestamp: new Date().toISOString(),
      response: data.choices?.[0]?.message?.content,
    };

    return data.choices?.[0]?.message;
  } catch (error) {
    bridgeState.errors.push({ service: 'grokDelegation', error: error.message });
    throw error;
  }
}

// API Key getters - these would integrate with environment or secure storage
function getGrokApiKey() {
  return typeof window !== 'undefined' ? window.GROK_API_KEY : process?.env?.GROK_API_KEY;
}

function getLinearApiKey() {
  return typeof window !== 'undefined' ? window.LINEAR_API_KEY : process?.env?.LINEAR_API_KEY;
}

function getGeminiApiKey() {
  return typeof window !== 'undefined' ? window.GEMINI_API_KEY : process?.env?.GEMINI_API_KEY;
}

// Initialize
initServiceStatus();

// Export bridge API
export const MeshBridge = {
  refresh: refreshMesh,
  getStatus: getBridgeStatus,
  delegateToGrok,
  delegateToClaude,
  verifyClaudeAdminKey,
  BRIDGE_STATUS,
  MESH_ENDPOINTS,
};

export {
  BRIDGE_STATUS,
  MESH_ENDPOINTS,
  detectLocalModelFamily,
  buildPerplexityReviewPrompt,
  buildCometExtensionReviewPrompt,
  normalizeCometExtensionService,
  normalizePerplexityAdapterService,
  normalizeRecursiveNodeBridgeService,
};

export default MeshBridge;
