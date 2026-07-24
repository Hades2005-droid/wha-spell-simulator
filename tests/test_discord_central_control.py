import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DISCORD = ROOT / "tools" / "discord_asuna_point0_unify.py"
CENTRAL = ROOT / "tools" / "perplexity_asuna_central_control.py"
DEEPSEEK_ALIAS = ROOT / "tools" / "deepseek_asuna_zero_unify.py"
NOTIFY = ROOT / "tools" / "discord_local" / "notify.py"
DISCORD_BRIDGE = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "discord_asuna_point0_unification.json"
)
CENTRAL_BRIDGE = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "perplexity_asuna_central_control.json"
)


class DiscordAsunaPoint0UnifyTests(unittest.TestCase):
    def test_write_unifies_discord_paused(self):
        proc = subprocess.run(
            [sys.executable, str(DISCORD), "write"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])
        self.assertTrue(DISCORD_BRIDGE.is_file())
        doc = json.loads(DISCORD_BRIDGE.read_text(encoding="utf-8"))
        self.assertEqual(
            doc["schema"], "shadow_garden.discord_asuna_point0_unification.v1"
        )
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["lane"]["id"], "discord_status_notify")
        self.assertEqual(doc["unification_target"]["name"], "perplexity_asuna_point_0")
        self.assertFalse(doc["controls"]["webhook_post"])
        self.assertFalse(doc["controls"]["scrape_channel_history"])
        self.assertEqual(doc["api_surface"]["mode"], "env_names_only")
        self.assertIn("ENABLE_DISCORD", doc["api_surface"]["env_names"])
        self.assertIn("DISCORD_WEBHOOK_URL", doc["api_surface"]["env_names"])
        self.assertGreaterEqual(doc["metrics"]["vector_count"], 3)
        self.assertEqual(doc["metrics"]["webhook_posts"], 0)
        dumped = json.dumps(doc)
        self.assertNotIn("discord.com/api/webhooks/", dumped)

    def test_self_test(self):
        proc = subprocess.run(
            [sys.executable, str(DISCORD), "self-test"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])


class DiscordLocalNotifyTests(unittest.TestCase):
    def test_dry_run_ping(self):
        import os

        env = {
            k: v
            for k, v in os.environ.items()
            if not k.startswith("DISCORD") and k != "ENABLE_DISCORD"
        }
        proc = subprocess.run(
            [sys.executable, str(NOTIFY), "ping", "--message", "unit dry-run"],
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
            cwd=str(ROOT),
            env=env,
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout)
        doc = json.loads(proc.stdout)
        self.assertTrue(doc.get("dry_run"))
        self.assertTrue(doc.get("ok"))


class DeepSeekAliasTests(unittest.TestCase):
    def test_alias_self_test(self):
        proc = subprocess.run(
            [sys.executable, str(DEEPSEEK_ALIAS), "self-test"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])


class PerplexityCentralControlTests(unittest.TestCase):
    def test_central_weaves_discord_and_deepseek(self):
        proc = subprocess.run(
            [sys.executable, str(CENTRAL), "write"],
            capture_output=True,
            text=True,
            timeout=180,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:800])
        self.assertTrue(CENTRAL_BRIDGE.is_file())
        doc = json.loads(CENTRAL_BRIDGE.read_text(encoding="utf-8"))
        self.assertEqual(
            doc["schema"], "shadow_garden.perplexity_asuna_central_control.v1"
        )
        self.assertTrue(doc["ok"])
        self.assertEqual(
            doc["central_control"]["name"], "perplexity_asuna_point_0"
        )
        ids = {s["id"] for s in doc["surfaces"]}
        self.assertIn("deepseek", ids)
        self.assertIn("discord", ids)
        self.assertIn("white_moon", ids)
        self.assertIn("github", ids)
        self.assertIn("kimi3", ids)
        self.assertTrue(doc["metrics"]["deepseek_ok"])
        self.assertTrue(doc["metrics"]["discord_ok"])
        self.assertTrue(doc["metrics"]["kimi3_ok"])
        self.assertEqual(
            doc["central_control"]["completion_bridge"], "kimi3_third_leverage"
        )
        self.assertEqual(doc["leverage_stack"]["3"], "kimi3_completion_to_local_open_weights")
        self.assertFalse(doc["controls"]["discord_webhook_post"])
        self.assertGreaterEqual(doc["metrics"]["vector_sum"], 25)


class Kimi3AsunaPoint0UnifyTests(unittest.TestCase):
    def test_write_third_leverage_transition(self):
        tool = ROOT / "tools" / "kimi3_asuna_point0_unify.py"
        bridge = (
            ROOT
            / "shadow_garden_handoff"
            / "bridges"
            / "kimi3_asuna_point0_unification.json"
        )
        transition = (
            ROOT
            / "shadow_garden_handoff"
            / "bridges"
            / "kimi3_local_open_weights_transition.json"
        )
        proc = subprocess.run(
            [sys.executable, str(tool), "write"],
            capture_output=True,
            text=True,
            timeout=60,
            check=False,
            cwd=str(ROOT),
        )
        self.assertEqual(proc.returncode, 0, proc.stderr or proc.stdout[:500])
        self.assertTrue(bridge.is_file())
        self.assertTrue(transition.is_file())
        doc = json.loads(bridge.read_text(encoding="utf-8"))
        self.assertEqual(
            doc["schema"], "shadow_garden.kimi3_asuna_point0_unification.v1"
        )
        self.assertTrue(doc["ok"])
        self.assertEqual(doc["leverage"]["ordinal"], 3)
        self.assertEqual(
            doc["leverage"]["role"],
            "asuna_point0_completion_to_local_open_weights",
        )
        self.assertEqual(
            doc["unification_target"]["name"], "perplexity_asuna_point_0"
        )
        self.assertFalse(doc["controls"]["provider_calls"])
        self.assertTrue(doc["controls"]["local_open_weights_preferred"])
        self.assertIn("KIMI_API_KEY", doc["api_surface"]["env_names"])
        self.assertIn("KIMI3_TRANSITION_ARMED", doc["api_surface"]["env_names"])
        self.assertGreaterEqual(doc["metrics"]["vector_count"], 5)
        plan = json.loads(transition.read_text(encoding="utf-8"))
        self.assertEqual(
            plan["schema"],
            "shadow_garden.kimi3_local_open_weights_transition.v1",
        )
        self.assertEqual(plan["to"], "local_open_weights_mesh")
        self.assertFalse(plan["armed"])


if __name__ == "__main__":
    unittest.main()
