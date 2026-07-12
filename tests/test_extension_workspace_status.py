import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.extension_workspace_status import build_status, main


class ExtensionWorkspaceStatusTests(unittest.TestCase):
    def make_args(self, workspace: Path, lawful_confirmed: bool = True):
        return SimpleNamespace(
            workspace=str(workspace),
            lawful_confirmed=lawful_confirmed,
            review_prompt_file=str(workspace.parent / "review.md"),
        )

    def write_json(self, path: Path, payload):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")

    def test_requires_lawful_confirmation_before_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "extension"
            with patch.dict(os.environ, {}, clear=True):
                status = build_status(self.make_args(workspace, lawful_confirmed=False))
        self.assertEqual(status["status"], "blocked_lawful_confirmation_required")
        self.assertFalse(status["legalGate"]["confirmed"])

    def test_reports_missing_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "extension"
            status = build_status(self.make_args(workspace))
        self.assertEqual(status["status"], "not_ready_workspace_missing")
        self.assertFalse(status["workspace"]["exists"])

    def test_reports_missing_package_json(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "extension"
            workspace.mkdir()
            status = build_status(self.make_args(workspace))
        self.assertEqual(status["status"], "not_ready_package_json_missing")
        self.assertFalse(status["package"]["present"])

    def test_reports_missing_build(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "extension"
            self.write_json(
                workspace / "package.json",
                {
                    "name": "pornhub-video-downloader-plugin-v3",
                    "packageManager": "pnpm@8.9.2",
                },
            )
            status = build_status(self.make_args(workspace))
        self.assertEqual(status["status"], "not_ready_build_missing")
        self.assertEqual(status["package"]["manager"], "pnpm@8.9.2")

    def test_requires_manifest_v3(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "extension"
            self.write_json(
                workspace / "package.json",
                {"name": "pornhub-video-downloader-plugin-v3"},
            )
            self.write_json(workspace / "dist" / "manifest.json", {"manifest_version": 2})
            status = build_status(self.make_args(workspace))
        self.assertEqual(status["status"], "not_ready_manifest_v3_required")
        self.assertIn("manifest_version_3_required", status["riskFlags"])

    def test_reports_ready_manifest_and_permission_risks(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Path(directory) / "extension"
            self.write_json(
                workspace / "package.json",
                {
                    "name": "pornhub-video-downloader-plugin-v3",
                    "packageManager": "pnpm@8.9.2",
                    "scripts": {"build": "vite build", "build:crx": "vite build"},
                },
            )
            self.write_json(
                workspace / "dist" / "manifest.json",
                {
                    "manifest_version": 3,
                    "permissions": ["downloads", "declarativeNetRequest"],
                    "host_permissions": ["<all_urls>"],
                },
            )
            (workspace / "release.crx").write_bytes(b"untrusted")
            status = build_status(self.make_args(workspace))
        self.assertEqual(status["status"], "ready")
        self.assertTrue(status["cometCompatibility"]["manifestV3"])
        self.assertTrue(status["cometCompatibility"]["manualLoadRequired"])
        self.assertFalse(status["cometCompatibility"]["verifiedInComet"])
        self.assertIn("downloads_permission", status["riskFlags"])
        self.assertIn("broad_host_permissions", status["riskFlags"])
        self.assertIn("bundled_crx_or_pem_quarantine_required", status["riskFlags"])
        self.assertEqual(status["artifacts"]["bundledCrxOrPem"], ["release.crx"])
        self.assertEqual(status["commands"]["install"][:3], ["pnpm", "--dir", str(workspace)])
        self.assertIn("docs-only review", status["perplexityReviewPrompt"])

    def test_main_writes_status_and_review_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            status_file = root / "status.json"
            review_file = root / "review.md"
            stdout = StringIO()
            with patch.dict(os.environ, {}, clear=True), redirect_stdout(stdout):
                result = main(
                    [
                        "--workspace",
                        str(root / "missing"),
                        "--status-file",
                        str(status_file),
                        "--review-prompt-file",
                        str(review_file),
                    ]
                )
            self.assertEqual(result, 0)
            self.assertTrue(status_file.is_file())
            self.assertTrue(review_file.is_file())
            self.assertEqual(
                json.loads(status_file.read_text(encoding="utf-8"))["status"],
                "blocked_lawful_confirmation_required",
            )
            self.assertIn("docs-only review", review_file.read_text(encoding="utf-8"))
            self.assertFalse(list(root.glob(".*.tmp")))


if __name__ == "__main__":
    unittest.main()
