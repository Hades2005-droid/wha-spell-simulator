#!/usr/bin/env python3
"""
Discord local status_notify dry-run (Shadow Garden).

Default: print what would be posted — never hits Discord APIs unless
ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1 are both set AND a webhook URL is present.

Never logs token/webhook values.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def presence() -> dict[str, bool]:
    names = [
        "ENABLE_DISCORD",
        "DISCORD_WEBHOOK_URL",
        "DISCORD_BOT_TOKEN",
        "DISCORD_TOKEN",
        "DISCORD_CHANNEL_ID",
        "DISCORD_GUILD_ID",
        "DISCORD_LIVE_OK",
    ]
    return {n: bool(os.environ.get(n)) for n in names}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Discord status_notify dry-run")
    parser.add_argument(
        "command",
        nargs="?",
        default="status",
        choices=["status", "ping", "self-test"],
    )
    parser.add_argument(
        "--message",
        default="Shadow Garden status_notify ping (content-neutral)",
        help="Message body for ping (content-neutral)",
    )
    args = parser.parse_args(argv)

    armed = os.environ.get("ENABLE_DISCORD") == "1"
    live = os.environ.get("DISCORD_LIVE_OK") == "1"
    webhook = os.environ.get("DISCORD_WEBHOOK_URL") or ""
    present = presence()

    if args.command == "self-test":
        print(
            json.dumps(
                {
                    "ok": True,
                    "dry_run_default": True,
                    "webhook_post_default": False,
                    "env_present": present,
                },
                indent=2,
            )
        )
        return 0

    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": True,
                    "service": "shadow_garden_discord_local",
                    "ts": utc_now(),
                    "mode": "armed_live" if (armed and live and webhook) else "dry_run",
                    "enable_discord": armed,
                    "live_ok": live,
                    "webhook_present": bool(webhook),
                    "env_present": present,
                    "controls": {
                        "secret_logged": False,
                        "scrape_channel_history": False,
                        "requires_ENABLE_DISCORD_and_DISCORD_LIVE_OK": True,
                    },
                    "asuna_point0_route": "perplexity_fable5_home_sim",
                },
                indent=2,
            )
        )
        return 0

    # ping
    payload = {
        "content": args.message[:1800],
        "allowed_mentions": {"parse": []},
    }
    if not (armed and live and webhook):
        print(
            json.dumps(
                {
                    "ok": True,
                    "dry_run": True,
                    "would_post": True,
                    "message_len": len(args.message),
                    "hint": "Set ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1 with webhook in env to post",
                },
                indent=2,
            )
        )
        return 0

    # Live post — webhook URL never printed
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        webhook,
        data=data,
        headers={"Content-Type": "application/json", "User-Agent": "ShadowGarden/1.0"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            code = int(resp.status)
        print(
            json.dumps(
                {
                    "ok": 200 <= code < 300,
                    "dry_run": False,
                    "http_status": code,
                    "posted": True,
                },
                indent=2,
            )
        )
        return 0 if 200 <= code < 300 else 1
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "dry_run": False,
                    "error": type(exc).__name__,
                    "posted": False,
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
