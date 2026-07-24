/**
 * Polymarket read-only client (Gamma discovery + optional CLOB price enrich).
 * Live network gated by ENABLE_POLYMARKET=1 (or options.enableLive).
 */

import { DefensiveHttp } from './http.ts';
import { SlidingWindowLimiter } from './rateLimit.ts';
import { structureMarket, pickBestMarket, applyClobMidsToOutcomes } from './parse.ts';
import { emptySample, sampleFromMarket } from './entropy.ts';
import type {
  ClientStatus,
  EntropySample,
  ListMarketsQuery,
  ListMarketsResult,
  PolymarketClientOptions,
  StructuredMarket,
} from './types.ts';
import { PolymarketError } from './types.ts';
import { POLYMARKET_RESEARCH } from './research.ts';

const DEFAULT_GAMMA = 'https://gamma-api.polymarket.com';
const DEFAULT_CLOB = 'https://clob.polymarket.com';

function envFlag(name: string): boolean {
  const v = process.env[name];
  return v === '1' || v === 'true';
}

function buildQuery(params: Record<string, string | number | boolean | undefined>): string {
  const sp = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v === undefined || v === null || v === '') continue;
    sp.set(k, String(v));
  }
  const q = sp.toString();
  return q ? `?${q}` : '';
}

export class PolymarketClient {
  private readonly gammaBaseUrl: string;
  private readonly clobBaseUrl: string;
  private readonly timeoutMs: number;
  private readonly maxRetries: number;
  private readonly staleAfterMs: number;
  private readonly minLiquidity: number;
  private readonly failureMode: 'soft' | 'hard';
  private readonly enableLive: boolean;
  private readonly now: () => number;
  private readonly httpGamma: DefensiveHttp;
  private readonly httpClob: DefensiveHttp;

  constructor(opts: PolymarketClientOptions = {}) {
    this.gammaBaseUrl = (opts.gammaBaseUrl || DEFAULT_GAMMA).replace(/\/$/, '');
    this.clobBaseUrl = (opts.clobBaseUrl || DEFAULT_CLOB).replace(/\/$/, '');
    this.timeoutMs = opts.timeoutMs ?? 8000;
    this.maxRetries = opts.maxRetries ?? 2;
    this.staleAfterMs = opts.staleAfterMs ?? 1_800_000;
    this.minLiquidity = opts.minLiquidity ?? 500;
    this.failureMode = opts.failureMode ?? 'soft';
    this.enableLive =
      opts.enableLive ??
      (envFlag('ENABLE_POLYMARKET') || envFlag('POLYMARKET_LIVE_OK'));
    this.now = opts.now ?? (() => Date.now());

    const fetchImpl = opts.fetchImpl;
    this.httpGamma = new DefensiveHttp({
      fetchImpl,
      timeoutMs: this.timeoutMs,
      maxRetries: this.maxRetries,
      now: this.now,
      // Stay under Gamma /markets 300 req / 10s
      limiter: new SlidingWindowLimiter({
        capacity: 60,
        windowMs: 10_000,
        now: this.now,
      }),
    });
    this.httpClob = new DefensiveHttp({
      fetchImpl,
      timeoutMs: this.timeoutMs,
      maxRetries: this.maxRetries,
      now: this.now,
      // Stay under CLOB /price 1500 req / 10s
      limiter: new SlidingWindowLimiter({
        capacity: 120,
        windowMs: 10_000,
        now: this.now,
      }),
    });
  }

  status(): ClientStatus {
    return {
      schema: 'shadow_garden.polymarket_client_status.v1',
      enableLive: this.enableLive,
      gammaBaseUrl: this.gammaBaseUrl,
      clobBaseUrl: this.clobBaseUrl,
      timeoutMs: this.timeoutMs,
      maxRetries: this.maxRetries,
      staleAfterMs: this.staleAfterMs,
      minLiquidity: this.minLiquidity,
      failureMode: this.failureMode,
      rateLimits: {
        gammaMarketsPer10s: POLYMARKET_RESEARCH.rateLimits.gamma.marketsPer10s,
        clobPricePer10s: POLYMARKET_RESEARCH.rateLimits.clob.pricePer10s,
      },
      discord: {
        communityInvite: POLYMARKET_RESEARCH.discord.communityInvite,
        notifyBridge: 'tools/discord_bot_bridge.py',
        liveRequires: ['ENABLE_DISCORD=1', 'DISCORD_LIVE_OK=1'],
      },
      perplexity: {
        autoConnectCli: 'python3 tools/perplexity_connect.py health',
        centralControlCli: 'python3 tools/perplexity_asuna_central_control.py write',
      },
    };
  }

  private assertLive(): void {
    if (!this.enableLive) {
      throw new PolymarketError(
        'live_disabled',
        'Polymarket live fetch disabled. Set ENABLE_POLYMARKET=1 to allow network.',
        { retryable: false },
      );
    }
  }

  async listMarkets(query: ListMarketsQuery = {}): Promise<ListMarketsResult> {
    this.assertLive();
    const limit = Math.min(100, Math.max(1, query.limit ?? 20));
    const qs = buildQuery({
      closed: query.closed === undefined ? false : query.closed,
      limit,
      after_cursor: query.afterCursor,
      tag_id: query.tagId,
      order: query.order,
      ascending: query.ascending,
      slug: query.slug,
    });
    // Prefer keyset pagination — offset pagination is rejected with 422.
    const url = `${this.gammaBaseUrl}/markets/keyset${qs}`;
    const res = await this.httpGamma.get(url);
    const body = (res.json && typeof res.json === 'object' ? res.json : {}) as {
      markets?: unknown[];
      next_cursor?: string | null;
      data?: unknown[];
    };
    const rawList = Array.isArray(body.markets)
      ? body.markets
      : Array.isArray(body.data)
        ? body.data
        : Array.isArray(res.json)
          ? res.json
          : [];

    const markets: StructuredMarket[] = [];
    for (const row of rawList) {
      if (!row || typeof row !== 'object') continue;
      markets.push(
        structureMarket(row as Record<string, unknown>, {
          now: this.now(),
          staleAfterMs: this.staleAfterMs,
          minLiquidity: this.minLiquidity,
          source: 'gamma',
        }),
      );
    }

    return {
      markets,
      nextCursor: body.next_cursor ?? null,
      rawCount: rawList.length,
    };
  }

  async getMarketById(id: string): Promise<StructuredMarket> {
    this.assertLive();
    const url = `${this.gammaBaseUrl}/markets/${encodeURIComponent(id)}`;
    const res = await this.httpGamma.get(url);
    const raw = res.json;
    if (!raw || typeof raw !== 'object') {
      throw new PolymarketError('invalid_market', `No market payload for id=${id}`, {
        status: res.status,
      });
    }
    return structureMarket(raw as Record<string, unknown>, {
      now: this.now(),
      staleAfterMs: this.staleAfterMs,
      minLiquidity: this.minLiquidity,
      source: 'gamma',
    });
  }

  async getMarketBySlug(slug: string): Promise<StructuredMarket> {
    this.assertLive();
    const url = `${this.gammaBaseUrl}/markets/slug/${encodeURIComponent(slug)}`;
    const res = await this.httpGamma.get(url);
    const raw = res.json;
    if (!raw || typeof raw !== 'object') {
      throw new PolymarketError(
        'invalid_market',
        `No market payload for slug=${slug}`,
        { status: res.status },
      );
    }
    return structureMarket(raw as Record<string, unknown>, {
      now: this.now(),
      staleAfterMs: this.staleAfterMs,
      minLiquidity: this.minLiquidity,
      source: 'gamma',
    });
  }

  async getMidpoint(tokenId: string): Promise<number | null> {
    this.assertLive();
    const url = `${this.clobBaseUrl}/midpoint?token_id=${encodeURIComponent(tokenId)}`;
    try {
      const res = await this.httpClob.get(url);
      const mid =
        res.json && typeof res.json === 'object'
          ? Number((res.json as { mid?: string }).mid)
          : NaN;
      return Number.isFinite(mid) ? mid : null;
    } catch (err) {
      if (err instanceof PolymarketError && err.status === 404) return null;
      throw err;
    }
  }

  async getBuyPrice(tokenId: string): Promise<number | null> {
    this.assertLive();
    const url = `${this.clobBaseUrl}/price?token_id=${encodeURIComponent(tokenId)}&side=buy`;
    try {
      const res = await this.httpClob.get(url);
      const price =
        res.json && typeof res.json === 'object'
          ? Number((res.json as { price?: string }).price)
          : NaN;
      return Number.isFinite(price) ? price : null;
    } catch (err) {
      if (err instanceof PolymarketError && err.status === 404) return null;
      throw err;
    }
  }

  /** Enrich Gamma outcomes with CLOB mid/buy when token ids exist. */
  async enrichWithClob(market: StructuredMarket): Promise<StructuredMarket> {
    const outcomes = [];
    for (const o of market.outcomes) {
      if (!o.tokenId) {
        outcomes.push(o);
        continue;
      }
      let midpoint: number | null = null;
      let buyPrice: number | null = null;
      try {
        midpoint = await this.getMidpoint(o.tokenId);
        buyPrice = await this.getBuyPrice(o.tokenId);
      } catch {
        // Soft: keep Gamma probabilities if CLOB enrich fails.
      }
      outcomes.push({ ...o, midpoint, buyPrice });
    }
    return applyClobMidsToOutcomes(
      { ...market, outcomes, source: 'gamma+clob' },
      {
        now: this.now(),
        staleAfterMs: this.staleAfterMs,
        minLiquidity: this.minLiquidity,
      },
    );
  }

  /**
   * Pull one market and return an entropy sample for the simulation.
   * Fails soft by default (degraded sample) when live is off or quality fails.
   * Default path auto-enriches with CLOB mids to fix Gamma lag / sum traps.
   */
  async entropyOracle(opts: {
    marketId?: string;
    slug?: string;
    enrichClob?: boolean;
  } = {}): Promise<EntropySample> {
    try {
      if (!this.enableLive) {
        return emptySample('live_disabled', this.failureMode);
      }
      let market: StructuredMarket;
      if (opts.marketId) {
        market = await this.getMarketById(opts.marketId);
      } else if (opts.slug) {
        market = await this.getMarketBySlug(opts.slug);
      } else {
        const page = await this.listMarkets({
          closed: false,
          limit: 20,
        });
        const trusted = pickBestMarket(page.markets);
        if (!trusted) {
          return emptySample('no_markets', this.failureMode);
        }
        market = trusted;
      }
      const shouldEnrich =
        opts.enrichClob !== false &&
        (opts.enrichClob === true ||
          !market.quality.ok ||
          market.quality.stale ||
          !market.quality.pricesSumNearOne);
      if (shouldEnrich) {
        market = await this.enrichWithClob(market);
      }
      return sampleFromMarket(market, { failureMode: this.failureMode });
    } catch (err) {
      const msg =
        err instanceof PolymarketError
          ? `${err.code}:${err.message}`
          : String(err);
      if (this.failureMode === 'hard') throw err;
      return emptySample(msg, this.failureMode);
    }
  }
}

export function createPolymarketClient(
  opts: PolymarketClientOptions = {},
): PolymarketClient {
  return new PolymarketClient(opts);
}
