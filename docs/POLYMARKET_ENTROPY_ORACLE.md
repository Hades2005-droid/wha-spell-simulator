# Polymarket entropy oracle

Read-only TypeScript client that turns Polymarket outcome probabilities into
structured entropy for the local spell simulation. Live fetches are **off**
until `ENABLE_POLYMARKET=1`.

## Package

| Path | Role |
|------|------|
| `src/oracle/polymarket/` | Clean TypeScript client + entropy oracle |
| `tools/polymarket_oracle.mjs` | CLI (`status` / `research` / `sample` / `list`) |
| `tools/polymarket_asuna_point0_unify.py` | Asuna Point-0 catalog + Discord/Perplexity pointers |
| `shadow_garden_handoff/bridges/polymarket_entropy_oracle.json` | Generated bridge |
| `tools/perplexity_connect.py` | Auto-connect research (certifi SSL) |
| `src/bridge/polymarketDiscord.js` | Discord bot + Polymarket community surface |
| `src/bridge/perplexityConnect.js` | Perplexity auto-connect manifest |

## Quick start

```bash
node --experimental-strip-types tools/polymarket_oracle.mjs status
node --experimental-strip-types tools/polymarket_oracle.mjs research
ENABLE_POLYMARKET=1 node --experimental-strip-types tools/polymarket_oracle.mjs sample
python3 tools/polymarket_asuna_point0_unify.py write
python3 tools/perplexity_connect.py health
python3 tools/discord_bot_bridge.py status
```

## API surface (research)

Sources: [API overview](https://docs.polymarket.com/api-reference/introduction),
[rate limits](https://docs.polymarket.com/api-reference/rate-limits),
[fetching markets](https://docs.polymarket.com/market-data/fetching-markets).

| API | Base | Read auth | Use here |
|-----|------|-----------|----------|
| **Gamma** | `https://gamma-api.polymarket.com` | none | Market metadata, `outcomePrices`, token ids |
| **CLOB** | `https://clob.polymarket.com` | none for `/price` `/midpoint` `/book` | Live mids / buy prices |
| **Data** | `https://data-api.polymarket.com` | mostly public activity | Not required for entropy |

Prefer **`GET /markets/keyset`**. Offset pagination on keyset endpoints returns **422**.

### Rate limits (sliding 10s windows; Cloudflare may throttle)

| Surface | Cap |
|---------|-----|
| Gamma `/markets` | 300 / 10s |
| Gamma general | 4,000 / 10s |
| CLOB `/price` `/midpoint` | 1,500 / 10s each |
| CLOB general | 9,000 / 10s |

Local client budgets stay **well under** these (60 Gamma / 120 CLOB per 10s).

## Quality traps (solved in client)

| Trap | Fix |
|------|-----|
| JSON-string `outcomePrices` | `parseMaybeJsonArray` |
| sum ≠ 1 (spread/fees) | `normalizeProbabilities` when sum ∈ [0.85, 1.15] |
| Gamma lag vs book | auto CLOB mid enrich; `usedClobPrices` |
| `updatedAt` lag | advisory `metadata_stale_updatedAt` — does **not** alone fail `ok` |
| Thin books | `minLiquidity` gate + `pickBestMarket` ranking |
| Offset pagination | always `/markets/keyset` |
## Failure modes + defenses

| Mode | Defense |
|------|---------|
| Rate limit / 429 | Local sliding window + `Retry-After` backoff + circuit breaker |
| Timeout | 8s `AbortController` |
| Stale / low liquidity | Quality flags → soft degraded sample (default stale window **30m**; Gamma `updatedAt` often lags) |
| Live off (default) | `emptySample('live_disabled')` — sim keeps running |
| CLOB 404 | Keep Gamma probs; null mid/price |
| Hard mode | `failureMode: 'hard'` throws / rejects instead of degrade |

## Discord

- Community (public): https://discord.com/invite/polymarket
- WHA bot bridge: `tools/discord_bot_bridge.py` (still dual-gated: `ENABLE_DISCORD` + `DISCORD_LIVE_OK`)
- Oracle health notify helper: `src/bridge/polymarketDiscord.js` → `notifyOracleHealth`

## Perplexity (going forward)

MCP `perplexity_search` failed here on macOS Python SSL; use the local connector:

```bash
python3 tools/perplexity_connect.py health
python3 tools/perplexity_connect.py search --query "Polymarket Gamma keyset pagination"
```

Central control now includes the `polymarket` surface:

```bash
python3 tools/perplexity_asuna_central_control.py write
```
