import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROK = ROOT / "tools" / "grok_xai_asuna_point0_unify.py"
CORNER = ROOT / "tools" / "white_moon_eastern_corner_unify.py"
GROK_BRIDGE = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "grok_xai_asuna_point0_unification.json"
)
CORNER_BRIDGE = (
    ROOT / "shadow_garden_handoff" / "bridges" / "white_moon_eastern_corner.json"
)
STRIPE_CFG = ROOT / "src" / "adapters" / "stripeConfig.js"
STRIPE_SERVER = ROOT / "tools" / "stripe_local" / "server.mjs"


class GrokXaiAsunaPoint0UnifyTests(unittest.TestCase):
    def test_write_unifies_grok_to_point0(self):
        proc = subprocess.run(
            [sys.executable, str(GROK), "write"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])
        self.assertTrue(GROK_BRIDGE.is_file())
        doc = json.loads(GROK_BRIDGE.read_text(encoding="utf-8"))
        self.assertEqual(
            doc["schema"], "shadow_garden.grok_xai_asuna_point0_unification.v1"
        )
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["corner"]["id"], "eastern_white_moon")
        self.assertEqual(doc["unification_target"]["name"], "perplexity_asuna_point_0")
        self.assertEqual(doc["asuna_point0"]["point_0"], "HOME")
        self.assertEqual(doc["carrier"], "love_and_harmony_6")
        self.assertGreaterEqual(doc["metrics"]["vector_count"], 4)
        self.assertFalse(doc["controls"]["provider_calls"])
        self.assertFalse(doc["controls"]["credential_access"])
        self.assertEqual(doc["api_surface"]["mode"], "env_names_only")
        self.assertIn("XAI_API_KEY", doc["api_surface"]["env_names"])
        dumped = json.dumps(doc)
        self.assertNotIn("Bearer ", dumped)

    def test_self_test(self):
        proc = subprocess.run(
            [sys.executable, str(GROK), "self-test"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])


class WhiteMoonEasternCornerTests(unittest.TestCase):
    def test_corner_weaves_deepseek_and_grok(self):
        proc = subprocess.run(
            [sys.executable, str(CORNER), "write"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:800])
        self.assertTrue(CORNER_BRIDGE.is_file())
        doc = json.loads(CORNER_BRIDGE.read_text(encoding="utf-8"))
        self.assertEqual(doc["schema"], "shadow_garden.white_moon_eastern_corner.v1")
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["corner"]["id"], "eastern_white_moon")
        self.assertEqual(doc["corner"]["leveraged_by"], "perplexity_asuna_point_0")
        self.assertGreaterEqual(doc["metrics"]["deepseek_vectors"], 5)
        self.assertGreaterEqual(doc["metrics"]["grok_vectors"], 4)
        self.assertTrue(doc["metrics"]["both_ok"])
        self.assertFalse(doc["controls"]["provider_calls"])


class StripeScaffoldTests(unittest.TestCase):
    def test_stripe_files_exist(self):
        self.assertTrue(STRIPE_CFG.is_file())
        self.assertTrue(STRIPE_SERVER.is_file())
        text = STRIPE_CFG.read_text(encoding="utf-8")
        self.assertIn("STRIPE_PUBLISHABLE_KEY", text)
        self.assertIn("secret_in_browser: false", text)
        server = STRIPE_SERVER.read_text(encoding="utf-8")
        self.assertIn("STRIPE_LIVE_OK", server)
        self.assertIn("dry_run", server)
        self.assertIn("127.0.0.1", server)


if __name__ == "__main__":
    unittest.main()
