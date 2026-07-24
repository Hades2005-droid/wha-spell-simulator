/**
 * Discord status_notify bridge (manifest-only by default).
 *
 * Live sends require ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1 in environment.
 * Never reads or returns secret values — env names / booleans only.
 */

const ENV_NAMES = [
  'ENABLE_DISCORD',
  'DISCORD_LIVE_OK',
  'DISCORD_APPLICATION_ID',
  'DISCORD_WEBHOOK_URL',
  'DISCORD_BOT_TOKEN',
  'DISCORD_TOKEN',
  'DISCORD_CHANNEL_ID',
  'DISCORD_GUILD_ID',
];

const BRIDGE_CLI = 'tools/discord_bot_bridge.py';
const PAIRED_BRIDGE = 'shadow_garden_handoff/bridges/discord_asuna_point0_unification.json';
const PHASE3_BRIDGE = 'shadow_garden_handoff/bridges/phase3_persephone_shutdown_bridge.json';

function envPresence() {
  const out = {};
  for (const name of ENV_NAMES) {
    out[name] = Boolean(process.env[name]);
  }
  return out;
}

export function liveDiscordAllowed() {
  return process.env.ENABLE_DISCORD === '1' && process.env.DISCORD_LIVE_OK === '1';
}

/**
 * Manifest-only Discord bridge status for sovereign spells / mesh diagnostics.
 */
export function getDiscordBridgeStatus() {
  return {
    schema: 'shadow_garden.wha_discord_notify.v1',
    role: 'status_notify_lane',
    executionMode: liveDiscordAllowed() ? 'live' : 'manifest_only',
    liveDiscord: liveDiscordAllowed(),
    discordApplicationIdEnv: 'DISCORD_APPLICATION_ID',
    bridgeCli: BRIDGE_CLI,
    pairedBridge: PAIRED_BRIDGE,
    phase3Bridge: PHASE3_BRIDGE,
    envPresent: envPresence(),
    gates: {
      enableDiscord: process.env.ENABLE_DISCORD === '1',
      discordLiveOk: process.env.DISCORD_LIVE_OK === '1',
      liveSendAllowed: liveDiscordAllowed(),
    },
    mutationPolicy: 'webhook_or_bot_status_messages_only',
    contentNeutral: true,
  };
}

/**
 * Status notify — dry-run unless live gates pass. No network from JS; callers
 * should spawn tools/discord_bot_bridge.py for live delivery.
 */
export function notifyDiscordStatus(text, { force = false } = {}) {
  const allowed = liveDiscordAllowed() || force;
  const preview = String(text || '').slice(0, 200);
  if (!allowed) {
    return {
      ok: true,
      dryRun: true,
      skipped: true,
      blocked: 'requires ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1',
      textLen: String(text || '').length,
      dryRunPreview: preview,
      bridgeCli: BRIDGE_CLI,
    };
  }
  return {
    ok: false,
    dryRun: false,
    skipped: true,
    hint: `Run: python3 ${BRIDGE_CLI} notify --text "..."`,
    textLen: String(text || '').length,
  };
}

export default {
  liveDiscordAllowed,
  getDiscordBridgeStatus,
  notifyDiscordStatus,
};
