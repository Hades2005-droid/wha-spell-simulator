import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "phase2_recursive_spell.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=str(ROOT),
    )


class Phase2RecursiveSpellTests(unittest.TestCase):
    def test_evolve_one_cycle_improves(self):
        proc = _run("evolve", "--cycles", "1")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        # stdout is JSON; stderr has wrote lines
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["schema"], "shadow_garden.phase2_recursive_spell.v1")
        self.assertEqual(payload["phase"], 2)
        self.assertTrue(payload["phase2_engine"]["ok"])
        self.assertTrue(payload["improved"])
        self.assertGreaterEqual(payload["metric"]["ready_count"], 4)
        self.assertEqual(len(payload["spells"]), 5)
        self.assertLessEqual(payload["cycles_ran"], 3)
        self.assertFalse(payload["controls"]["infinite_loop"])
        top = payload["spells"][0]
        self.assertGreaterEqual(top["quality"], 0.55)
        self.assertIn("agi_task_ref", payload)

    def test_rejects_over_max_cycles(self):
        proc = _run("evolve", "--cycles", "9")
        self.assertEqual(proc.returncode, 2)


if __name__ == "__main__":
    unittest.main()
