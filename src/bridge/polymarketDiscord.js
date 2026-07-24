/**
 * Discord + Polymarket community/oracle notify helpers.
 * Live posts still require ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1.
 */

import {
  getDiscordBridgeStatus,
  notifyDiscordStatus,
  liveDiscordAllowed,
} from './discordNotify.js';

export const POLYMARKET_DISCORD = Object.freeze({
  communityInvite: 'https://discord.com/invite/polymarket',
  communityLabel: 'Polymarket Discord',
  botBridgeCli: 'tools/discord_bot_bridge.py',
  oracleCli: 'tools/polymarket_oracle.mjs',
  unifyCli: 'tools/polymarket_asuna_point0_unify.py',
});

export function getPolymarketDiscordSurface() {
  const discord = getDiscordBridgeStatus();
  return {
    schema: 'shadow_garden.polymarket_discord_surface.v1',
    community: {
      invite: POLYMARKET_DISCORD.communityInvite,
      label: POLYMARKET_DISCORD.communityLabel,
      public: true,
    },
    bot: {
      bridgeCli: POLYMARKET_DISCORD.botBridgeCli,
      liveDiscord: discord.liveDiscord,
      executionMode: discord.executionMode,
      gates: discord.gates,
    },
    oracle: {
      cli: POLYMARKET_DISCORD.oracleCli,
      unifyCli: POLYMARKET_DISCORD.unifyCli,
      enableEnv: 'ENABLE_POLYMARKET',
    },
    mutationPolicy: 'status_notify_only_dual_gated',
    contentNeutral: true,
  };
}

/**
 * Dry-run (or live-gated) status line about an entropy sample.
 */
export function notifyOracleHealth(sample, { force = false } = {}) {
  const bits =
    sample && typeof sample.entropyBits === 'number'
      ? sample.entropyBits.toFixed(3)
      : '?';
  const mid = sample?.marketId || 'none';
  const ok = sample?.ok ? 'ok' : sample?.degraded ? 'degraded' : 'fail';
  const text = `Polymarket entropy oracle · ${ok} · market=${mid} · H=${bits} bits · community ${POLYMARKET_DISCORD.communityInvite}`;
  return {
    ...notifyDiscordStatus(text, { force }),
    polymarketCommunity: POLYMARKET_DISCORD.communityInvite,
    liveDiscordAllowed: liveDiscordAllowed(),
  };
}

export default {
  POLYMARKET_DISCORD,
  getPolymarketDiscordSurface,
  notifyOracleHealth,
};
