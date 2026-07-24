/**
 * Parse Gamma market payloads into structured probabilities + quality flags.
 */

import type {
  MarketQuality,
  OutcomeProbability,
  StructuredMarket,
} from './types.ts';

function asString(v: unknown): string | null {
  if (typeof v === 'string' && v.length) return v;
  if (typeof v === 'number' && Number.isFinite(v)) return String(v);
  return null;
}

function asNumber(v: unknown): number | null {
  if (typeof v === 'number' && Number.isFinite(v)) return v;
  if (typeof v === 'string' && v.trim()) {
    const n = Number(v);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function asBool(v: unknown): boolean {
  return v === true || v === 'true' || v === 1 || v === '1';
}

/** Gamma often serializes nested arrays as JSON strings. */
export function parseMaybeJsonArray(raw: unknown): unknown[] {
  if (Array.isArray(raw)) return raw;
  if (typeof raw === 'string') {
    const t = raw.trim();
    if (!t) return [];
    try {
      const parsed = JSON.parse(t);
      return Array.isArray(parsed) ? parsed : [];
    } catch {
      return [];
    }
  }
  return [];
}

export function shannonEntropyBits(probs: number[]): number {
  let h = 0;
  for (const p of probs) {
    if (p > 0) h -= p * Math.log2(p);
  }
  return h;
}

/**
 * Soft-fix sum≠1 traps: renormalize when sum is in a recoverable band.
 * Outside the band, leave as-is and let quality mark incomplete / sum_off.
 */
export function normalizeProbabilities(
  probs: number[],
  opts: { minSum?: number; maxSum?: number } = {},
): { probs: number[]; renormalized: boolean; priceSum: number } {
  const minSum = opts.minSum ?? 0.85;
  const maxSum = opts.maxSum ?? 1.15;
  const finite = probs.map((p) => (Number.isFinite(p) ? Math.min(1, Math.max(0, p)) : NaN));
  const priceSum = finite.reduce((a, b) => a + (Number.isFinite(b) ? b : 0), 0);
  if (
    finite.every((p) => Number.isFinite(p)) &&
    priceSum >= minSum &&
    priceSum <= maxSum &&
    Math.abs(priceSum - 1) > 1e-9
  ) {
    return {
      probs: finite.map((p) => p / priceSum),
      renormalized: true,
      priceSum,
    };
  }
  return { probs: finite, renormalized: false, priceSum };
}

export function assessQuality(
  outcomes: OutcomeProbability[],
  meta: {
    closed: boolean;
    liquidity: number | null;
    updatedAt: string | null;
    now: number;
    staleAfterMs: number;
    minLiquidity: number;
    renormalized?: boolean;
    usedClobPrices?: boolean;
  },
): MarketQuality {
  const warnings: string[] = [];
  const probs = outcomes.map((o) => o.probability);
  const priceSum = probs.reduce((a, b) => a + (Number.isFinite(b) ? b : 0), 0);
  const pricesSumNearOne = Math.abs(priceSum - 1) <= 0.05;
  if (!pricesSumNearOne) warnings.push('outcome_prices_sum_off');
  if (meta.renormalized) warnings.push('renormalized_probabilities');
  if (meta.usedClobPrices) warnings.push('used_clob_midpoints');

  const incompleteOutcomes =
    outcomes.length < 2 || outcomes.some((o) => !Number.isFinite(o.probability));
  if (incompleteOutcomes) warnings.push('incomplete_outcomes');

  let stale = false;
  if (meta.updatedAt) {
    const ts = Date.parse(meta.updatedAt);
    if (Number.isFinite(ts) && meta.now - ts > meta.staleAfterMs) {
      stale = true;
      // Advisory: Gamma updatedAt often lags live books.
      warnings.push('metadata_stale_updatedAt');
    }
  } else {
    warnings.push('missing_updatedAt');
  }

  const lowLiquidity =
    meta.liquidity == null || meta.liquidity < meta.minLiquidity;
  if (lowLiquidity) warnings.push('low_liquidity');

  if (meta.closed) warnings.push('market_closed');

  // ok fails only on hard traps — metadata staleness alone does not degrade ok.
  const ok =
    !incompleteOutcomes &&
    pricesSumNearOne &&
    !meta.closed &&
    !lowLiquidity;

  return {
    ok,
    stale,
    lowLiquidity,
    closed: meta.closed,
    incompleteOutcomes,
    pricesSumNearOne,
    priceSum,
    renormalized: Boolean(meta.renormalized),
    usedClobPrices: Boolean(meta.usedClobPrices),
    warnings,
  };
}

export function structureMarket(
  raw: Record<string, unknown>,
  opts: {
    now: number;
    staleAfterMs: number;
    minLiquidity: number;
    source?: StructuredMarket['source'];
    usedClobPrices?: boolean;
  },
): StructuredMarket {
  const labels = parseMaybeJsonArray(raw.outcomes).map((x) => String(x));
  const rawPrices = parseMaybeJsonArray(raw.outcomePrices).map((x) => Number(x));
  const tokens = parseMaybeJsonArray(raw.clobTokenIds).map((x) => String(x));
  const { probs, renormalized, priceSum: _sum } = normalizeProbabilities(rawPrices);

  const outcomes: OutcomeProbability[] = [];
  const n = Math.max(labels.length, probs.length, tokens.length, 0);
  for (let i = 0; i < n; i += 1) {
    const p = Number(probs[i]);
    outcomes.push({
      label: labels[i] ?? `outcome_${i}`,
      tokenId: tokens[i] ?? null,
      probability: Number.isFinite(p) ? Math.min(1, Math.max(0, p)) : NaN,
      midpoint: null,
      buyPrice: null,
    });
  }

  const closed = asBool(raw.closed);
  const liquidity =
    asNumber(raw.liquidityNum) ?? asNumber(raw.liquidity) ?? null;
  const volume = asNumber(raw.volumeNum) ?? asNumber(raw.volume) ?? null;
  const updatedAt = asString(raw.updatedAt);
  const quality = assessQuality(outcomes, {
    closed,
    liquidity,
    updatedAt,
    now: opts.now,
    staleAfterMs: opts.staleAfterMs,
    minLiquidity: opts.minLiquidity,
    renormalized,
    usedClobPrices: opts.usedClobPrices,
  });

  const validProbs = outcomes
    .map((o) => o.probability)
    .filter((p) => Number.isFinite(p) && p >= 0);

  return {
    id: asString(raw.id) ?? '',
    slug: asString(raw.slug),
    question: asString(raw.question) ?? '',
    conditionId: asString(raw.conditionId),
    closed,
    active: asBool(raw.active),
    acceptingOrders: asBool(raw.acceptingOrders),
    endDate: asString(raw.endDate),
    updatedAt,
    liquidity,
    volume,
    outcomes,
    entropyBits: shannonEntropyBits(validProbs),
    quality,
    fetchedAt: new Date(opts.now).toISOString(),
    source: opts.source ?? 'gamma',
  };
}

/** Prefer liquid, open, accepting-order markets with quality.ok. */
export function pickBestMarket(markets: StructuredMarket[]): StructuredMarket | null {
  if (!markets.length) return null;
  const ranked = [...markets].sort((a, b) => {
    const score = (m: StructuredMarket) =>
      (m.quality.ok ? 8 : 0) +
      (m.acceptingOrders ? 4 : 0) +
      (m.active && !m.closed ? 2 : 0) +
      Math.min(2, Math.log10(1 + (m.liquidity ?? 0)) / 2);
    return score(b) - score(a);
  });
  return ranked[0] ?? null;
}

/**
 * Rebuild outcome probabilities from CLOB midpoints when available.
 * Falls back to existing Gamma probs when mids are incomplete.
 */
export function applyClobMidsToOutcomes(
  market: StructuredMarket,
  opts: {
    now: number;
    staleAfterMs: number;
    minLiquidity: number;
  },
): StructuredMarket {
  const mids = market.outcomes.map((o) => o.midpoint);
  const allMids =
    mids.length >= 2 && mids.every((m) => m != null && Number.isFinite(m));
  if (!allMids) {
    return {
      ...market,
      source: 'gamma+clob',
      quality: {
        ...market.quality,
        usedClobPrices: false,
        warnings: [...new Set([...market.quality.warnings, 'clob_mids_incomplete'])],
      },
    };
  }

  const { probs, renormalized } = normalizeProbabilities(
    mids.map((m) => Number(m)),
  );
  const outcomes = market.outcomes.map((o, i) => ({
    ...o,
    probability: probs[i]!,
  }));
  const quality = assessQuality(outcomes, {
    closed: market.closed,
    liquidity: market.liquidity,
    updatedAt: market.updatedAt,
    now: opts.now,
    staleAfterMs: opts.staleAfterMs,
    minLiquidity: opts.minLiquidity,
    renormalized: renormalized || market.quality.renormalized,
    usedClobPrices: true,
  });
  return {
    ...market,
    outcomes,
    entropyBits: shannonEntropyBits(probs),
    quality,
    source: 'gamma+clob',
    fetchedAt: new Date(opts.now).toISOString(),
  };
}
