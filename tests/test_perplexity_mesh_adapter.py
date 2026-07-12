import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from tools.perplexity_mesh_adapter import build_prompt, main


class PerplexityMeshAdapterTests(unittest.TestCase):
    def test_prompt_is_local_review_only(self):
        prompt = build_prompt("Review the mesh", {"recursive": {"status": "ready"}})
        self.assertIn("docs-only technical analysis", prompt)
        self.assertIn("do not control browser profiles", prompt)
        self.assertIn("Review the mesh", prompt)

    def test_dry_run_never_requires_or_sends_a_key(self):
        with tempfile.TemporaryDirectory() as directory:
            status_file = str(Path(directory) / "status.json")
            output_file = str(Path(directory) / "output.json")
            stdout = StringIO()
            with patch.dict(os.environ, {}, clear=True), redirect_stdout(stdout):
                result = main([
                    "--request",
                    "Review local status",
                    "--status-file",
                    status_file,
                    "--output-file",
                    output_file,
                ])
            self.assertEqual(result, 0)
            payload = json.loads(Path(status_file).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "dry_run_api_key_missing")
            self.assertFalse(payload["api_key_present"])
            self.assertFalse(Path(output_file).exists())
            self.assertNotIn("pplx-", stdout.getvalue())

    def test_send_without_key_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            status_file = str(Path(directory) / "status.json")
            with patch.dict(os.environ, {}, clear=True):
                result = main(["--send", "--status-file", status_file])
            self.assertEqual(result, 2)
            payload = json.loads(Path(status_file).read_text(encoding="utf-8"))
            self.assertEqual(payload["status"], "blocked_api_key_missing")


if __name__ == "__main__":
    unittest.main()
