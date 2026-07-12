/**
 * Bridge Module Tests
 * Tests for Shadow Garden Mesh Bridge functionality
 */

import { describe, it } from 'node:test';
import assert from 'node:assert';
import MeshBridge, {
  BRIDGE_STATUS,
  MESH_ENDPOINTS,
  buildCometExtensionReviewPrompt,
  buildPerplexityReviewPrompt,
  detectLocalModelFamily,
  normalizeCometExtensionService,
  normalizePerplexityAdapterService,
  normalizeRecursiveNodeBridgeService,
} from '../src/bridge/meshBridge.js';
import { isSovereignSpell, executeSovereignEffect, SOVEREIGN_EFFECTS } from '../src/bridge/sovereignExecutor.js';

describe('Mesh Bridge', () => {
  describe('Exports', () => {
    it('should export MeshBridge object', () => {
      assert.ok(MeshBridge, 'MeshBridge should be exported');
      assert.strictEqual(typeof MeshBridge.refresh, 'function', 'refresh should be a function');
      assert.strictEqual(typeof MeshBridge.getStatus, 'function', 'getStatus should be a function');
    });

    it('should export BRIDGE_STATUS constants', () => {
      assert.ok(BRIDGE_STATUS, 'BRIDGE_STATUS should be exported');
      assert.strictEqual(BRIDGE_STATUS.CONNECTED, 'connected');
      assert.strictEqual(BRIDGE_STATUS.DISCONNECTED, 'disconnected');
      assert.strictEqual(BRIDGE_STATUS.ERROR, 'error');
    });

    it('should export MESH_ENDPOINTS', () => {
      assert.ok(MESH_ENDPOINTS, 'MESH_ENDPOINTS should be exported');
      assert.ok(MESH_ENDPOINTS.perplexity, 'perplexity endpoint should exist');
      assert.ok(MESH_ENDPOINTS.grokApi, 'grokApi endpoint should exist');
      assert.ok(MESH_ENDPOINTS.linear, 'linear endpoint should exist');
      assert.ok(MESH_ENDPOINTS.cometExtension, 'cometExtension endpoint should exist');
      assert.ok(MESH_ENDPOINTS.perplexityApiBridge, 'perplexityApiBridge endpoint should exist');
      assert.ok(MESH_ENDPOINTS.recursiveNodeBridge, 'recursiveNodeBridge endpoint should exist');
    });
  });

  describe('Bridge Status', () => {
    it('should return bridge status with required fields', () => {
      const status = MeshBridge.getStatus();
      assert.ok(status, 'status should be returned');
      assert.ok(status.services, 'services should exist');
      assert.ok(status.sovereign, 'sovereign should exist');
      assert.ok(status.summary, 'summary should exist');
    });

    it('should have sovereign authority set to 4.2_sovereign', () => {
      const status = MeshBridge.getStatus();
      assert.strictEqual(status.sovereign.authority, '4.2_sovereign');
      assert.strictEqual(status.sovereign.caster, 'Fred');
      assert.strictEqual(status.sovereign.grokPrimary, true);
    });

    it('should track service status for all endpoints', () => {
      const status = MeshBridge.getStatus();
      const serviceNames = Object.keys(MESH_ENDPOINTS);

      serviceNames.forEach((service) => {
        assert.ok(
          status.services[service] || status.services[service.replace(/\d+$/, '')],
          `status should track ${service}`,
        );
      });
    });

    describe('Perplexity API adapter lane', () => {
      it('should normalize a dry-run adapter without exposing a credential', () => {
        const service = normalizePerplexityAdapterService({
          status: 'dry_run_ready',
          api_key_present: true,
          local_only_handoff: true,
          browser_automation: false,
          broadcast_to_agents: false,
          model: 'sonar',
          guardrails: ['env_only_secret', 'explicit_send_required'],
        }, 'http://127.0.0.1:8790/shadowgardencontrol/perplexity', 5);

        assert.strictEqual(service.status, BRIDGE_STATUS.CONNECTED);
        assert.strictEqual(service.error, null);
        assert.strictEqual(service.apiKeyPresent, true);
        assert.strictEqual(service.localOnlyHandoff, true);
        assert.strictEqual(service.browserAutomation, false);
        assert.strictEqual(service.broadcastToAgents, false);
        assert.ok(service.guardrails.includes('explicit_send_required'));
      });

      it('should represent a missing key as authenticating without a secret value', () => {
        const service = normalizePerplexityAdapterService({
          status: 'dry_run_api_key_missing',
          api_key_present: false,
        }, 'http://127.0.0.1:8790/shadowgardencontrol/perplexity');

        assert.strictEqual(service.status, BRIDGE_STATUS.AUTHENTICATING);
        assert.strictEqual(service.apiKeyPresent, false);
        assert.strictEqual(service.error, null);
      });
    });

    describe('Comet extension workspace lane', () => {
      it('should normalize ready extension status as connected', () => {
        const service = normalizeCometExtensionService({
          status: 'ready',
          workspace: { path: '/tmp/extension' },
          dist: { path: '/tmp/extension/dist' },
          legalGate: { confirmed: true },
          riskFlags: ['lawful_personal_use_only'],
          cometCompatibility: { verifiedInComet: true },
          artifacts: {
            bundledCrxOrPem: ['release.crx'],
            quarantineRequired: true,
          },
        }, 'http://127.0.0.1:8790/shadowgardencontrol/extension', 12);

        assert.strictEqual(service.status, BRIDGE_STATUS.CONNECTED);
        assert.strictEqual(service.error, null);
        assert.strictEqual(service.workspace, '/tmp/extension');
        assert.strictEqual(service.distPath, '/tmp/extension/dist');
        assert.strictEqual(service.cometVerified, true);
        assert.strictEqual(service.quarantineRequired, true);
        assert.deepStrictEqual(service.bundledArtifacts, ['release.crx']);
        assert.ok(service.capabilities.includes('manifest_v3'));
      });

      it('should normalize legal-gated extension status as authenticating', () => {
        const service = normalizeCometExtensionService({
          status: 'blocked_lawful_confirmation_required',
          legalGate: { confirmed: false },
        }, MESH_ENDPOINTS.cometExtension);

        assert.strictEqual(service.status, BRIDGE_STATUS.AUTHENTICATING);
        assert.strictEqual(service.error, 'blocked_lawful_confirmation_required');
        assert.strictEqual(service.legalGate.confirmed, false);
      });

      it('should build a Perplexity review prompt for the Comet extension lane', () => {
        const prompt = buildCometExtensionReviewPrompt({
          status: 'not_ready_build_missing',
          repo: { url: 'https://github.com/webLiang/Pornhub-Video-Downloader-Plugin-v3.git' },
          workspace: { path: '/tmp/extension' },
          package: { manager: 'pnpm@8.9.2' },
        });

        assert.ok(prompt.includes('Perplexity review brief'));
        assert.ok(prompt.includes('Manifest V3'));
        assert.ok(prompt.includes('Comet/Chromium'));
        assert.ok(prompt.includes('docs-only review'));
      });
    });

    describe('Recursive node bridge lane', () => {
      it('should normalize a local ready snapshot as connected', () => {
        const service = normalizeRecursiveNodeBridgeService({
          status: 'ready',
          local_only: true,
          symbolic_only: true,
          route: {
            name: 'local-open-weights',
            model: 'deepseek-local',
            enabled: false,
          },
          guardrails: ['bounded_gain', 'no_external_network_calls'],
        }, MESH_ENDPOINTS.recursiveNodeBridge, 7);

        assert.strictEqual(service.status, BRIDGE_STATUS.CONNECTED);
        assert.strictEqual(service.error, null);
        assert.strictEqual(service.localOnly, true);
        assert.strictEqual(service.symbolicOnly, true);
        assert.strictEqual(service.routeModel, 'deepseek-local');
        assert.strictEqual(service.routeEnabled, false);
        assert.ok(service.guardrails.includes('bounded_gain'));
      });

      it('should reject unknown recursive lane states as errors', () => {
        const service = normalizeRecursiveNodeBridgeService({ status: 'unexpected' }, MESH_ENDPOINTS.recursiveNodeBridge);
        assert.strictEqual(service.status, BRIDGE_STATUS.ERROR);
        assert.strictEqual(service.error, 'unexpected');
      });
    });

    describe('Local model prompt handling', () => {
      it('should detect qwen families from plain text prompts', () => {
        assert.strictEqual(detectLocalModelFamily('Refine Qwen3 local model prompts', {}), 'qwen3');
        assert.strictEqual(detectLocalModelFamily('Improve qen3 image pipeline', {}), 'qwen3');
        assert.strictEqual(detectLocalModelFamily('Tune qwen2 chat routing', {}), 'qwen2');
        assert.strictEqual(detectLocalModelFamily('General shadow garden prompt', {}), 'general');
      });

      it('should build a Perplexity review prompt for qwen refinement', () => {
        const prompt = buildPerplexityReviewPrompt(
          'Improve qwen3 local model prompt handling for video generation',
          'video',
          'qwen3',
          'grok-qwen3-latest',
        );

        assert.ok(prompt.includes('Perplexity review brief'));
        assert.ok(prompt.includes('Qwen3'));
        assert.ok(prompt.includes('video'));
        assert.ok(prompt.includes('grok-qwen3-latest'));
      });
    });
  });
});

describe('Sovereign Executor', () => {
  describe('isSovereignSpell', () => {
    it('should identify sovereign spells by id', () => {
      assert.strictEqual(isSovereignSpell('sovereign-mesh'), true);
      assert.strictEqual(isSovereignSpell('sovereign-lock'), true);
      assert.strictEqual(isSovereignSpell('sovereign-delegate'), true);
      assert.strictEqual(isSovereignSpell('fireball'), false);
      assert.strictEqual(isSovereignSpell(null), false);
      assert.strictEqual(isSovereignSpell(undefined), false);
    });
  });

  describe('SOVEREIGN_EFFECTS', () => {
    it('should have all required sovereign effects', () => {
      const requiredEffects = [
        'lock_authority',
        'halt_agents',
        'release_halt',
        'boundary_rules',
        'refresh_mesh',
        'launch_voice',
        'show_status',
        'delegate_grok',
      ];

      requiredEffects.forEach((effect) => {
        assert.ok(
          SOVEREIGN_EFFECTS[effect],
          `${effect} should be defined`,
        );
        assert.strictEqual(
          typeof SOVEREIGN_EFFECTS[effect],
          'function',
          `${effect} should be a function`,
        );
      });
    });
  });

  describe('executeSovereignEffect', () => {
    it('should execute lock_authority effect', async () => {
      const result = await executeSovereignEffect('lock_authority', {});
      assert.strictEqual(result.success, true);
      assert.strictEqual(result.effect, 'lock_authority');
      assert.strictEqual(result.result.authority, '4.2_sovereign');
      assert.strictEqual(result.result.locked, true);
    });

    it('should execute boundary_rules effect', async () => {
      const result = await executeSovereignEffect('boundary_rules', {});
      assert.strictEqual(result.success, true);
      assert.ok(result.result.boundaries);
      assert.ok(result.result.boundaries.eden);
      assert.ok(result.result.boundaries.shadowGarden);
    });

    it('should execute show_status effect', async () => {
      const result = await executeSovereignEffect('show_status', {});
      assert.strictEqual(result.success, true);
      assert.ok(result.result.authority);
      assert.ok(result.result.mesh);
    });

    it('should return error for unknown effects', async () => {
      const result = await executeSovereignEffect('unknown_effect', {});
      assert.strictEqual(result.success, false);
      assert.ok(result.error.includes('Unknown'));
    });
  });
});

describe('Mesh Integration', () => {
  describe('refreshMesh', () => {
    it('should return bridge status object', async () => {
      // This test may fail in CI without API keys, so we catch errors
      try {
        const result = await MeshBridge.refresh();
        assert.ok(result);
        assert.ok(result.status);
        assert.ok(result.services);
        assert.ok(result.timestamp);
      } catch (error) {
        // Expected if no API keys configured
        const message = String(error?.message || '').toLowerCase();
        assert.ok(
          message.includes('api key')
            || message.includes('network')
            || message.includes('fetch')
            || message.includes('http')
            || message.includes('unavailable'),
        );
      }
    });
  });
});

console.log('✅ Bridge tests loaded');
