"""Tests for the deterministic MCP router policy engine."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from mcp_router_policy import (  # noqa: E402
    load_registry,
    validate_registry,
    select_route,
    ledger_entry,
)


class RegistryValidationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()

    def test_shipped_registry_is_valid(self):
        self.assertEqual(validate_registry(self.registry), [])

    def test_write_lanes_require_approval(self):
        lanes = self.registry["policy"]["lanes"]
        self.assertTrue(lanes["draft_write"]["requires_approval"])
        self.assertTrue(lanes["confirmed_write"]["requires_approval"])
        self.assertFalse(lanes["read_only"]["requires_approval"])

    def test_github_and_slack_are_wired(self):
        ids = {s["id"] for s in self.registry["servers"]}
        self.assertIn("github", ids)
        self.assertIn("slack", ids)

    def test_env_vars_are_names_only(self):
        broken = dict(self.registry)
        broken["servers"] = [dict(self.registry["servers"][0])]
        broken["servers"][0]["env_vars"] = ["GITHUB_TOKEN=ghp_notreallyasecret"]
        issues = validate_registry(broken)
        self.assertTrue(any("names only" in issue for issue in issues))

    def test_default_lane_must_be_allowed(self):
        broken = dict(self.registry)
        broken["servers"] = [dict(self.registry["servers"][0])]
        broken["servers"][0]["default_lane"] = "confirmed_write"
        broken["servers"][0]["allowed_lanes"] = ["read_only"]
        issues = validate_registry(broken)
        self.assertTrue(any("default_lane" in issue for issue in issues))


class RoutingTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.registry = load_registry()

    def test_read_only_route_auto_approved(self):
        decision = select_route(self.registry, "source_control")
        self.assertTrue(decision["allowed"])
        self.assertFalse(decision["requires_approval"])
        self.assertEqual(decision["targets"], ["github"])
        self.assertEqual(decision["lane"], "read_only")

    def test_write_route_blocked_without_approval(self):
        decision = select_route(self.registry, "messaging", lane="confirmed_write")
        self.assertFalse(decision["allowed"])
        self.assertTrue(decision["requires_approval"])
        self.assertIn("approval required", decision["reason"])

    def test_write_route_allowed_with_exact_approval(self):
        decision = select_route(
            self.registry, "messaging", lane="confirmed_write",
            approval={"server": "slack", "lane": "confirmed_write"},
        )
        self.assertTrue(decision["allowed"])

    def test_qdrant_write_needs_exact_collection_scope(self):
        blocked = select_route(
            self.registry, "vector_memory", lane="confirmed_write",
            approval={"server": "qdrant", "lane": "confirmed_write"},
        )
        self.assertFalse(blocked["allowed"])
        self.assertIn("collection scope", blocked["reason"])

        allowed = select_route(
            self.registry, "vector_memory", lane="confirmed_write",
            approval={"server": "qdrant", "lane": "confirmed_write", "scope": "fable5_notes"},
        )
        self.assertTrue(allowed["allowed"])

    def test_unknown_domain_is_denied(self):
        decision = select_route(self.registry, "not_a_domain")
        self.assertFalse(decision["allowed"])

    def test_lane_not_allowed_for_server_is_denied(self):
        # harpa is read_only-only
        decision = select_route(self.registry, "browser_assistant", lane="confirmed_write")
        self.assertFalse(decision["allowed"])

    def test_ledger_entry_has_required_fields(self):
        entry = ledger_entry(select_route(self.registry, "source_control"))
        required = load_registry()["policy"]["ledger_required_fields"]
        for field in required:
            self.assertIn(field, entry)


if __name__ == "__main__":
    unittest.main()
