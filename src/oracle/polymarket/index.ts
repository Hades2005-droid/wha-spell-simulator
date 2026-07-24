/**
 * Polymarket entropy oracle — public market probabilities → sim seed material.
 */

export { PolymarketClient, createPolymarketClient } from './client.ts';
export {
  sampleFromMarket,
  emptySample,
  entropyWordFromProbs,
  seedHexFromSample,
} from './entropy.ts';
export {
  parseMaybeJsonArray,
  shannonEntropyBits,
  assessQuality,
  structureMarket,
  normalizeProbabilities,
  pickBestMarket,
  applyClobMidsToOutcomes,
} from './parse.ts';
export { POLYMARKET_RESEARCH } from './research.ts';
export { SlidingWindowLimiter } from './rateLimit.ts';
export { DefensiveHttp } from './http.ts';
export type {
  PolymarketClientOptions,
  OutcomeProbability,
  StructuredMarket,
  MarketQuality,
  EntropySample,
  ListMarketsQuery,
  ListMarketsResult,
  ClientStatus,
} from './types.ts';
export { PolymarketError } from './types.ts';
