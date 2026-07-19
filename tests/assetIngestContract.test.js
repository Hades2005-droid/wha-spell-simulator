// assetIngestContract.test.js
// Asserts the JS Eden ingest contract matches the shared, language-neutral
// vectors in tests/fixtures/ingest-contract-vectors.json. The same fixture is
// the source of truth for the C++ eden::MetadataCatalog, so this test failing
// means JS and C++ have diverged on how they key sha256 provenance.

import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

import {
  AssetIngestCatalog,
  absorbSequence,
  classifySource,
  isRemoteSource,
  looksSecretNamedSource,
  INGEST_POLICY_DEFAULTS,
  INGEST_REASONS,
} from "../src/compiler/assetIngestContract.js";

const HERE = dirname(fileURLToPath(import.meta.url));
const fixture = JSON.parse(
  readFileSync(join(HERE, "fixtures", "ingest-contract-vectors.json"), "utf8"),
);

test("shared fixture: every decision matches, in order", () => {
  const records = fixture.sequence.map((c) => c.record);
  const { decisions, accepted, totalBytes } = absorbSequence(records, fixture.policy);

  fixture.sequence.forEach((c, i) => {
    const decision = decisions[i];
    if (c.expect === "accepted") {
      assert.equal(decision.accepted, true, `case ${i} (${c.note}) should be accepted`);
      assert.equal(decision.reason, "");
    } else {
      assert.equal(decision.accepted, false, `case ${i} (${c.note}) should be rejected`);
      assert.equal(decision.reason, c.expect, `case ${i} (${c.note}) reason`);
    }
  });

  assert.equal(accepted, fixture.expectedFinal.accepted, "accepted count");
  assert.equal(totalBytes, fixture.expectedFinal.totalBytes, "total bytes");
});

test("fixture only uses reasons the contract defines", () => {
  for (const c of fixture.sequence) {
    if (c.expect !== "accepted") {
      assert.ok(INGEST_REASONS.includes(c.expect), `unknown reason ${c.expect}`);
    }
  }
});

test("policy defaults mirror the C++ struct", () => {
  assert.deepEqual(INGEST_POLICY_DEFAULTS, {
    maxDepth: 2,
    maxEntries: 5000,
    maxBytes: 64 * 1024 * 1024,
    maxRecordBytes: 16 * 1024 * 1024,
  });
});

test("remote + secret-named sources are rejected", () => {
  assert.ok(isRemoteSource("https://a/b"));
  assert.ok(isRemoteSource("file://host/x"));
  assert.ok(!isRemoteSource("/home/u/a.png"));
  assert.ok(looksSecretNamedSource("/home/u/.env"));
  assert.ok(looksSecretNamedSource("/x/PRIVATE_KEY.pem"));
  assert.ok(!looksSecretNamedSource("/home/u/photo.png"));
});

test("classifySource: astro-node / land / data", () => {
  assert.equal(classifySource("/x/lunar-node.png"), "astro-node");
  assert.equal(classifySource("/x/world-map.png"), "land");
  assert.equal(classifySource("/x/photo.png"), "data");
});

test("duplicate digest is rejected even from a different path", () => {
  const cat = new AssetIngestCatalog();
  const sha = "e".repeat(64);
  assert.equal(cat.absorb({ source: "/a.png", sha256: sha, bytes: 1 }).accepted, true);
  const dup = cat.absorb({ source: "/b.png", sha256: sha, bytes: 1 });
  assert.equal(dup.accepted, false);
  assert.equal(dup.reason, "duplicate_content");
});
