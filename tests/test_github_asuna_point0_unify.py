import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "github_asuna_point0_unify.py"
BRIDGE = (
    ROOT / "shadow_garden_handoff" / "bridges" / "github_asuna_point0_unification.json"
)
SCENE = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "shadow_garden_lainie_julia_scene_manifest.json"
)
CATALYST3 = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "catalyst3_persona_telemetry_launch_finalization.json"
)


class GitHubAsunaPoint0UnifyTests(unittest.TestCase):
    def test_write_unifies_profile_to_point0(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "write"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])
        self.assertTrue(BRIDGE.is_file())
        doc = json.loads(BRIDGE.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], "shadow_garden.github_asuna_point0_unification.v1")
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["unification_target"]["name"], "perplexity_asuna_point_0")
        self.assertEqual(doc["asuna_point0"]["point_0"], "HOME")
        self.assertEqual(
            doc["asuna_point0"]["resident_archetype"], "angela_asuna_home"
        )
        self.assertGreaterEqual(doc["metrics"]["vector_count"], 3)
        self.assertGreaterEqual(doc["metrics"]["local_path_count"], 3)
        self.assertFalse(doc["controls"]["bulk_clone"])
        self.assertFalse(doc["controls"]["external_fetch"])
        self.assertFalse(doc["controls"]["credential_access"])
        self.assertEqual(doc["metrics"]["provider_calls"], 0)
        self.assertTrue(doc["controls"]["source_pointers_only"])
        self.assertEqual(doc["github_profile"]["mode"], "pointer_only")
        self.assertFalse(doc["github_profile"]["fetched"])
        ids = {v["id"] for v in doc["vectors"]}
        self.assertIn("wha-spell-simulator", ids)
        self.assertTrue(all("private" not in vector for vector in doc["vectors"]))

    def test_scene_and_catalyst3_remain_manifest_only(self):
        scene = json.loads(SCENE.read_text(encoding="utf-8"))
        catalyst = json.loads(CATALYST3.read_text(encoding="utf-8"))
        self.assertFalse(scene["scene"]["render_queued"])
        self.assertTrue(scene["approval_gates"]["human_approval_before_render"])
        self.assertFalse(scene["approval_gates"]["provider_calls"])
        self.assertEqual(scene["loopback_hosts"]["comfyui"], "http://127.0.0.1:8189")
        providers = catalyst["terminal_auto_backport_capabilities"]
        self.assertEqual(len(providers), 5)
        self.assertTrue(
            all(not item["enabled"] and item["mode"] == "pointer_only" for item in providers)
        )
        self.assertFalse(catalyst["controls"]["provider_calls"])


if __name__ == "__main__":
    unittest.main()
