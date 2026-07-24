#!/usr/bin/env node
/**
 * CLI: Polymarket entropy oracle status / sample (TypeScript via Node strip-types).
 *
 *   node --experimental-strip-types tools/polymarket_oracle.mjs status
 *   ENABLE_POLYMARKET=1 node --experimental-strip-types tools/polymarket_oracle.mjs sample
 */

import { createPolymarketClient, POLYMARKET_RESEARCH } from '../src/oracle/polymarket/index.ts';

const [cmd = 'status', ...rest] = process.argv.slice(2);
const client = createPolymarketClient();

function arg(name, fallback = null) {
  const i = rest.indexOf(name);
  if (i >= 0 && rest[i + 1]) return rest[i + 1];
  return fallback;
}

async function main() {
  if (cmd === 'research') {
    console.log(JSON.stringify(POLYMARKET_RESEARCH, null, 2));
    return 0;
  }
  if (cmd === 'status') {
    console.log(JSON.stringify(client.status(), null, 2));
    return 0;
  }
  if (cmd === 'sample') {
    const sample = await client.entropyOracle({
      marketId: arg('--id'),
      slug: arg('--slug'),
      enrichClob: rest.includes('--enrich-clob'),
    });
    console.log(JSON.stringify(sample, null, 2));
    return sample.ok || sample.degraded ? 0 : 1;
  }
  if (cmd === 'list') {
    const page = await client.listMarkets({
      closed: false,
      limit: Number(arg('--limit', '5')),
    });
    console.log(
      JSON.stringify(
        {
          count: page.markets.length,
          nextCursor: page.nextCursor,
          markets: page.markets.map((m) => ({
            id: m.id,
            question: m.question,
            entropyBits: m.entropyBits,
            quality: m.quality,
            probabilities: m.outcomes.map((o) => ({
              label: o.label,
              probability: o.probability,
            })),
          })),
        },
        null,
        2,
      ),
    );
    return 0;
  }
  console.error('Usage: status | research | sample [--id ID|--slug SLUG] [--enrich-clob] | list [--limit N]');
  return 2;
}

main().then((code) => process.exit(code));
