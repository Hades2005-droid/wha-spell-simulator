#!/usr/bin/env python3
"""
Polymarket → Asuna Point-0 unify catalog (entropy oracle + Discord community).

Metadata only by default. Live Gamma/CLOB pulls require ENABLE_POLYMARKET=1.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.polymarket_asuna_point0_unification.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "polymarket_entropy_oracle.json"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "polymarket_entropy_oracle.json"
STATUS_OUT = Path("/tmp/shadow_garden_polymarket_entropy_oracle.json")

ENV_NAMES = [
    "ENABLE_POLYMARKET",
    "POLYMARKET_LIVE_OK",
    "POLYMARKET_GAMMA_BASE",
    "POLYMARKET_CLOB_BASE",
    "POLYMARKET_MIN_LIQUIDITY",
    "POLYMARKET_STALE_AFTER_MS",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def env_presence() -> dict[str, bool]:
    return {n: bool(os.environ.get(n)) for n in ENV_NAMES}


def live_allowed() -> bool:
    return os.environ.get("ENABLE_POLYMARKET") == "1" or os.environ.get(
        "POLYMARKET_LIVE_OK"
    ) == "1"


def discord_surface() -> dict[str, Any]:
    return {
        "community_invite": "https://discord.com/invite/polymarket",
        "community_label": "Polymarket Discord",
        "wha_bot_bridge": "tools/discord_bot_bridge.py",
        "asuna_catalog": "shadow_garden_handoff/bridges/discord_asuna_point0_unification.json",
        "notify_module": "src/bridge/discordNotify.js",
        "live_requires": ["ENABLE_DISCORD=1", "DISCORD_LIVE_OK=1"],
        "paused_by_default": True,
        "roles": [
            "status_notify_oracle_health",
            "polymarket_community_pointer",
            "phase3_persephone_paired_lane",
        ],
    }


def perplexity_surface() -> dict[str, Any]:
    return {
        "auto_connect_cli": "tools/perplexity_connect.py",
        "central_control_cli": "tools/perplexity_asuna_central_control.py",
        "role": "research_and_going_forward_leverage",
        "ssl_fix": "certifi_context",
        "bulk_upload_requires_approval": True,
    }


def oracle_paths() -> dict[str, Any]:
    root = WHA / "src" / "oracle" / "polymarket"
    files = [
        "index.ts",
        "client.ts",
        "entropy.ts",
        "parse.ts",
        "http.ts",
        "rateLimit.ts",
        "research.ts",
        "types.ts",
    ]
    return {
        "package": str(root),
        "cli": "tools/polymarket_oracle.mjs",
        "files": [
            {
                "name": name,
                "exists": (root / name).is_file(),
                "path": str(root / name),
            }
            for name in files
        ],
    }


def try_live_sample() -> dict[str, Any] | None:
    if not live_allowed():
        return None
    cli = WHA / "tools" / "polymarket_oracle.mjs"
    if not cli.is_file():
        return {"ok": False, "error": "missing_cli"}
    env = os.environ.copy()
    env["ENABLE_POLYMARKET"] = "1"
    proc = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            str(cli),
            "sample",
        ],
        capture_output=True,
        text=True,
        timeout=45,
        check=False,
        cwd=str(WHA),
        env=env,
    )
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "sample_parse_failed",
            "exit": proc.returncode,
            "stderr": (proc.stderr or "")[:300],
        }


def build() -> dict[str, Any]:
    paths = oracle_paths()
    sample = try_live_sample()
    payload = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "phase": 2,
        "lane": {
            "id": "polymarket_entropy_oracle",
            "domain": "market_data_entropy",
            "transport": "gamma_plus_clob_public_read",
            "default_state": "PAUSED",
            "leveraged_by": "perplexity_asuna_point_0",
        },
        "unification_target": {
            "name": "perplexity_asuna_point_0",
            "point_0": "HOME",
            "lane": "perplexity_fable5_synthesis",
            "role": "entropy_oracle_surface",
            "meaning": (
                "Index Polymarket structured probabilities as a fail-soft entropy "
                "oracle for the local simulation; Perplexity auto-connect for research."
            ),
        },
        "api_surface": {
            "mode": "env_names_only",
            "gamma": "https://gamma-api.polymarket.com",
            "clob": "https://clob.polymarket.com",
            "docs": "https://docs.polymarket.com/api-reference/rate-limits",
            "env_names": ENV_NAMES,
            "env_present": env_presence(),
            "enable_polymarket_armed": live_allowed(),
            "notes": [
                "Read-only public endpoints; no trading keys in this surface.",
                "Prefer /markets/keyset (offset pagination returns 422).",
                "outcomePrices may be JSON strings — client parses defensively.",
            ],
        },
        "defenses": [
            "timeout_abort",
            "retry_backoff_retry_after",
            "local_sliding_window_limiter",
            "circuit_breaker",
            "stale_liquidity_quality_gates",
            "soft_empty_sample_when_live_off",
        ],
        "oracle": paths,
        "discord": discord_surface(),
        "perplexity": perplexity_surface(),
        "live_sample": sample,
        "controls": {
            "provider_trading": False,
            "credential_logging": False,
            "content_neutral": True,
            "live_default": False,
            "discord_webhook_post": False,
        },
        "cli": {
            "status": "node --experimental-strip-types tools/polymarket_oracle.mjs status",
            "research": "node --experimental-strip-types tools/polymarket_oracle.mjs research",
            "sample": "ENABLE_POLYMARKET=1 node --experimental-strip-types tools/polymarket_oracle.mjs sample",
            "unify": "python3 tools/polymarket_asuna_point0_unify.py write",
            "perplexity_health": "python3 tools/perplexity_connect.py health",
            "discord_status": "python3 tools/discord_bot_bridge.py status",
        },
    }
    files_ok = all(f.get("exists") for f in paths["files"])
    payload["ok"] = bool(files_ok)
    payload["metrics"] = {
        "vector_count": 8,
        "files_ok": files_ok,
        "live_armed": live_allowed(),
        "live_sample_ok": bool(sample and sample.get("ok")),
    }
    return payload


def write_outputs(payload: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for path in (STATUS_OUT, DEFAULT_OUT, MIRROR_OUT):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            written.append(str(path))
        except OSError:
            continue
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Polymarket entropy oracle unify")
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test"],
    )
    args = parser.parse_args(argv)
    payload = build()
    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": payload.get("ok"),
                    "lane": payload.get("lane"),
                    "metrics": payload.get("metrics"),
                    "discord": payload.get("discord"),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload["schema"] == SCHEMA
        assert payload["controls"]["live_default"] is False
        assert payload["discord"]["community_invite"].endswith("/polymarket")
        print(json.dumps({"ok": True, "metrics": payload["metrics"]}, indent=2))
        return 0 if payload.get("ok") else 1
    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
