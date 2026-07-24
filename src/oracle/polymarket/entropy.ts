/**
 * Entropy oracle: turn structured market probabilities into sim seed material.
 * Not a CSPRNG — deterministic, content-neutral, fail-soft by default.
 */

import { createHash } from 'node:crypto';

import type {
  EntropySample,
  OutcomeProbability,
  PolymarketClientOptions,
  StructuredMarket,
} from './types.ts';
import { shannonEntropyBits } from './parse.ts';

function clamp01(n: number): number {
  if (!Number.isFinite(n)) return 0;
  return Math.min(1, Math.max(0, n));
}

/** Fold probabilities into a stable 32-bit word. */
export function entropyWordFromProbs(
  marketId: string,
  probs: number[],
): number {
  let h = 2166136261;
  const s = `${marketId}|${probs.map((p) => clamp01(p).toFixed(6)).join(',')}`;
  for (let i = 0; i < s.length; i += 1) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function seedHexFromSample(parts: {
  marketId: string;
  probs: number[];
  entropyBits: number;
  fetchedAt: string;
}): string {
  const payload = JSON.stringify({
    v: 1,
    marketId: parts.marketId,
    probs: parts.probs.map((p) => clamp01(p)),
    entropyBits: Number(parts.entropyBits.toFixed(8)),
    fetchedAt: parts.fetchedAt,
  });
  return createHash('sha256').update(payload).digest('hex');
}

export function sampleFromMarket(
  market: StructuredMarket,
  opts: Pick<PolymarketClientOptions, 'failureMode'> = {},
): EntropySample {
  const failureMode = opts.failureMode ?? 'soft';
  const probs = market.outcomes.map((o) => clamp01(o.probability));
  const entropyBits = shannonEntropyBits(probs.filter((p) => p > 0));
  const ok = market.quality.ok && probs.length >= 2;
  const degraded = !ok;

  if (!ok && failureMode === 'hard') {
    return {
      schema: 'shadow_garden.polymarket_entropy_sample.v1',
      ok: false,
      degraded: true,
      marketId: market.id,
      question: market.question,
      probabilities: [],
      outcomes: [],
      entropyBits: 0,
      entropyWord: 0,
      seedHex: '',
      quality: market.quality,
      fetchedAt: market.fetchedAt,
      error: `quality_rejected:${market.quality.warnings.join(',') || 'unknown'}`,
      failureMode,
    };
  }

  return {
    schema: 'shadow_garden.polymarket_entropy_sample.v1',
    ok,
    degraded,
    marketId: market.id,
    question: market.question,
    probabilities: probs,
    outcomes: market.outcomes as OutcomeProbability[],
    entropyBits,
    entropyWord: entropyWordFromProbs(market.id, probs),
    seedHex: seedHexFromSample({
      marketId: market.id,
      probs,
      entropyBits,
      fetchedAt: market.fetchedAt,
    }),
    quality: market.quality,
    fetchedAt: market.fetchedAt,
    error: degraded
      ? `degraded:${market.quality.warnings.join(',') || 'quality'}`
      : null,
    failureMode,
  };
}

export function emptySample(
  error: string,
  failureMode: 'soft' | 'hard' = 'soft',
): EntropySample {
  return {
    schema: 'shadow_garden.polymarket_entropy_sample.v1',
    ok: false,
    degraded: true,
    marketId: null,
    question: null,
    probabilities: [],
    outcomes: [],
    entropyBits: 0,
    entropyWord: 0,
    seedHex: '',
    quality: {
      ok: false,
      stale: true,
      lowLiquidity: true,
      closed: false,
      incompleteOutcomes: true,
      pricesSumNearOne: false,
      priceSum: 0,
      renormalized: false,
      usedClobPrices: false,
      warnings: ['empty_sample'],
    },
    fetchedAt: new Date().toISOString(),
    error,
    failureMode,
  };
}
