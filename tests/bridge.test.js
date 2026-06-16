/**
 * Bridge Module Tests
 * Tests for Shadow Garden Mesh Bridge functionality
 */

import { describe, it } from "node:test";
import assert from "node:assert";
import MeshBridge, { BRIDGE_STATUS, MESH_ENDPOINTS } from "../src/bridge/meshBridge.js";
import { isSovereignSpell, executeSovereignEffect, SOVEREIGN_EFFECTS } from "../src/bridge/sovereignExecutor.js";

describe("Mesh Bridge", () => {
  describe("Exports", () => {
    it("should export MeshBridge object", () => {
      assert.ok(MeshBridge, "MeshBridge should be exported");
      assert.strictEqual(typeof MeshBridge.refresh, "function", "refresh should be a function");
      assert.strictEqual(typeof MeshBridge.getStatus, "function", "getStatus should be a function");
    });

    it("should export BRIDGE_STATUS constants", () => {
      assert.ok(BRIDGE_STATUS, "BRIDGE_STATUS should be exported");
      assert.strictEqual(BRIDGE_STATUS.CONNECTED, "connected");
      assert.strictEqual(BRIDGE_STATUS.DISCONNECTED, "disconnected");
      assert.strictEqual(BRIDGE_STATUS.ERROR, "error");
    });

    it("should export MESH_ENDPOINTS", () => {
      assert.ok(MESH_ENDPOINTS, "MESH_ENDPOINTS should be exported");
      assert.ok(MESH_ENDPOINTS.perplexity, "perplexity endpoint should exist");
      assert.ok(MESH_ENDPOINTS.grokApi, "grokApi endpoint should exist");
      assert.ok(MESH_ENDPOINTS.linear, "linear endpoint should exist");
    });
  });

  describe("Bridge Status", () => {
    it("should return bridge status with required fields", () => {
      const status = MeshBridge.getStatus();
      assert.ok(status, "status should be returned");
      assert.ok(status.services, "services should exist");
      assert.ok(status.sovereign, "sovereign should exist");
      assert.ok(status.summary, "summary should exist");
    });

    it("should have sovereign authority set to 4.2_sovereign", () => {
      const status = MeshBridge.getStatus();
      assert.strictEqual(status.sovereign.authority, "4.2_sovereign");
      assert.strictEqual(status.sovereign.caster, "Fred");
      assert.strictEqual(status.sovereign.grokPrimary, true);
    });

    it("should track service status for all endpoints", () => {
      const status = MeshBridge.getStatus();
      const serviceNames = Object.keys(MESH_ENDPOINTS);

      serviceNames.forEach(service => {
        assert.ok(
          status.services[service] || status.services[service.replace(/\d+$/, "")],
          `status should track ${service}`
        );
      });
    });
  });
});

describe("Sovereign Executor", () => {
  describe("isSovereignSpell", () => {
    it("should identify sovereign spells by id", () => {
      assert.strictEqual(isSovereignSpell("sovereign-mesh"), true);
      assert.strictEqual(isSovereignSpell("sovereign-lock"), true);
      assert.strictEqual(isSovereignSpell("sovereign-delegate"), true);
      assert.strictEqual(isSovereignSpell("fireball"), false);
      assert.strictEqual(isSovereignSpell(null), false);
      assert.strictEqual(isSovereignSpell(undefined), false);
    });
  });

  describe("SOVEREIGN_EFFECTS", () => {
    it("should have all required sovereign effects", () => {
      const requiredEffects = [
        "lock_authority",
        "halt_agents",
        "release_halt",
        "boundary_rules",
        "refresh_mesh",
        "launch_voice",
        "show_status",
        "delegate_grok"
      ];

      requiredEffects.forEach(effect => {
        assert.ok(
          SOVEREIGN_EFFECTS[effect],
          `${effect} should be defined`
        );
        assert.strictEqual(
          typeof SOVEREIGN_EFFECTS[effect],
          "function",
          `${effect} should be a function`
        );
      });
    });
  });

  describe("executeSovereignEffect", () => {
    it("should execute lock_authority effect", async () => {
      const result = await executeSovereignEffect("lock_authority", {});
      assert.strictEqual(result.success, true);
      assert.strictEqual(result.effect, "lock_authority");
      assert.strictEqual(result.result.authority, "4.2_sovereign");
      assert.strictEqual(result.result.locked, true);
    });

    it("should execute boundary_rules effect", async () => {
      const result = await executeSovereignEffect("boundary_rules", {});
      assert.strictEqual(result.success, true);
      assert.ok(result.result.boundaries);
      assert.ok(result.result.boundaries.eden);
      assert.ok(result.result.boundaries.shadowGarden);
    });

    it("should execute show_status effect", async () => {
      const result = await executeSovereignEffect("show_status", {});
      assert.strictEqual(result.success, true);
      assert.ok(result.result.authority);
      assert.ok(result.result.mesh);
    });

    it("should return error for unknown effects", async () => {
      const result = await executeSovereignEffect("unknown_effect", {});
      assert.strictEqual(result.success, false);
      assert.ok(result.error.includes("Unknown"));
    });
  });
});

describe("Mesh Integration", () => {
  describe("refreshMesh", () => {
    it("should return bridge status object", async () => {
      // This test may fail in CI without API keys, so we catch errors
      try {
        const result = await MeshBridge.refresh();
        assert.ok(result);
        assert.ok(result.status);
        assert.ok(result.services);
        assert.ok(result.timestamp);
      } catch (error) {
        // Expected if no API keys configured
        assert.ok(error.message.includes("API key") || error.message.includes("network"));
      }
    });
  });
});

console.log("✅ Bridge tests loaded");
