"""Tests for the Phase 3 Persephone shutdown bridge artifact."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "phase3_persephone_shutdown_bridge.json"
)


class Phase3PersephoneShutdownBridgeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = json.loads(BRIDGE.read_text(encoding="utf-8"))

    def test_bridge_file_exists(self):
        self.assertTrue(BRIDGE.is_file())

    def test_schema_and_phase3_seal_fields(self):
        self.assertEqual(
            self.doc["schema"],
            "shadow_garden.phase3_persephone_shutdown_bridge.v1",
        )
        self.assertEqual(self.doc["phase"], 3)
        self.assertEqual(self.doc["seal"], "dimension_0_shutdown")
        self.assertTrue(self.doc["polarity"]["yin_polarity"])
        self.assertEqual(self.doc["polarity"]["yang_anchor"], "sovereign-black-sun")
        self.assertEqual(self.doc["polarity"]["paired_with"], "sovereign-white-moon-gate")

    def test_discord_is_env_only_and_not_live(self):
        discord = self.doc["discord"]
        self.assertEqual(discord["discord_application_id_env"], "DISCORD_APPLICATION_ID")
        self.assertFalse(discord["live_discord"])
        self.assertEqual(discord["execution_mode"], "manifest_only")
        blob = json.dumps(self.doc)
        self.assertNotIn("1528529880227123421", blob)

    def test_gate10_and_controls_block_external_writes(self):
        self.assertEqual(self.doc["gate10"]["policy"], "no_external_writes")
        self.assertFalse(self.doc["live_discord"])
        self.assertEqual(self.doc["execution_mode"], "manifest_only")
        self.assertFalse(self.doc["controls"]["external_writes"])
        self.assertFalse(self.doc["controls"]["secrets_in_artifacts"])

    def test_persephone_throne_is_sealed(self):
        catalyst = self.doc["catalyst"]
        self.assertEqual(catalyst["section"], 11)
        self.assertEqual(catalyst["name"], "Persephone Throne")
        self.assertEqual(catalyst["throne_state"], "sealed")


if __name__ == "__main__":
    unittest.main()
