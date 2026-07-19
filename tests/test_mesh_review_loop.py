import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from tools.mesh_review_loop import (
    CONFIRM_SEND_TOKEN,
    MAX_EXTERNAL_CYCLES,
    MAX_LOCAL_CYCLES,
    MeshReviewLoop,
    MeshReviewLoopConfig,
)


class MeshReviewLoopTests(unittest.TestCase):
    def make_loop(self, root: Path, config: MeshReviewLoopConfig, request_fn=None):
        kwargs = {}
        if request_fn is not None:
            kwargs["request_fn"] = request_fn
        return MeshReviewLoop(
            config,
            status_file=str(root / "status.json"),
            output_file=str(root / "results.json"),
            recursive_status_file=str(root / "recursive.json"),
            extension_status_file=str(root / "extension.json"),
            **kwargs,
        )

    def test_local_cycle_limit_is_hard_bounded(self):
        with self.assertRaises(ValueError):
            MeshReviewLoopConfig(cycles=MAX_LOCAL_CYCLES + 1)

    def test_external_mode_requires_confirmation_and_rate_interval(self):
        with self.assertRaises(ValueError):
            MeshReviewLoopConfig(send_perplexity=True)
        with self.assertRaises(ValueError):
            MeshReviewLoopConfig(
                send_perplexity=True,
                confirm_send=CONFIRM_SEND_TOKEN,
                interval_seconds=1,
            )

    def test_request_rejects_credential_like_values(self):
        with self.assertRaises(ValueError):
            MeshReviewLoopConfig(request="review REDACTED_FAKE_CREDENTIAL_PLACEHOLDER")

    def test_dry_run_never_calls_external_request(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_fn = Mock(side_effect=AssertionError("network request attempted"))
            loop = self.make_loop(root, MeshReviewLoopConfig(), request_fn)
            with patch.dict(os.environ, {}, clear=True):
                status = loop.run()
            results = json.loads((root / "results.json").read_text(encoding="utf-8"))
        request_fn.assert_not_called()
        self.assertEqual(status["status"], "completed")
        self.assertEqual(status["completed_cycles"], 1)
        self.assertEqual(status["external_requests"], 0)
        self.assertTrue(status["dry_run"])
        self.assertFalse(status["cascade_chat_connected"])
        self.assertIn("prompt_preview", results["results"][0])

    def test_external_mode_uses_one_mocked_request_without_logging_key(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_fn = Mock(return_value={"choices": [{"message": {"content": "review"}}]})
            config = MeshReviewLoopConfig(
                send_perplexity=True,
                confirm_send=CONFIRM_SEND_TOKEN,
                interval_seconds=30,
                max_seconds=1,
            )
            loop = self.make_loop(root, config, request_fn)
            api_key = "rotated-test-key-not-a-real-secret"
            with patch.dict(os.environ, {"PERPLEXITY_API_KEY": api_key}, clear=True):
                status = loop.run()
            serialized = (root / "status.json").read_text(encoding="utf-8")
            results = json.loads((root / "results.json").read_text(encoding="utf-8"))
        request_fn.assert_called_once()
        self.assertEqual(status["external_requests"], 1)
        self.assertFalse(status["dry_run"])
        self.assertNotIn(api_key, serialized)
        self.assertEqual(results["results"][0]["response"]["choices"][0]["message"]["content"], "review")

    def test_external_mode_without_environment_key_is_blocked(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = MeshReviewLoopConfig(
                send_perplexity=True,
                confirm_send=CONFIRM_SEND_TOKEN,
                interval_seconds=30,
                max_seconds=1,
            )
            loop = self.make_loop(root, config, Mock())
            with patch.dict(os.environ, {}, clear=True), self.assertRaises(ValueError):
                loop.run()

    def test_preemptive_stop_completes_without_a_cycle(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            loop = self.make_loop(root, MeshReviewLoopConfig(cycles=2))
            loop.stop()
            status = loop.run()
            results = json.loads((root / "results.json").read_text(encoding="utf-8"))
        self.assertEqual(status["status"], "stopped")
        self.assertEqual(status["completed_cycles"], 0)
        self.assertEqual(results["results"], [])

    def test_external_cycle_limit_is_hard_bounded(self):
        with self.assertRaises(ValueError):
            MeshReviewLoopConfig(
                send_perplexity=True,
                confirm_send=CONFIRM_SEND_TOKEN,
                cycles=MAX_EXTERNAL_CYCLES + 1,
                interval_seconds=30,
            )

    def test_api_key_not_in_results_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            request_fn = Mock(return_value={"choices": [{"message": {"content": "review"}}]})
            config = MeshReviewLoopConfig(
                send_perplexity=True,
                confirm_send=CONFIRM_SEND_TOKEN,
                interval_seconds=30,
                max_seconds=1,
            )
            loop = self.make_loop(root, config, request_fn)
            api_key = "rotated-test-key-not-a-real-secret"
            with patch.dict(os.environ, {"PERPLEXITY_API_KEY": api_key}, clear=True):
                loop.run()
            serialized = (root / "results.json").read_text(encoding="utf-8")
        self.assertNotIn(api_key, serialized)

    def test_max_seconds_caps_completed_cycles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            loop = self.make_loop(
                root,
                MeshReviewLoopConfig(cycles=6, interval_seconds=0.1, max_seconds=0.05),
            )
            status = loop.run()
        self.assertEqual(status["completed_cycles"], 1)

    def test_guardrails_present_in_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            loop = self.make_loop(root, MeshReviewLoopConfig())
            status = loop.run()
        self.assertIn("dry_run_by_default", status["guardrails"])
        self.assertTrue(status["bounded"])

    def test_sk_credential_rejected_in_request(self):
        with self.assertRaises(ValueError):
            MeshReviewLoopConfig(request="use sk-proj-abcdefghijklmnopqrstuvwxyz123456")


if __name__ == "__main__":
    unittest.main()
