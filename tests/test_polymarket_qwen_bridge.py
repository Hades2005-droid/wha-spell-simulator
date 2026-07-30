"""Tests for Google Drive legend catalyst + Polymarket→Qwen bridge (local-only)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    path = ROOT / rel
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class DriveLegendCatalystTests(unittest.TestCase):
    def test_build_indexes_qwen_decision(self):
        mod = load("gdrive_legend", "tools/google_drive_legend_catalyst.py")
        payload = mod.build()
        self.assertEqual(payload["schema"], mod.SCHEMA)
        self.assertEqual(payload["catalyst"]["ordinal"], 3)
        self.assertFalse(payload["controls"]["uploads"])
        self.assertEqual(payload["legend"]["qwen_default"]["ollama_tag"], "qwen3:8b")
        self.assertFalse(payload["legend"]["mcp"]["google_drive_mcp_configured"])


class PolymarketQwenBridgeTests(unittest.TestCase):
    def test_bridge_prefers_qwen3_8b_and_stays_unarmed(self):
        mod = load("pm_qwen", "tools/polymarket_qwen_open_weights_bridge.py")
        payload = mod.build(invoke_local=False, force_sample=False)
        self.assertEqual(payload["schema"], mod.SCHEMA)
        self.assertEqual(payload["preferred_model"], "qwen3:8b")
        self.assertFalse(payload["lane"]["armed"])
        self.assertFalse(payload["metrics"]["cutover_ready"])
        self.assertIn("chat_packet", payload)
        self.assertEqual(payload["chat_packet"]["messages"][0]["role"], "system")


if __name__ == "__main__":
    unittest.main()
