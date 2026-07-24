/**
 * Polymarket entropy-oracle types (read-only market data).
 * Secrets never appear here — public Gamma/CLOB surfaces only.
 */

export type JsonPrimitive = string | number | boolean | null;
export type JsonValue = JsonPrimitive | JsonValue[] | { [key: string]: JsonValue };

export interface PolymarketClientOptions {
  /** Gamma discovery base. Default: https://gamma-api.polymarket.com */
  gammaBaseUrl?: string;
  /** CLOB market-data base. Default: https://clob.polymarket.com */
  clobBaseUrl?: string;
  /** Per-request timeout in ms. Default: 8000 */
  timeoutMs?: number;
  /** Max retries for transient errors. Default: 2 */
  maxRetries?: number;
  /** Treat prices older than this as stale. Default: 1_800_000 (30m) */
  staleAfterMs?: number;
  /** Minimum liquidity to trust an entropy sample. Default: 500 */
  minLiquidity?: number;
  /** Hard fail vs soft degraded sample. Default: 'soft' */
  failureMode?: 'soft' | 'hard';
  /** Optional fetch override (tests). */
  fetchImpl?: typeof fetch;
  /** Optional clock (tests). */
  now?: () => number;
  /** Enable live network. Default: process.env.ENABLE_POLYMARKET === '1' */
  enableLive?: boolean;
}

export interface OutcomeProbability {
  label: string;
  tokenId: string | null;
  /** Implied probability in [0, 1]. */
  probability: number;
  /** Optional CLOB mid when available. */
  midpoint: number | null;
  /** Optional CLOB buy price when available. */
  buyPrice: number | null;
}

export interface StructuredMarket {
  id: string;
  slug: string | null;
  question: string;
  conditionId: string | null;
  closed: boolean;
  active: boolean;
  acceptingOrders: boolean;
  endDate: string | null;
  updatedAt: string | null;
  liquidity: number | null;
  volume: number | null;
  outcomes: OutcomeProbability[];
  /** Shannon entropy of the outcome distribution (bits). */
  entropyBits: number;
  /** Quality flags used by the oracle. */
  quality: MarketQuality;
  fetchedAt: string;
  source: 'gamma' | 'gamma+clob' | 'cache' | 'degraded';
}

export interface MarketQuality {
  ok: boolean;
  /** True when Gamma updatedAt is older than staleAfterMs (advisory unless severe). */
  stale: boolean;
  lowLiquidity: boolean;
  closed: boolean;
  incompleteOutcomes: boolean;
  pricesSumNearOne: boolean;
  priceSum: number;
  /** Probabilities were renormalized to sum≈1. */
  renormalized: boolean;
  /** Probabilities prefer CLOB mid over Gamma outcomePrices. */
  usedClobPrices: boolean;
  warnings: string[];
}

export interface EntropySample {
  schema: 'shadow_garden.polymarket_entropy_sample.v1';
  ok: boolean;
  degraded: boolean;
  marketId: string | null;
  question: string | null;
  probabilities: number[];
  outcomes: OutcomeProbability[];
  entropyBits: number;
  /** Deterministic u32 derived from probs + market id (not cryptographic RNG). */
  entropyWord: number;
  /** Hex digest suitable for seeding sims (sha256 of structured payload). */
  seedHex: string;
  quality: MarketQuality;
  fetchedAt: string;
  error: string | null;
  failureMode: 'soft' | 'hard';
}

export interface ListMarketsQuery {
  closed?: boolean;
  limit?: number;
  afterCursor?: string;
  tagId?: number;
  order?: string;
  ascending?: boolean;
  slug?: string;
}

export interface ListMarketsResult {
  markets: StructuredMarket[];
  nextCursor: string | null;
  rawCount: number;
}

export interface ClientStatus {
  schema: 'shadow_garden.polymarket_client_status.v1';
  enableLive: boolean;
  gammaBaseUrl: string;
  clobBaseUrl: string;
  timeoutMs: number;
  maxRetries: number;
  staleAfterMs: number;
  minLiquidity: number;
  failureMode: 'soft' | 'hard';
  rateLimits: {
    gammaMarketsPer10s: number;
    clobPricePer10s: number;
  };
  discord: {
    communityInvite: string;
    notifyBridge: string;
    liveRequires: string[];
  };
  perplexity: {
    autoConnectCli: string;
    centralControlCli: string;
  };
}

export class PolymarketError extends Error {
  readonly code: string;
  readonly status: number | null;
  readonly retryable: boolean;

  constructor(
    code: string,
    message: string,
    opts: { status?: number | null; retryable?: boolean } = {},
  ) {
    super(message);
    this.name = 'PolymarketError';
    this.code = code;
    this.status = opts.status ?? null;
    this.retryable = Boolean(opts.retryable);
  }
}
