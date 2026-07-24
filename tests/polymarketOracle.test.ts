/**
 * Polymarket entropy oracle tests — mocked network, fail-soft defaults.
 */

import assert from 'node:assert/strict';
import test from 'node:test';

import {
  createPolymarketClient,
  structureMarket,
  shannonEntropyBits,
  sampleFromMarket,
  emptySample,
  POLYMARKET_RESEARCH,
} from '../src/oracle/polymarket/index.ts';

const FIXTURE_MARKET = {
  id: '540817',
  question: 'Fixture market?',
  conditionId: '0xabc',
  slug: 'fixture-market',
  closed: false,
  active: true,
  acceptingOrders: true,
  endDate: '2026-12-31T00:00:00Z',
  updatedAt: new Date().toISOString(),
  liquidityNum: 5000,
  volumeNum: 10000,
  outcomes: '["Yes","No"]',
  outcomePrices: '["0.6","0.4"]',
  clobTokenIds: '["tok_yes","tok_no"]',
};

test('parses JSON-string outcomePrices and computes entropy', () => {
  const m = structureMarket(FIXTURE_MARKET, {
    now: Date.now(),
    staleAfterMs: 120_000,
    minLiquidity: 500,
  });
  assert.equal(m.outcomes.length, 2);
  assert.equal(m.outcomes[0]!.probability, 0.6);
  assert.equal(m.outcomes[1]!.probability, 0.4);
  assert.ok(m.quality.ok);
  assert.ok(m.entropyBits > 0.9 && m.entropyBits < 1.0);
  assert.equal(Number(shannonEntropyBits([0.5, 0.5]).toFixed(6)), 1);
});

test('status is live-disabled by default and documents Discord + Perplexity', () => {
  const status = createPolymarketClient({ enableLive: false }).status();
  assert.equal(status.enableLive, false);
  assert.equal(status.discord.communityInvite, 'https://discord.com/invite/polymarket');
  assert.match(status.perplexity.autoConnectCli, /perplexity_connect/);
  assert.equal(POLYMARKET_RESEARCH.rateLimits.gamma.marketsPer10s, 300);
});

test('entropyOracle soft-fails when live disabled', async () => {
  const sample = await createPolymarketClient({ enableLive: false }).entropyOracle();
  assert.equal(sample.ok, false);
  assert.equal(sample.degraded, true);
  assert.equal(sample.error, 'live_disabled');
  assert.equal(sample.schema, 'shadow_garden.polymarket_entropy_sample.v1');
});

test('entropyOracle returns structured sample from mocked Gamma', async () => {
  const fetchImpl = async (url: string) => {
    assert.match(String(url), /gamma-api|markets/);
    return new Response(JSON.stringify(FIXTURE_MARKET), {
      status: 200,
      headers: { 'content-type': 'application/json' },
    });
  };
  const client = createPolymarketClient({
    enableLive: true,
    fetchImpl: fetchImpl as typeof fetch,
    now: () => Date.parse(FIXTURE_MARKET.updatedAt),
  });
  const sample = await client.entropyOracle({ marketId: '540817' });
  assert.equal(sample.ok, true);
  assert.equal(sample.degraded, false);
  assert.equal(sample.marketId, '540817');
  assert.deepEqual(sample.probabilities, [0.6, 0.4]);
  assert.equal(sample.seedHex.length, 64);
  assert.ok(sample.entropyWord > 0);
});

test('sampleFromMarket hard mode rejects bad quality', () => {
  const bad = structureMarket(
    {
      ...FIXTURE_MARKET,
      closed: true,
      liquidityNum: 1,
      outcomePrices: '["0.9","0.9"]',
    },
    { now: Date.now(), staleAfterMs: 1000, minLiquidity: 500 },
  );
  const hard = sampleFromMarket(bad, { failureMode: 'hard' });
  assert.equal(hard.ok, false);
  assert.match(String(hard.error), /quality_rejected/);
  const soft = sampleFromMarket(bad, { failureMode: 'soft' });
  assert.equal(soft.degraded, true);
  assert.ok(soft.probabilities.length >= 1);
});

test('renormalizes recoverable sum≠1 and keeps quality ok', () => {
  const m = structureMarket(
    {
      ...FIXTURE_MARKET,
      outcomePrices: '["0.55","0.50"]', // sum 1.05
    },
    { now: Date.now(), staleAfterMs: 1_800_000, minLiquidity: 500 },
  );
  assert.equal(m.quality.renormalized, true);
  assert.ok(Math.abs(m.outcomes[0]!.probability + m.outcomes[1]!.probability - 1) < 1e-9);
  assert.equal(m.quality.ok, true);
  assert.ok(m.quality.warnings.includes('renormalized_probabilities'));
});

test('metadata staleness is advisory and does not alone fail ok', () => {
  const old = new Date(Date.now() - 3_600_000).toISOString();
  const m = structureMarket(
    { ...FIXTURE_MARKET, updatedAt: old },
    { now: Date.now(), staleAfterMs: 120_000, minLiquidity: 500 },
  );
  assert.equal(m.quality.stale, true);
  assert.equal(m.quality.ok, true);
  assert.ok(m.quality.warnings.includes('metadata_stale_updatedAt'));
});

test('pickBestMarket prefers liquid accepting markets', async () => {
  const { pickBestMarket } = await import('../src/oracle/polymarket/index.ts');
  const low = structureMarket(
    { ...FIXTURE_MARKET, id: '1', liquidityNum: 10, acceptingOrders: false },
    { now: Date.now(), staleAfterMs: 1_800_000, minLiquidity: 500 },
  );
  const high = structureMarket(
    { ...FIXTURE_MARKET, id: '2', liquidityNum: 9000, acceptingOrders: true },
    { now: Date.now(), staleAfterMs: 1_800_000, minLiquidity: 500 },
  );
  const best = pickBestMarket([low, high]);
  assert.equal(best?.id, '2');
});

test('retries then soft-fails on persistent network errors', async () => {
  let calls = 0;
  const fetchImpl = async () => {
    calls += 1;
    throw new Error('socket hang up');
  };
  const sample = await createPolymarketClient({
    enableLive: true,
    maxRetries: 1,
    fetchImpl: fetchImpl as typeof fetch,
    failureMode: 'soft',
  }).entropyOracle({ marketId: '1' });
  assert.ok(calls >= 2);
  assert.equal(sample.ok, false);
  assert.equal(sample.degraded, true);
  assert.match(String(sample.error), /network_error|exhausted|socket/);
});

test('listMarkets prefers keyset and structures page', async () => {
  const fetchImpl = async (url: string) => {
    assert.match(String(url), /\/markets\/keyset/);
    assert.doesNotMatch(String(url), /offset=/);
    return new Response(
      JSON.stringify({ markets: [FIXTURE_MARKET], next_cursor: 'abc' }),
      { status: 200, headers: { 'content-type': 'application/json' } },
    );
  };
  const page = await createPolymarketClient({
    enableLive: true,
    fetchImpl: fetchImpl as typeof fetch,
  }).listMarkets({ closed: false, limit: 5 });
  assert.equal(page.markets.length, 1);
  assert.equal(page.nextCursor, 'abc');
});
