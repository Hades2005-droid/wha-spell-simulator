import unittest

from tools.recursive_node_bridge import LoopConfig, RecursiveLoop


class RecursiveNodeBridgeTests(unittest.TestCase):
    def test_gain_eight_is_accepted_but_bounded(self):
        loop = RecursiveLoop(LoopConfig(node_count=9, gain=8.0, max_feed_entries=4))
        snapshot = loop.run_loop(max_cycles=3)
        self.assertEqual(snapshot["config"]["gain"], 8.0)
        self.assertLessEqual(snapshot["sovereign"]["cycle_power"], 8.0)
        self.assertLessEqual(len(snapshot["content_pool"]), 4)
        self.assertEqual(len(snapshot["matriarchs"]), 9)

    def test_loop_is_local_and_route_is_metadata_only(self):
        snapshot = RecursiveLoop().run_loop(max_cycles=1)
        self.assertTrue(snapshot["local_only"])
        self.assertTrue(snapshot["symbolic_only"])
        self.assertFalse(snapshot["route"]["enabled"])
        self.assertIn("no_external_network_calls", snapshot["guardrails"])
        self.assertIn("node_0_resonance_feed_v2", snapshot["content_pool"])

    def test_continuous_mode_requires_explicit_duration_at_cli_boundary(self):
        with self.assertRaises(ValueError):
            RecursiveLoop().run_loop(max_cycles=0)


if __name__ == "__main__":
    unittest.main()
