import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "deepseek_asuna_point0_unify.py"
BRIDGE = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "deepseek_asuna_point0_unification.json"
)


class DeepSeekAsunaPoint0UnifyTests(unittest.TestCase):
    def test_write_unifies_deepseek_to_point0(self):
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
        self.assertEqual(
            doc["schema"], "shadow_garden.deepseek_asuna_point0_unification.v1"
        )
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["unification_target"]["name"], "perplexity_asuna_point_0")
        self.assertEqual(doc["asuna_point0"]["point_0"], "HOME")
        self.assertEqual(
            doc["asuna_point0"]["resident_archetype"], "angela_asuna_home"
        )
        self.assertEqual(doc["carrier"], "love_and_harmony_6")
        self.assertEqual(doc["bridge_signature"], "f2e596cd043d6819")
        self.assertGreaterEqual(doc["metrics"]["vector_count"], 5)
        self.assertGreaterEqual(doc["metrics"]["chat_pointer_existing"], 3)
        self.assertEqual(doc["metrics"]["provider_calls"], 0)
        self.assertEqual(doc["metrics"]["remote_deepseek_calls"], 0)
        self.assertFalse(doc["controls"]["remote_deepseek_api"])
        self.assertFalse(doc["controls"]["bulk_chat_copy"])
        self.assertFalse(doc["controls"]["credential_access"])
        self.assertTrue(doc["controls"]["source_pointers_only"])
        self.assertTrue(doc["controls"]["local_ollama_preferred"])
        self.assertEqual(doc["api_surface"]["mode"], "env_names_only")
        self.assertIn("DEEPSEEK_API_KEY", doc["api_surface"]["env_names"])
        self.assertIn("OLLAMA_HOST", doc["api_surface"]["env_names"])
        # No secret-looking substrings in artifact.
        dumped = json.dumps(doc)
        self.assertNotIn("sk-", dumped)
        self.assertNotIn("Bearer ", dumped)
        # Weight pointers never claim blob read.
        for ptr in doc.get("weight_pointers") or []:
            self.assertFalse(ptr.get("blob_contents_read", True))
        for ptr in doc.get("chat_memory_pointers") or []:
            self.assertFalse(ptr.get("bulk_copy", True))
            self.assertFalse(ptr.get("content_inlined", True))

    def test_self_test_command(self):
        proc = subprocess.run(
            [sys.executable, str(TOOL), "self-test"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])


if __name__ == "__main__":
    unittest.main()
