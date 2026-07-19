import unittest

from tools.claude_shadowgarden import build_command_plan, build_route_hints


class ClaudeShadowGardenExtensionPlanTests(unittest.TestCase):
    def test_plan_includes_gated_extension_review_context(self):
        workspace = "/tmp/comet-extension"
        plan = build_command_plan(
            "Review Manifest V3 compatibility",
            "auto",
            {"extension_workspace": workspace},
        )
        self.assertEqual(plan["extension_workspace"], workspace)
        command_by_id = {command["id"]: command for command in plan["commands"]}
        self.assertIn("configure_extension_context", command_by_id)
        self.assertTrue(command_by_id["configure_extension_context"]["requires_live"])
        self.assertIn("inspect_extension_status", command_by_id)
        self.assertFalse(command_by_id["inspect_extension_status"]["requires_live"])
        self.assertIn("lawful personal-use only", plan["context_prompt"])
        self.assertIn("clone/install/build actions explicit and gated", plan["context_prompt"])

    def test_route_hints_include_docs_only_review_lanes(self):
        hints = build_route_hints("auto", "dry_run", {})
        lanes = {route["lane"] for route in hints["suggested_routes"]}
        self.assertIn("perplexity", lanes)
        self.assertIn("comet_extension", lanes)


if __name__ == "__main__":
    unittest.main()
