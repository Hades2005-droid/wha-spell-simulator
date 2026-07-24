"""Tests for WHA Discord bot bridge adapter (no live network)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
BRIDGE = ROOT / "tools" / "discord_bot_bridge.py"

# Ensure importable in-process
sys.path.insert(0, str(ROOT / "tools"))
import discord_bot_bridge as dbb  # noqa: E402


class DiscordBotBridgeTests(unittest.TestCase):
    def test_status_cli_no_secrets(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("DISCORD")}
        env.pop("ENABLE_DISCORD", None)
        env.pop("DISCORD_LIVE_OK", None)
        proc = subprocess.run(
            [sys.executable, str(BRIDGE), "status"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            cwd=str(ROOT),
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        doc = json.loads(proc.stdout)
        self.assertEqual(doc["schema"], "shadow_garden.wha_discord_bot_bridge.v1")
        self.assertFalse(doc["live_discord"])
        self.assertEqual(doc["execution_mode"], "manifest_only")
        blob = json.dumps(doc)
        self.assertNotIn("discord.com/api/webhooks", blob)

    def test_notify_dry_run_without_gates(self):
        env = {k: v for k, v in os.environ.items() if not k.startswith("DISCORD")}
        env.pop("ENABLE_DISCORD", None)
        env.pop("DISCORD_LIVE_OK", None)
        proc = subprocess.run(
            [
                sys.executable,
                str(BRIDGE),
                "notify",
                "--text",
                "unit test dry-run",
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
            cwd=str(ROOT),
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        doc = json.loads(proc.stdout)
        self.assertTrue(doc.get("dry_run"))
        self.assertTrue(doc.get("skipped"))

    def test_live_allowed_requires_both_flags(self):
        with mock.patch.dict(os.environ, {"ENABLE_DISCORD": "1"}, clear=False):
            self.assertFalse(dbb.live_allowed())
        with mock.patch.dict(
            os.environ,
            {"ENABLE_DISCORD": "1", "DISCORD_LIVE_OK": "1"},
            clear=False,
        ):
            self.assertTrue(dbb.live_allowed())

    def test_bridge_pointer_includes_sg_path(self):
        ptr = dbb.bridge_pointer()
        self.assertIn("sg_module", ptr)
        self.assertIn("phase3_bridge", ptr)
        self.assertFalse(ptr["live_discord"])


if __name__ == "__main__":
    unittest.main()
