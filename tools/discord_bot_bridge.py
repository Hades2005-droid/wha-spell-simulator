#!/usr/bin/env python3
"""
WHA ↔ Shadow Garden Discord bridge adapter (status_notify lane).

Points at ShadowGarden spacetime_alchemy.discord_bridge when present;
falls back to tools/discord_local/notify.py for dry-run status.

Live Discord requires ENABLE_DISCORD=1 AND DISCORD_LIVE_OK=1 (never default-on).
Secrets: env only — never logged or written to artifacts.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.wha_discord_bot_bridge.v1"
HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
LOCAL_NOTIFY = WHA / "tools" / "discord_local" / "notify.py"
SG_MODULE = SG / "spacetime_alchemy" / "discord_bridge.py"
SG_STATUS = SG / "live" / "spacetime_alchemy" / "DISCORD_BRIDGE_STATUS.json"

ENV_NAMES = [
    "ENABLE_DISCORD",
    "DISCORD_LIVE_OK",
    "DISCORD_APPLICATION_ID",
    "DISCORD_WEBHOOK_URL",
    "DISCORD_BOT_TOKEN",
    "DISCORD_TOKEN",
    "DISCORD_CHANNEL_ID",
    "DISCORD_GUILD_ID",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def env_presence() -> dict[str, bool]:
    return {name: bool(os.environ.get(name)) for name in ENV_NAMES}


def live_allowed() -> bool:
    return (
        os.environ.get("ENABLE_DISCORD") == "1"
        and os.environ.get("DISCORD_LIVE_OK") == "1"
    )


def load_sg_bridge() -> Any | None:
    if not SG_MODULE.is_file():
        return None
    spec = importlib.util.spec_from_file_location(
        "shadow_garden_discord_bridge", SG_MODULE
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception:  # noqa: BLE001
        return None
    return module


def bridge_pointer() -> dict[str, Any]:
    sg = load_sg_bridge()
    prior: dict[str, Any] = {}
    if SG_STATUS.is_file():
        try:
            loaded = json.loads(SG_STATUS.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                prior = loaded
        except (OSError, json.JSONDecodeError):
            prior = {}
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "role": "status_notify_lane",
        "execution_mode": "live" if live_allowed() else "manifest_only",
        "live_discord": live_allowed(),
        "shadow_garden_root": str(SG),
        "sg_module": str(SG_MODULE),
        "sg_module_exists": SG_MODULE.is_file(),
        "sg_import_ok": sg is not None,
        "sg_status_path": str(SG_STATUS),
        "sg_prior_status": prior.get("status"),
        "sg_prior_mode": prior.get("mode"),
        "local_notify_cli": str(LOCAL_NOTIFY),
        "local_notify_exists": LOCAL_NOTIFY.is_file(),
        "env_present": env_presence(),
        "gates": {
            "enable_discord": os.environ.get("ENABLE_DISCORD") == "1",
            "discord_live_ok": os.environ.get("DISCORD_LIVE_OK") == "1",
            "live_send_allowed": live_allowed(),
        },
        "paired_bridge": "shadow_garden_handoff/bridges/discord_asuna_point0_unification.json",
        "phase3_bridge": "shadow_garden_handoff/bridges/phase3_persephone_shutdown_bridge.json",
        "polymarket": {
            "community_invite": "https://discord.com/invite/polymarket",
            "community_label": "Polymarket Discord",
            "oracle_bridge": "shadow_garden_handoff/bridges/polymarket_entropy_oracle.json",
            "oracle_cli": "tools/polymarket_oracle.mjs",
            "unify_cli": "tools/polymarket_asuna_point0_unify.py",
            "role": "status_notify_entropy_oracle_plus_community_pointer",
        },
        "perplexity_auto_connect": {
            "cli": "tools/perplexity_connect.py",
            "central_control_cli": "tools/perplexity_asuna_central_control.py",
        },
    }


def cmd_status() -> int:
    print(json.dumps(bridge_pointer(), indent=2))
    return 0


def cmd_summary() -> int:
    sg = load_sg_bridge()
    if sg is not None and hasattr(sg, "bridge_summary_for_export"):
        summary = sg.bridge_summary_for_export(compact=True)
        summary["wha_adapter"] = SCHEMA
        summary["live_discord"] = live_allowed()
        summary["execution_mode"] = "live" if live_allowed() else "manifest_only"
    else:
        summary = {
            "schema": SCHEMA,
            "mode": "ARMED_AWAITING_TOKEN",
            "role": "status_notify_lane",
            "sg_import_ok": False,
            "live_discord": live_allowed(),
            "execution_mode": "manifest_only",
        }
    print(json.dumps(summary, indent=2))
    return 0


def cmd_notify(text: str) -> int:
    if not live_allowed():
        print(
            json.dumps(
                {
                    "schema": SCHEMA,
                    "action": "notify",
                    "ok": True,
                    "dry_run": True,
                    "skipped": True,
                    "blocked": "requires ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1",
                    "text_len": len(text),
                    "dry_run_preview": text[:200],
                },
                indent=2,
            )
        )
        return 0

    sg = load_sg_bridge()
    if sg is not None and hasattr(sg, "notify"):
        result = sg.notify(text, force=True)
        result["wha_adapter"] = SCHEMA
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 2

    proc = subprocess.run(
        [sys.executable, str(LOCAL_NOTIFY), "ping", "--message", text],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
        cwd=str(WHA),
    )
    print(proc.stdout or proc.stderr)
    return proc.returncode


def cmd_ping() -> int:
    msg = f"WHA Discord bridge ping · `{utc_now()}` · status_notify lane"
    return cmd_notify(msg)


def cmd_merge(*, send_ping: bool) -> int:
    sg = load_sg_bridge()
    if sg is not None and hasattr(sg, "merge_status"):
        packet = sg.merge_status(send_ping=send_ping and live_allowed())
        packet["wha_adapter"] = SCHEMA
        packet["live_discord"] = live_allowed()
        print(
            json.dumps(
                {
                    "ok": True,
                    "status": packet.get("status"),
                    "mode": packet.get("mode"),
                    "live_discord": live_allowed(),
                    "path": str(SG_STATUS),
                },
                indent=2,
            )
        )
        return 0

    print(
        json.dumps(
            {
                "ok": False,
                "error": "shadow_garden discord_bridge unavailable",
                "sg_module": str(SG_MODULE),
                "hint": "Set SHADOW_GARDEN_ROOT or install spacetime_alchemy/discord_bridge.py",
            },
            indent=2,
        )
    )
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="WHA Discord bot bridge (Shadow Garden adapter)"
    )
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status", help="Bridge pointer + gating (no secrets)")
    sub.add_parser("summary", help="Export-safe summary for bedrock/compact")
    sub.add_parser("ping", help="Status ping (dry-run unless live gates pass)")
    p_n = sub.add_parser("notify", help="Custom status notify")
    p_n.add_argument("--text", required=True)
    p_m = sub.add_parser("merge", help="Register merge in Shadow Garden artifacts")
    p_m.add_argument(
        "--ping",
        action="store_true",
        help="Send live merge ping only when ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1",
    )

    args = parser.parse_args(argv)
    if args.cmd == "status":
        return cmd_status()
    if args.cmd == "summary":
        return cmd_summary()
    if args.cmd == "ping":
        return cmd_ping()
    if args.cmd == "notify":
        return cmd_notify(args.text)
    if args.cmd == "merge":
        return cmd_merge(send_ping=bool(args.ping))
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
