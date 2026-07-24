import assert from 'node:assert/strict';
import test from 'node:test';

import {
  getPolymarketDiscordSurface,
  notifyOracleHealth,
  POLYMARKET_DISCORD,
} from '../src/bridge/polymarketDiscord.js';
import { getPerplexityConnectStatus } from '../src/bridge/perplexityConnect.js';

test('polymarket discord surface points at community + bot bridge', () => {
  const surface = getPolymarketDiscordSurface();
  assert.equal(surface.community.invite, 'https://discord.com/invite/polymarket');
  assert.equal(POLYMARKET_DISCORD.botBridgeCli, 'tools/discord_bot_bridge.py');
  assert.equal(surface.bot.executionMode, 'manifest_only');
  assert.equal(surface.contentNeutral, true);
});

test('notifyOracleHealth stays dry-run without discord live gates', () => {
  const result = notifyOracleHealth({
    ok: true,
    degraded: false,
    marketId: '540817',
    entropyBits: 0.97,
  });
  assert.equal(result.dryRun, true);
  assert.equal(result.skipped, true);
  assert.match(result.dryRunPreview, /Polymarket entropy oracle/);
  assert.equal(result.polymarketCommunity, 'https://discord.com/invite/polymarket');
});

test('perplexity connect status never exposes secrets', () => {
  const status = getPerplexityConnectStatus();
  assert.equal(status.schema, 'shadow_garden.perplexity_connect_status.v1');
  assert.equal(status.controls.secretLogging, false);
  assert.ok(status.connectCli.includes('perplexity_connect.py'));
  assert.equal('apiKey' in status, false);
  assert.equal('PERPLEXITY_API_KEY' in (status.envPresent || {}), true);
});
