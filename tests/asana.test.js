/**
 * Asana Connector Tests.
 *
 * All network access is stubbed by default. No live Asana calls are made
 * unless RUN_LIVE_ASANA_TESTS=1 is set (see the guarded suite at the end).
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';

import { loadAsanaConfig, describeAsanaConfig } from '../src/reporting/asanaConfig.js';
import { AsanaAdapter, redactBearerTokens } from '../src/reporting/asanaAdapter.js';
import {
  toSample, aggregateMetrics, formatMetricsComment, sanitizeLabel,
} from '../src/reporting/asanaMetrics.js';
import { AsanaReporter } from '../src/reporting/asanaReporter.js';

const NODE_ENV = {};

function makeFetchStub(recorder, response = {}) {
  const {
    ok = true, status = 200, body = { data: { gid: '123' } },
  } = response;
  return async (url, init) => {
    recorder.push({ url, init });
    return {
      ok,
      status,
      text: async () => JSON.stringify(body),
    };
  };
}

const enabledEnv = {
  ...NODE_ENV,
  ASANA_ACCESS_TOKEN: 'test-token-should-never-be-logged',
  ASANA_PROJECT_SPELLSIM: 'proj-1',
  ASANA_REPORTING_ENABLED: '1',
};

describe('Asana config', () => {
  it('is disabled by default with no env', () => {
    const config = loadAsanaConfig({ ...NODE_ENV });
    assert.strictEqual(config.enabled, false);
    assert.strictEqual(config.hasToken, false);
    assert.strictEqual(config.getToken(), null);
  });

  it('requires explicit enable + token + destination', () => {
    const noEnable = loadAsanaConfig({
      ...NODE_ENV, ASANA_ACCESS_TOKEN: 't', ASANA_PROJECT_SPELLSIM: 'p',
    });
    assert.strictEqual(noEnable.enabled, false, 'not enabled without ASANA_REPORTING_ENABLED');

    const noDest = loadAsanaConfig({
      ...NODE_ENV, ASANA_ACCESS_TOKEN: 't', ASANA_REPORTING_ENABLED: '1',
    });
    assert.strictEqual(noDest.enabled, false, 'not enabled without a destination');

    const good = loadAsanaConfig(enabledEnv);
    assert.strictEqual(good.enabled, true);
    assert.strictEqual(good.getToken(), 'test-token-should-never-be-logged');
  });

  it('never exposes the token via describe/serialization', () => {
    const config = loadAsanaConfig(enabledEnv);
    const described = describeAsanaConfig(config);
    const serialized = JSON.stringify(described);
    assert.ok(!serialized.includes('test-token'), 'token must not appear in describe output');
    assert.strictEqual(described.tokenPresent, true);

    // Direct serialization of the frozen config must not leak the token either.
    assert.ok(!JSON.stringify(config).includes('test-token'), 'token must not serialize');
  });

  it('refuses token access in browser-like contexts', () => {
    const originalWindow = globalThis.window;
    globalThis.window = {};
    try {
      // A DOM `window` is present -> treated as browser, token withheld.
      const config = loadAsanaConfig({
        ASANA_ACCESS_TOKEN: 't', ASANA_PROJECT_SPELLSIM: 'p', ASANA_REPORTING_ENABLED: '1',
      });
      assert.strictEqual(config.getToken(), null, 'token withheld in browser');
      assert.strictEqual(config.enabled, false, 'reporting disabled in browser');
    } finally {
      if (originalWindow === undefined) delete globalThis.window;
      else globalThis.window = originalWindow;
    }
  });
});

describe('Asana adapter', () => {
  it('is not ready without a token', () => {
    const adapter = new AsanaAdapter({
      config: loadAsanaConfig({ ...NODE_ENV }),
      fetch: async () => ({ ok: true, status: 200, text: async () => '{}' }),
    });
    assert.strictEqual(adapter.isReady(), false);
  });

  it('sends bearer auth and wraps body in { data }', async () => {
    const calls = [];
    const adapter = new AsanaAdapter({
      config: loadAsanaConfig(enabledEnv),
      fetch: makeFetchStub(calls, { body: { data: { gid: 'story-1' } } }),
    });
    const result = await adapter.addComment('task-9', 'hello');
    assert.strictEqual(result.gid, 'story-1');
    assert.strictEqual(calls.length, 1);
    assert.match(calls[0].url, /\/tasks\/task-9\/stories$/);
    assert.strictEqual(calls[0].init.headers.Authorization, 'Bearer test-token-should-never-be-logged');
    assert.deepStrictEqual(JSON.parse(calls[0].init.body), { data: { text: 'hello' } });
  });

  it('throws a redacted error on HTTP failure', async () => {
    const adapter = new AsanaAdapter({
      config: loadAsanaConfig(enabledEnv),
      fetch: async () => ({
        ok: false,
        status: 401,
        text: async () => JSON.stringify({ errors: [{ message: 'Not Authorized' }] }),
      }),
    });
    await assert.rejects(() => adapter.getMe(), /401: Not Authorized/);
  });

  it('redacts bearer tokens from messages', () => {
    const redacted = redactBearerTokens('failed with Bearer abc.def-123 token');
    assert.ok(!redacted.includes('abc.def-123'));
    assert.match(redacted, /Bearer \[REDACTED\]/);
  });
});

describe('Asana metrics', () => {
  const validSample = {
    spellIR: {
      valid: true,
      quality: 0.8,
      stability: 0.7,
      neatness: 0.75,
      directionCoherence: 0.6,
      elementConfidence: 0.9,
    },
    glyphAST: {
      primarySigil: { confidence: 0.9 },
      signs: [{ confidence: 0.8 }],
      globalMetrics: { neatness: 0.75 },
    },
  };
  const invalidSample = { spellIR: { valid: false }, glyphAST: {} };

  it('reduces a compiled spell to a sanitized numeric sample', () => {
    const sample = toSample(validSample);
    assert.strictEqual(sample.valid, true);
    assert.ok(sample.recognitionAccuracy > 0 && sample.recognitionAccuracy <= 1);
    assert.ok(sample.soulResonance > 0 && sample.soulResonance <= 1);
    // No coordinate/raw data leaks into the sample.
    assert.deepStrictEqual(
      Object.keys(sample).sort(),
      ['compiled', 'copyEffectiveness', 'recognitionAccuracy', 'soulResonance', 'valid'],
    );
  });

  it('computes compilation success rate across samples', () => {
    const metrics = aggregateMetrics([validSample, invalidSample]);
    assert.strictEqual(metrics.sampleCount, 2);
    assert.strictEqual(metrics.compilationSuccessRate, 0.5);
    assert.ok(metrics.glyphRecognitionAccuracy >= 0);
    assert.ok(metrics.soulAlignmentResonance >= 0);
  });

  it('handles empty input without dividing by zero', () => {
    const metrics = aggregateMetrics([]);
    assert.strictEqual(metrics.sampleCount, 0);
    assert.strictEqual(metrics.compilationSuccessRate, 0);
  });

  it('formats a sanitized comment body', () => {
    const metrics = aggregateMetrics([validSample]);
    const comment = formatMetricsComment(metrics, { milestone: 'Sprint 1', appVersion: '0.1.0' });
    assert.match(comment, /Glyph recognition accuracy:/);
    assert.match(comment, /Compilation success rate:/);
    assert.match(comment, /Milestone: Sprint 1/);
  });

  it('sanitizeLabel strips control chars and markup', () => {
    assert.strictEqual(sanitizeLabel('bad\n<script>alert(1)</script>'), 'bad scriptalert1/script');
    assert.strictEqual(sanitizeLabel('Sprint 3: Glyphs/AST +1'), 'Sprint 3: Glyphs/AST +1');
  });
});

describe('Asana reporter', () => {
  it('skips (non-blocking) when disabled', async () => {
    const reporter = new AsanaReporter({ config: loadAsanaConfig({ ...NODE_ENV }) });
    const result = await reporter.reportMetrics([{ spellIR: { valid: true } }]);
    assert.strictEqual(result.skipped, true);
    assert.strictEqual(result.ok, false);
  });

  it('posts a comment to a configured task', async () => {
    const calls = [];
    const config = loadAsanaConfig({ ...enabledEnv, ASANA_TASK_ID: 'task-42' });
    const reporter = new AsanaReporter({ config, fetch: makeFetchStub(calls) });
    const result = await reporter.reportMetrics([{ spellIR: { valid: true, quality: 0.5 } }], {
      milestone: 'M1',
    });
    assert.strictEqual(result.ok, true);
    assert.strictEqual(result.target, 'task');
    assert.match(calls[0].url, /\/tasks\/task-42\/stories$/);
  });

  it('creates a task in a project when no task id is set', async () => {
    const calls = [];
    const reporter = new AsanaReporter({
      config: loadAsanaConfig(enabledEnv),
      fetch: makeFetchStub(calls),
    });
    const result = await reporter.reportMetrics([{ spellIR: { valid: true } }], { milestone: 'M2' });
    assert.strictEqual(result.ok, true);
    assert.strictEqual(result.target, 'project');
    assert.match(calls[0].url, /\/tasks$/);
    const sent = JSON.parse(calls[0].init.body).data;
    assert.deepStrictEqual(sent.projects, ['proj-1']);
  });

  it('is non-blocking on network errors', async () => {
    const reporter = new AsanaReporter({
      config: loadAsanaConfig({ ...enabledEnv, ASANA_TASK_ID: 'task-1' }),
      fetch: async () => { throw new Error('network down'); },
    });
    const result = await reporter.reportMetrics([{ spellIR: { valid: true } }]);
    assert.strictEqual(result.ok, false);
    assert.strictEqual(result.skipped, false);
    assert.match(result.error, /network down/);
  });

  it('never includes the token in reporter output', async () => {
    const calls = [];
    const reporter = new AsanaReporter({
      config: loadAsanaConfig({ ...enabledEnv, ASANA_TASK_ID: 'task-1' }),
      fetch: makeFetchStub(calls),
    });
    const result = await reporter.reportMetrics([{ spellIR: { valid: true } }]);
    assert.ok(!JSON.stringify(result).includes('test-token'));
  });
});

// Live tests are opt-in only. They never run in CI/default `npm test`.
const runLive = process.env.RUN_LIVE_ASANA_TESTS === '1';
describe('Asana live (opt-in)', { skip: !runLive }, () => {
  it('verifies real credentials', async () => {
    const reporter = new AsanaReporter({ config: loadAsanaConfig({ ...process.env }) });
    const result = await reporter.verify();
    assert.strictEqual(result.ok, true, `verify failed: ${JSON.stringify(result)}`);
  });
});
