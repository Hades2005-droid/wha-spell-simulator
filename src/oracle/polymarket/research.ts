/**
 * Research snapshot for Polymarket public APIs (as of 2026-07 docs.polymarket.com).
 * Used by the client status surface and bridge catalogs — no secrets.
 */

export const POLYMARKET_RESEARCH = {
  schema: 'shadow_garden.polymarket_api_research.v1',
  researchedAt: '2026-07-24',
  docs: {
    overview: 'https://docs.polymarket.com/api-reference/introduction',
    rateLimits: 'https://docs.polymarket.com/api-reference/rate-limits',
    fetchingMarkets: 'https://docs.polymarket.com/market-data/fetching-markets',
    llmsIndex: 'https://docs.polymarket.com/llms.txt',
  },
  surfaces: {
    gamma: {
      baseUrl: 'https://gamma-api.polymarket.com',
      purpose: 'Discover events/markets + metadata (outcomePrices, clobTokenIds)',
      authForRead: 'none',
      keyEndpoints: [
        'GET /markets/keyset',
        'GET /markets/{id}',
        'GET /markets/slug/{slug}',
        'GET /events/keyset',
        'GET /public-search',
      ],
    },
    clob: {
      baseUrl: 'https://clob.polymarket.com',
      purpose: 'Live order book / midpoint / price (trading needs auth; reads public)',
      authForRead: 'none for /price /midpoint /book',
      keyEndpoints: [
        'GET /price?token_id=&side=',
        'GET /midpoint?token_id=',
        'GET /book?token_id=',
        'GET /prices-history',
      ],
    },
    dataApi: {
      baseUrl: 'https://data-api.polymarket.com',
      purpose: 'Positions, trades, activity after discovery',
      authForRead: 'public for many market activity endpoints',
    },
  },
  rateLimits: {
    note: 'Cloudflare throttles (delay/queue) rather than always hard-rejecting; sliding windows.',
    gamma: {
      generalPer10s: 4000,
      marketsPer10s: 300,
      eventsPer10s: 500,
      marketsPlusEventsListingPer10s: 900,
      publicSearchPer10s: 350,
    },
    clob: {
      generalPer10s: 9000,
      bookPer10s: 1500,
      pricePer10s: 1500,
      pricesPer10s: 500,
      midpointPer10s: 1500,
      pricesHistoryPer10s: 1000,
    },
    dataApi: {
      generalPer10s: 1000,
      tradesPer10s: 200,
    },
  },
  dataQualityIssues: [
    'outcomePrices and outcomes often arrive as JSON-encoded strings, not arrays',
    'Gamma outcomePrices can lag CLOB mid; enrich when precision matters',
    'Low-liquidity markets have noisy / jump-discontinuous implied probs',
    'Closed or resolving markets may still appear briefly in open listings',
    'updatedAt may be missing or far behind last trade',
    'Outcome price vectors can sum ≠ 1 (fees, spread, stale book)',
    'Offset pagination on /markets/keyset returns 422 — use after_cursor',
    'Some order= query values on /markets/keyset return 422 — rank client-side (pickBestMarket)',
  ],
  failureModes: [
    {
      id: 'rate_limit_throttle',
      symptom: 'Elevated latency or 429',
      defense: 'Local sliding-window limiter + Retry-After backoff + circuit breaker',
    },
    {
      id: 'timeout',
      symptom: 'Hang / AbortError',
      defense: 'Per-request AbortController timeout (default 8s)',
    },
    {
      id: 'stale_prices',
      symptom: 'entropy from outdated probs',
      defense: 'staleAfterMs quality flag; soft-degrade sample',
    },
    {
      id: 'low_liquidity',
      symptom: 'unstable oracle entropy',
      defense: 'minLiquidity gate; prefer quality.ok markets',
    },
    {
      id: 'live_disabled',
      symptom: 'no network in Gate-10 / default',
      defense: 'ENABLE_POLYMARKET=1 required; emptySample soft fail',
    },
    {
      id: 'clob_404',
      symptom: 'token missing on CLOB',
      defense: 'null mid/price; keep Gamma probs',
    },
    {
      id: 'ssl_or_network',
      symptom: 'fetch/TLS failure',
      defense: 'retries then soft emptySample (failureMode soft)',
    },
  ],
  discord: {
    communityInvite: 'https://discord.com/invite/polymarket',
    communityLabel: 'Polymarket Discord',
    whaBridge: 'tools/discord_bot_bridge.py',
    note: 'Community invite is public metadata; live bot posts still need ENABLE_DISCORD + DISCORD_LIVE_OK',
  },
  perplexity: {
    role: 'auto-connect research + central control leverage for oracle work going forward',
    healthCli: 'python3 tools/perplexity_connect.py health',
    searchCli: 'python3 tools/perplexity_connect.py search --query "..."',
    central: 'python3 tools/perplexity_asuna_central_control.py write',
  },
} as const;
