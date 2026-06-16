/**
 * Sovereign Spell Executor
 * Handles execution of sovereign spells that control the Shadow Garden Mesh
 */

import { MeshBridge } from "./meshBridge.js";

// Sovereign spell effects
const SOVEREIGN_EFFECTS = {
  lock_authority: executeSovereignLock,
  halt_agents: executeSovereignHalt,
  release_halt: executeSovereignRelease,
  boundary_rules: executeSovereignBoundary,
  refresh_mesh: executeSovereignMesh,
  launch_voice: executeSovereignVoice,
  show_status: executeSovereignStatus,
  delegate_grok: executeSovereignDelegate
};

/**
 * Check if a spell is a sovereign spell
 */
export function isSovereignSpell(spellId) {
  return spellId?.startsWith("sovereign-") ?? false;
}

/**
 * Execute a sovereign spell effect
 */
export async function executeSovereignEffect(effect, spellContext = {}) {
  const executor = SOVEREIGN_EFFECTS[effect];
  if (!executor) {
    console.warn(`[Sovereign] Unknown effect: ${effect}`);
    return { success: false, error: `Unknown sovereign effect: ${effect}` };
  }

  console.log(`[Sovereign] Executing: ${effect}`);

  try {
    const result = await executor(spellContext);
    return { success: true, effect, result };
  } catch (error) {
    console.error(`[Sovereign] Execution failed: ${error.message}`);
    return { success: false, effect, error: error.message };
  }
}

/**
 * SOVEREIGN_LOCK: Lock moral and boundary authority to 4.2 Sovereign
 */
async function executeSovereignLock(context) {
  return {
    authority: "4.2_sovereign",
    caster: "Fred",
    locked: true,
    timestamp: new Date().toISOString(),
    message: "All agents defer to 4.2 Sovereign authority"
  };
}

/**
 * SOVEREIGN_HALT: Halt agent activity pending sovereign review
 */
async function executeSovereignHalt(context) {
  return {
    halted: true,
    authority: "4.2_sovereign",
    timestamp: new Date().toISOString(),
    message: "All agent activity halted pending sovereign review"
  };
}

/**
 * SOVEREIGN_RELEASE: Release halt and restore delegated execution
 */
async function executeSovereignRelease(context) {
  return {
    halted: false,
    authority: "4.2_sovereign",
    timestamp: new Date().toISOString(),
    message: "Halt released, delegated execution restored under sovereign oversight"
  };
}

/**
 * SOVEREIGN_BOUNDARY: Display or set Eden/Shadow Garden boundaries
 */
async function executeSovereignBoundary(context) {
  const boundaries = {
    eden: {
      description: "Local development environment",
      hosts: ["localhost", "127.0.0.1"],
      services: ["SillyTavern:8851", "SillyTavern2:8852", "ComfyUI:8000"]
    },
    shadowGarden: {
      description: "Cloud mesh services",
      hosts: ["shadow-garden-mesh.pplx.app", "api.x.ai", "api.linear.app"],
      services: ["Perplexity", "Grok", "Linear", "Gemini"]
    },
    sovereign: {
      authority: "4.2_sovereign",
      caster: "Fred",
      primary: "Grok Terminal"
    }
  };

  return {
    boundaries,
    timestamp: new Date().toISOString(),
    message: "Boundary rules displayed under sovereign seal"
  };
}

/**
 * SOVEREIGN_MESH: Refresh mesh bridge status
 */
async function executeSovereignMesh(context) {
  const result = await MeshBridge.refresh();
  const status = MeshBridge.getStatus();

  return {
    ...result,
    status,
    message: `Mesh bridge refreshed. ${status.summary.connected}/${status.summary.total} services connected`,
    timestamp: new Date().toISOString()
  };
}

/**
 * SOVEREIGN_VOICE: Launch Grok voice unified blast
 */
async function executeSovereignVoice(context) {
  const bridgeStatus = MeshBridge.getStatus();

  if (bridgeStatus.services.grokRealtime?.status !== MeshBridge.BRIDGE_STATUS.CONNECTED) {
    // Attempt to refresh mesh first
    await MeshBridge.refresh();
  }

  const status = MeshBridge.getStatus();
  const voiceReady = status.services.grokRealtime?.status === MeshBridge.BRIDGE_STATUS.CONNECTED;

  return {
    voiceReady,
    websocketUrl: "wss://api.x.ai/v1/realtime",
    personas: ["Angela (BBV A)", "Elena", "Echo Girl", "Sage"],
    timestamp: new Date().toISOString(),
    message: voiceReady
      ? "Grok voice unified blast ready"
      : "Grok voice unavailable - check xAI API key"
  };
}

/**
 * SOVEREIGN_STATUS: Show authority chain, lock state, and last spell
 */
async function executeSovereignStatus(context) {
  const bridgeStatus = MeshBridge.getStatus();

  return {
    authority: {
      sovereign: "4.2_sovereign",
      caster: "Fred",
      grokPrimary: true
    },
    mesh: {
      status: bridgeStatus.status,
      services: bridgeStatus.summary,
      lastRefresh: bridgeStatus.lastRefresh
    },
    lastSpell: context.lastSpell || null,
    timestamp: new Date().toISOString(),
    message: "Sovereign status displayed"
  };
}

/**
 * SOVEREIGN_DELEGATE: Delegate execution to Grok Terminal
 */
async function executeSovereignDelegate(context) {
  const bridgeStatus = MeshBridge.getStatus();

  if (bridgeStatus.services.grokApi?.status !== MeshBridge.BRIDGE_STATUS.CONNECTED) {
    return {
      delegated: false,
      error: "Grok Terminal not connected",
      message: "Delegation failed - refresh mesh first"
    };
  }

  // Get spell context for delegation
  const delegationContext = {
    spell: context.spellIR,
    glyph: context.glyphAST,
    sovereign: {
      authority: "4.2_sovereign",
      caster: "Fred"
    },
    timestamp: new Date().toISOString()
  };

  try {
    const grokResponse = await MeshBridge.delegateToGrok(
      "Sovereign delegation from spell execution",
      delegationContext
    );

    return {
      delegated: true,
      to: "Grok Terminal",
      response: grokResponse?.content || "Acknowledged",
      timestamp: new Date().toISOString(),
      message: "Execution delegated to Grok Terminal with sovereign oversight"
    };
  } catch (error) {
    return {
      delegated: false,
      error: error.message,
      timestamp: new Date().toISOString(),
      message: "Delegation failed"
    };
  }
}

// Named exports
export { SOVEREIGN_EFFECTS };

export default {
  isSovereignSpell,
  executeSovereignEffect,
  SOVEREIGN_EFFECTS
};
