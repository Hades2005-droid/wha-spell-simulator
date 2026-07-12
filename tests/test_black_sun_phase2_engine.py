import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENGINE = ROOT / "tools" / "black_sun_phase2_engine.py"
MON = Path.home() / "shadow_garden_may30_monitoring"
SOUTH = MON / "shaoshi_bridge" / "south_star"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ENGINE), *args],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


@unittest.skipUnless(SOUTH.is_dir(), "shadow_garden_may30_monitoring not present")
class BlackSunPhase2EngineTests(unittest.TestCase):
    def test_self_test_passes(self):
        proc = _run("self-test")
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        payload = json.loads(proc.stdout)
        self.assertTrue(payload["ok"], payload)
        self.assertGreaterEqual(payload["passed"], 8)

    def test_manifest_invariants(self):
        proc = _run("manifest")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        manifest = json.loads(proc.stdout)
        self.assertEqual(manifest["phase"], 2)
        self.assertEqual(
            manifest["q24_canonical_id"],
            "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1",
        )
        self.assertTrue(manifest["symbolic_only"])
        self.assertEqual(manifest["home_black_sun"]["justice_toggle"]["q24_anchor"], 14)

    def test_adapter_launch_to_glide(self):
        proc = _run("apply", "--action", "launch")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        result = json.loads(proc.stdout)
        self.assertTrue(result["ok"])
        self.assertEqual(result["next_state"], "glide")

    def test_json_replay_moon_18(self):
        proc = subprocess.run(
            [sys.executable, str(ENGINE), "json"],
            input=json.dumps(
                {
                    "command": "replay",
                    "actions": ["launch", "fable", "harmony", "chariot", "land"],
                    "seed": 42,
                    "mastery": 10,
                }
            ),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr)
        report = json.loads(proc.stdout)
        self.assertTrue(report["state"]["moon_18"]["gate_open"])
        self.assertEqual(report["state"]["phase"], "complete")


if __name__ == "__main__":
    unittest.main()
