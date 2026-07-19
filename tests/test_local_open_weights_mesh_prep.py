import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREP = ROOT / "tools" / "local_open_weights_mesh_prep.py"
BRIDGE = (
    ROOT / "shadow_garden_handoff" / "bridges" / "local_open_weights_mesh_prep.json"
)
CHECKLIST = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "local_open_weights_mesh_checklist.md"
)


class LocalOpenWeightsMeshPrepTests(unittest.TestCase):
    def test_self_test(self):
        proc = subprocess.run(
            [sys.executable, str(PREP), "self-test"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])

    def test_write_prep_ledger(self):
        proc = subprocess.run(
            [sys.executable, str(PREP), "write", "--no-refresh", "--no-packet"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:800])
        self.assertTrue(BRIDGE.is_file())
        self.assertTrue(CHECKLIST.is_file())
        doc = json.loads(BRIDGE.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], "shadow_garden.local_open_weights_mesh_prep.v1")
        self.assertEqual(doc["mesh_id"], "local_open_weights_mesh")
        self.assertTrue(doc["ok"])
        self.assertFalse(doc["controls"]["provider_calls"])
        self.assertTrue(doc["controls"]["local_bind_only"])
        self.assertTrue(
            doc["controls"]["final_cutover_requires_KIMI3_TRANSITION_ARMED"]
        )
        self.assertIn("fable5", (doc.get("ports") or {}).get("ports") or {})
        self.assertIn("ollama", (doc.get("ports") or {}).get("ports") or {})
        self.assertGreaterEqual(len(doc.get("checklist") or []), 8)
        self.assertIn("Operator cutover", CHECKLIST.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
