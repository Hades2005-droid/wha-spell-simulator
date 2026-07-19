// assetIngestContract.js
// The canonical JavaScript implementation of the Eden ingest contract — a
// faithful port of the C++ `eden::MetadataCatalog::absorb` in
// `cpp/include/eden/ingest_policy.hpp`. Both sides key provenance on the same
// SHA-256 digest and apply the SAME rejection precedence, so a record accepted
// (or rejected) by the C++ catalog is accepted (or rejected) identically here.
//
// Why this exists: the project's cryptography is SHA-256 asset digests feeding a
// fingerprint. That digest contract was previously enforced twice — once in C++
// (`absorb`) and once, differently, in JS (`mergeLocalAssetSources`, which only
// deduped on digest with no path/capacity/byte precedence). This module unifies
// the two on one contract, and `tests/fixtures/ingest-contract-vectors.json` is
// the shared, language-neutral source of truth both suites assert against.
//
// Local-only by construction: remote and secret-named sources are rejected
// before anything is admitted. Pure and isomorphic — no Node or browser APIs.

/** Policy bounds — mirror `struct IngestPolicy` defaults exactly. */
export const INGEST_POLICY_DEFAULTS = Object.freeze({
  maxDepth: 2,
  maxEntries: 5000,
  maxBytes: 64 * 1024 * 1024, // 64 MiB cumulative
  maxRecordBytes: 16 * 1024 * 1024, // 16 MiB per record
});

/** Rejection reasons, in the exact order `absorb` checks them. */
export const INGEST_REASONS = Object.freeze([
  "empty_source",
  "remote_source_rejected",
  "secret_named_path_rejected",
  "missing_digest",
  "depth_limit_exceeded",
  "record_byte_limit_exceeded",
  "duplicate_path",
  "duplicate_content",
  "entry_limit_exceeded",
  "total_byte_limit_exceeded",
]);

const SECRET_MARKERS = [
  ".env", "api_key", "apikey", "password", "secret", "token",
  "credentials", "private_key",
];
const ASTRO_MARKERS = ["astro", "astronomy", "node", "moon", "lunar", "celestial"];
const LAND_MARKERS = ["land", "terrain", "region", "world"];

/** Any `scheme://` authority is remote and rejected (mirrors `isRemoteSource`). */
export function isRemoteSource(source) {
  return String(source).includes("://");
}

/** True if the path names a secret, so we never ingest credential files. */
export function looksSecretNamedSource(source) {
  const lowered = String(source).toLowerCase();
  return SECRET_MARKERS.some((marker) => lowered.includes(marker));
}

/** Classify a source into 'astro-node' | 'land' | 'data' (mirrors `classifySource`). */
export function classifySource(source) {
  const lowered = String(source).toLowerCase();
  if (ASTRO_MARKERS.some((m) => lowered.includes(m))) return "astro-node";
  if (LAND_MARKERS.some((m) => lowered.includes(m))) return "land";
  return "data";
}

/**
 * A digest-keyed catalog that admits metadata records under the Eden contract.
 * Instances are stateful across `.absorb()` calls, exactly like the C++ class,
 * so duplicate-path / duplicate-content / capacity decisions depend on history.
 */
export class AssetIngestCatalog {
  constructor(policy = {}) {
    this.policy = { ...INGEST_POLICY_DEFAULTS, ...policy };
    this.records = [];
    this.totalBytes = 0;
    this._sources = new Set();
    this._digests = new Set();
  }

  /**
   * @param {{source:string, sha256:string, bytes?:number, depth?:number}} record
   * @returns {{accepted:boolean, reason:string}} reason is "" when accepted.
   */
  absorb(record = {}) {
    const source = record.source == null ? "" : String(record.source);
    const sha256 = record.sha256 == null ? "" : String(record.sha256);
    const bytes = Number.isFinite(record.bytes) ? record.bytes : 0;
    const depth = Number.isFinite(record.depth) ? record.depth : 0;
    const { policy } = this;

    if (source === "") return reject("empty_source");
    if (isRemoteSource(source)) return reject("remote_source_rejected");
    if (looksSecretNamedSource(source)) return reject("secret_named_path_rejected");
    if (sha256 === "") return reject("missing_digest");
    if (depth > policy.maxDepth) return reject("depth_limit_exceeded");
    if (bytes > policy.maxRecordBytes) return reject("record_byte_limit_exceeded");
    // Duplicate checks run before capacity so a full catalog still reports the
    // duplicate reason instead of masking it with entry_limit_exceeded.
    if (this._sources.has(source)) return reject("duplicate_path");
    if (this._digests.has(sha256)) return reject("duplicate_content");
    if (this.records.length >= policy.maxEntries) return reject("entry_limit_exceeded");
    if (bytes > policy.maxBytes - Math.min(this.totalBytes, policy.maxBytes)) {
      return reject("total_byte_limit_exceeded");
    }

    this._sources.add(source);
    this._digests.add(sha256);
    this.records.push({ source, sha256, bytes, depth, kind: classifySource(source) });
    this.totalBytes += bytes;
    return { accepted: true, reason: "" };
  }
}

function reject(reason) {
  return { accepted: false, reason };
}

/**
 * Replay a sequence of records through a fresh catalog and return one decision
 * per input, in order. This is the shape the shared fixture asserts against.
 */
export function absorbSequence(records = [], policy = {}) {
  if (!Array.isArray(records)) {
    throw new Error("absorbSequence requires an array of records");
  }
  const catalog = new AssetIngestCatalog(policy);
  const decisions = records.map((record) => catalog.absorb(record));
  return { decisions, accepted: catalog.records.length, totalBytes: catalog.totalBytes };
}
