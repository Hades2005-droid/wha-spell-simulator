import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.elevenlabs_garden_bridge import build_manifest


class ElevenLabsGardenBridgeTests(unittest.TestCase):
    def test_indexes_native_nodes_and_workflow_metadata(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            extension = root / "comfy_api_nodes"
            apis = extension / "apis"
            apis.mkdir(parents=True)
            (extension / "nodes_elevenlabs.py").write_text(
                "native node metadata", encoding="utf-8"
            )
            (apis / "elevenlabs.py").write_text("native api metadata", encoding="utf-8")
            workflow = root / "workflow.json"
            workflow.write_text(
                json.dumps(
                    {
                        "nodes": [
                            {"type": "KSampler"},
                            {"class_type": "ElevenLabsTextToSpeech"},
                            {"class_type": "ElevenLabsTextToDialogue"},
                        ]
                    }
                ),
                encoding="utf-8",
            )

            manifest = build_manifest(comfyui_root=root, workflow=workflow)

        self.assertTrue(manifest["comfyui"]["native_extension"]["exists"])
        self.assertTrue(manifest["comfyui"]["api_contract"]["exists"])
        self.assertEqual(manifest["workflow"]["node_count"], 3)
        self.assertEqual(
            manifest["workflow"]["elevenlabs_nodes"],
            ["ElevenLabsTextToDialogue", "ElevenLabsTextToSpeech"],
        )
        self.assertEqual(len(manifest["comfyui"]["api_contract"]["endpoints"]), 7)
        self.assertTrue(manifest["controls"]["local_only"])
        self.assertFalse(manifest["controls"]["provider_calls"])

    def test_reports_key_presence_without_emitting_secret(self):
        secret = "elevenlabs-test-secret"
        with tempfile.TemporaryDirectory() as directory, patch.dict(
            os.environ, {"ELEVENLABS_API_KEY": secret}
        ):
            manifest = build_manifest(
                comfyui_root=Path(directory),
                workflow=Path(directory) / "missing-workflow.json",
            )

        rendered = json.dumps(manifest)
        self.assertTrue(manifest["credentials"]["present"])
        self.assertFalse(manifest["credentials"]["value_emitted"])
        self.assertNotIn(secret, rendered)

    def test_missing_installation_is_non_mutating_status(self):
        with tempfile.TemporaryDirectory() as directory:
            manifest = build_manifest(
                comfyui_root=Path(directory),
                workflow=Path(directory) / "missing-workflow.json",
            )

        self.assertFalse(manifest["comfyui"]["native_extension"]["exists"])
        self.assertFalse(manifest["comfyui"]["api_contract"]["exists"])
        self.assertFalse(manifest["workflow"]["exists"])
        self.assertEqual(manifest["mode"], "manifest_only")
        self.assertFalse(manifest["controls"]["comfy_prompt_submission"])


if __name__ == "__main__":
    unittest.main()
