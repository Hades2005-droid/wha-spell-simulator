"""Tests for Polymarket Asuna unify catalog (no live network required)."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "tools" / "polymarket_asuna_point0_unify.py"


def load():
    spec = importlib.util.spec_from_file_location("polymarket_asuna_point0_unify", MOD)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


class PolymarketUnifyTests(unittest.TestCase):
    def test_self_test_and_discord_community(self):
        mod = load()
        payload = mod.build()
        self.assertEqual(payload["schema"], mod.SCHEMA)
        self.assertTrue(payload["ok"])
        self.assertFalse(payload["controls"]["live_default"])
        self.assertTrue(
            payload["discord"]["community_invite"].endswith("/polymarket")
        )
        self.assertIn("perplexity_connect.py", payload["perplexity"]["auto_connect_cli"])
        self.assertTrue(all(f["exists"] for f in payload["oracle"]["files"]))


if __name__ == "__main__":
    unittest.main()
