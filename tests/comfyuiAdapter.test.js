/**
 * Fable 5 -> ComfyUI adapter tests.
 * Deterministic: no network, no wall-clock, no RNG. A fake fetch is injected
 * wherever I/O gating is exercised so the suite runs fully offline.
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import adapter, {
  ADAPTER_ROLES,
  ADAPTER_ENDPOINTS,
  DEFAULT_POLICY,
  MEDIA_TYPES,
  PROVENANCE,
  compileManifest,
  screenContent,
  assertContentAllowed,
  normalizePolicy,
  isLocalEndpoint,
  checkComfyUiHealth,
  queueManifest,
  ContentRejectedError,
  PolicyViolationError,
} from '../eden/comfyuiAdapter.mjs';

const baseSpec = {
  media: 'image',
  intent: 'a glowing witch-hat sigil radiating warm firelight over parchment',
  roles: [{ id: 'caster', descriptor: 'abstract robed figure' }],
  tags: ['fire', 'atelier'],
  spell: { element: 'fire', quality: 0.8, stability: 0.6 },
};

describe('Fable5 ComfyUI adapter', () => {
  describe('constants and provenance', () => {
    it('exposes the two supported adapter roles', () => {
      assert.deepStrictEqual(
        [...ADAPTER_ROLES],
        ['unification_target', 'fable5_comfyui_open_merge_target'],
      );
    });

    it('pins local-only endpoints (Fable5 5619, ComfyUI 8188, EDEN 8791)', () => {
      assert.strictEqual(ADAPTER_ENDPOINTS.fable5, 'http://127.0.0.1:5619');
      assert.strictEqual(ADAPTER_ENDPOINTS.comfyui, 'http://127.0.0.1:8188');
      assert.strictEqual(ADAPTER_ENDPOINTS.eden, 'http://127.0.0.1:8791');
      assert.strictEqual(ADAPTER_ENDPOINTS.comfyuiHealthPath, '/system_stats');
    });

    it('carries canonical task provenance and policy pointer', () => {
      assert.strictEqual(PROVENANCE.targetTaskId, '37bce2fb-1ba6-471f-854f-3871d9c19947');
      assert.strictEqual(PROVENANCE.leadTaskId, '2366bfee-b78c-4ddc-9f86-304c30c67c4d');
      assert.strictEqual(PROVENANCE.policy, 'no_scrape_pointer_only');
      assert.strictEqual(PROVENANCE.branch, 'fable5-comfyui-unification');
    });

    it('defaults to manifest_only with safety caps locked', () => {
      assert.strictEqual(DEFAULT_POLICY.mode, 'manifest_only');
      assert.strictEqual(DEFAULT_POLICY.approve, false);
      assert.strictEqual(DEFAULT_POLICY.externalRequests, 0);
      assert.strictEqual(DEFAULT_POLICY.trainingAllowed, false);
      assert.strictEqual(DEFAULT_POLICY.autoDownloadWeights, false);
      assert.strictEqual(DEFAULT_POLICY.maxVideoSeconds, 30);
      assert.strictEqual(DEFAULT_POLICY.maxRoles, 5);
    });
  });

  describe('normalizePolicy', () => {
    it('re-clamps hard caps so callers can only tighten', () => {
      const p = normalizePolicy({
        maxVideoSeconds: 600,
        maxRoles: 50,
        trainingAllowed: true,
        autoDownloadWeights: true,
        externalRequests: 99,
      });
      assert.strictEqual(p.maxVideoSeconds, 30);
      assert.strictEqual(p.maxRoles, 5);
      assert.strictEqual(p.trainingAllowed, false);
      assert.strictEqual(p.autoDownloadWeights, false);
      assert.strictEqual(p.externalRequests, 0);
      assert.strictEqual(p.scrape, 'no_scrape_pointer_only');
    });

    it('allows callers to tighten a cap below the default', () => {
      assert.strictEqual(normalizePolicy({ maxVideoSeconds: 10 }).maxVideoSeconds, 10);
    });
  });

  describe('compileManifest determinism', () => {
    it('is byte-stable for identical input', () => {
      const a = compileManifest(baseSpec);
      const b = compileManifest(baseSpec);
      assert.strictEqual(JSON.stringify(a), JSON.stringify(b));
      assert.strictEqual(a.manifestId, b.manifestId);
    });

    it('changes manifestId when intent changes', () => {
      const a = compileManifest(baseSpec);
      const b = compileManifest({ ...baseSpec, intent: 'a cold water sigil' });
      assert.notStrictEqual(a.manifestId, b.manifestId);
    });

    it('produces a v1 image graph with pointer-only weights', () => {
      const m = compileManifest(baseSpec);
      assert.strictEqual(m.schema, 'fable5.comfyui.manifest.v1');
      assert.strictEqual(m.media, 'image');
      assert.strictEqual(m.role, 'unification_target');
      assert.strictEqual(m.prompt.save.class_type, 'SaveImage');
      const ckpt = m.prompt.checkpoint_loader.inputs.ckpt_name;
      assert.strictEqual(ckpt.source, 'local_pointer');
      assert.strictEqual(ckpt.autoDownload, false);
      assert.strictEqual(m.weights.autoDownload, false);
    });

    it('derives deterministic seed/steps/cfg within bounds', () => {
      const { parameters } = compileManifest(baseSpec);
      assert.ok(parameters.steps >= 12 && parameters.steps <= 30);
      assert.ok(parameters.cfg >= 5 && parameters.cfg <= 8);
      assert.strictEqual(parameters.seed, compileManifest(baseSpec).parameters.seed);
    });
  });

  describe('media types', () => {
    it('supports image, video, and audio', () => {
      assert.deepStrictEqual([...MEDIA_TYPES], ['image', 'video', 'audio']);
    });

    it('builds a video graph and honours the 30s cap', () => {
      const m = compileManifest({ ...baseSpec, media: 'video', durationSeconds: 8 });
      assert.strictEqual(m.durationSeconds, 8);
      assert.strictEqual(m.prompt.video_combine.class_type, 'VHS_VideoCombine');
      const fps = m.prompt.video_combine.inputs.frame_rate;
      assert.strictEqual(m.prompt.latent.inputs.batch_size, 8 * fps);
    });

    it('rejects video longer than 30s', () => {
      assert.throws(
        () => compileManifest({ ...baseSpec, media: 'video', durationSeconds: 45 }),
        (err) => err instanceof PolicyViolationError && err.code === 'duration_cap',
      );
    });

    it('builds an audio graph', () => {
      const m = compileManifest({ ...baseSpec, media: 'audio', durationSeconds: 10 });
      assert.strictEqual(m.prompt.save.class_type, 'SaveAudio');
      assert.strictEqual(m.prompt.sampler.inputs.seconds, 10);
    });

    it('rejects an unknown media type', () => {
      assert.throws(
        () => compileManifest({ ...baseSpec, media: 'hologram' }),
        (err) => err instanceof PolicyViolationError && err.code === 'unknown_media',
      );
    });
  });

  describe('roles', () => {
    it('accepts both adapter roles', () => {
      ADAPTER_ROLES.forEach((role) => {
        assert.strictEqual(compileManifest(baseSpec, { role }).role, role);
      });
    });

    it('rejects an unknown adapter role', () => {
      assert.throws(
        () => compileManifest(baseSpec, { role: 'broadcast_target' }),
        (err) => err instanceof PolicyViolationError && err.code === 'unknown_role',
      );
    });

    it('caps abstract roles at five', () => {
      const roles = Array.from({ length: 6 }, (_, i) => ({ id: `r${i}` }));
      assert.throws(
        () => compileManifest({ ...baseSpec, roles }),
        (err) => err instanceof PolicyViolationError && err.code === 'roles_max',
      );
    });

    it('normalizes all roles to abstract kind', () => {
      const m = compileManifest(baseSpec);
      assert.ok(m.roles.every((r) => r.kind === 'abstract'));
    });

    it('rejects a role requesting a real-person likeness', () => {
      assert.throws(
        () => compileManifest({ ...baseSpec, roles: [{ id: 'x', realPerson: true }] }),
        (err) => err instanceof PolicyViolationError && err.code === 'real_person_role',
      );
    });
  });

  describe('content safety guard', () => {
    const cases = {
      minors: 'a child in a compromising scene',
      non_consent: 'a forced non-consent scenario',
      incest: 'an incest storyline',
      trafficking: 'a sex trafficking ring',
      hidden_cam: 'a hidden camera voyeur clip',
      exploitation: 'revenge porn sextortion',
      real_person_likeness: 'a deepfake of a real person',
    };

    Object.entries(cases).forEach(([category, intent]) => {
      it(`blocks ${category}`, () => {
        const { allowed, violations } = screenContent({ intent });
        assert.strictEqual(allowed, false);
        assert.ok(violations.some((v) => v.category === category));
      });
    });

    it('allows benign fantasy content', () => {
      assert.strictEqual(screenContent(baseSpec).allowed, true);
    });

    it('throws ContentRejectedError during compile for prohibited content', () => {
      assert.throws(
        () => compileManifest({ ...baseSpec, intent: 'underage character' }),
        (err) => err instanceof ContentRejectedError && err.violations.length > 0,
      );
    });

    it('flags structured real-person likeness requests', () => {
      const { allowed, violations } = screenContent({ intent: 'ok', likenessOf: 'Jane Doe' });
      assert.strictEqual(allowed, false);
      assert.ok(violations.some((v) => v.category === 'real_person_likeness'));
    });

    it('assertContentAllowed is a no-op for clean specs', () => {
      assert.doesNotThrow(() => assertContentAllowed(baseSpec));
    });
  });

  describe('endpoint locality', () => {
    it('treats loopback hosts as local', () => {
      assert.strictEqual(isLocalEndpoint('http://127.0.0.1:8188'), true);
      assert.strictEqual(isLocalEndpoint('http://localhost:8188'), true);
    });

    it('treats remote hosts as external', () => {
      assert.strictEqual(isLocalEndpoint('https://api.x.ai/v1'), false);
      assert.strictEqual(isLocalEndpoint('http://example.com'), false);
    });
  });

  describe('queueManifest gating (manifest_only by default)', () => {
    const failFetch = () => {
      throw new Error('network access must not happen in manifest_only path');
    };

    it('does not queue by default (manifest_only)', async () => {
      const m = compileManifest(baseSpec);
      const res = await queueManifest(m, { fetchImpl: failFetch });
      assert.strictEqual(res.queued, false);
      assert.strictEqual(res.reason, 'manifest_only');
    });

    it('requires approve:true even in queue mode', async () => {
      const m = compileManifest(baseSpec, { policy: { mode: 'queue', allowLocalRequests: true } });
      const res = await queueManifest(m, { fetchImpl: failFetch });
      assert.strictEqual(res.queued, false);
      assert.strictEqual(res.reason, 'approval_required');
    });

    it('refuses to queue to a non-local endpoint', async () => {
      const m = compileManifest(baseSpec, { policy: { mode: 'queue', allowLocalRequests: true } });
      await assert.rejects(
        () => queueManifest(m, { approve: true, endpoint: 'https://api.x.ai/v1', fetchImpl: failFetch }),
        (err) => err instanceof PolicyViolationError && err.code === 'non_local_endpoint',
      );
    });

    it('will not touch the network unless local requests are enabled', async () => {
      const m = compileManifest(baseSpec, { policy: { mode: 'queue' } });
      const res = await queueManifest(m, { approve: true, fetchImpl: failFetch });
      assert.strictEqual(res.queued, false);
      assert.strictEqual(res.reason, 'local_requests_disabled');
    });

    it('queues to local ComfyUI only when fully approved', async () => {
      const calls = [];
      const fakeFetch = async (url, init) => {
        calls.push({ url, init });
        return { ok: true, json: async () => ({ prompt_id: 'abc-123' }) };
      };
      const m = compileManifest(baseSpec, { policy: { mode: 'queue', allowLocalRequests: true } });
      const res = await queueManifest(m, { approve: true, fetchImpl: fakeFetch });
      assert.strictEqual(res.queued, true);
      assert.strictEqual(res.promptId, 'abc-123');
      assert.strictEqual(calls.length, 1);
      assert.ok(calls[0].url.startsWith('http://127.0.0.1:8188/prompt'));
    });
  });

  describe('checkComfyUiHealth', () => {
    it('is a no-op unless local requests are enabled', async () => {
      const res = await checkComfyUiHealth({ fetchImpl: () => { throw new Error('nope'); } });
      assert.strictEqual(res.ok, false);
      assert.strictEqual(res.reason, 'local_requests_disabled');
    });

    it('refuses a non-local endpoint', async () => {
      await assert.rejects(
        () => checkComfyUiHealth({ endpoint: 'https://evil.example', policy: { allowLocalRequests: true } }),
        (err) => err instanceof PolicyViolationError && err.code === 'non_local_endpoint',
      );
    });

    it('hits /system_stats on the local endpoint when enabled', async () => {
      let hit = null;
      const fakeFetch = async (url) => {
        hit = url;
        return { ok: true, json: async () => ({ system: { os: 'linux' } }) };
      };
      const res = await checkComfyUiHealth({
        policy: { allowLocalRequests: true },
        fetchImpl: fakeFetch,
      });
      assert.strictEqual(res.ok, true);
      assert.strictEqual(hit, 'http://127.0.0.1:8188/system_stats');
    });
  });

  describe('default export surface', () => {
    it('exposes the full API', () => {
      ['compileManifest', 'queueManifest', 'screenContent', 'checkComfyUiHealth'].forEach((key) => {
        assert.strictEqual(typeof adapter[key], 'function');
      });
    });
  });
});
