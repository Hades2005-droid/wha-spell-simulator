#!/usr/bin/env python3
"""
Perplexity Asuna central control — unify all Point-0 surfaces into one ledger.

Aggregates GitHub + DeepSeek + Grok/xAI + eastern white-moon + Discord + Kimi 3
(3rd leverage → local open-weights transition) + Stripe scaffolds toward
Perplexity Asuna HOME point-zero. Metadata only; no provider calls; no secret values.
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

SCHEMA = "shadow_garden.perplexity_asuna_central_control.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "perplexity_asuna_central_control.json"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "perplexity_asuna_central_control.json"
STATUS_OUT = Path("/tmp/shadow_garden_perplexity_asuna_central_control.json")

SURFACES: list[dict[str, str]] = [
    {
        "id": "github",
        "cli": "github_asuna_point0_unify.py",
        "catalog": "github_asuna_point0_unification.json",
        "role": "profile_index",
    },
    {
        "id": "deepseek",
        "cli": "deepseek_asuna_point0_unify.py",
        "catalog": "deepseek_asuna_point0_unification.json",
        "role": "eastern_local_open_weights",
    },
    {
        "id": "grok_xai",
        "cli": "grok_xai_asuna_point0_unify.py",
        "catalog": "grok_xai_asuna_point0_unification.json",
        "role": "eastern_white_moon_harmony_6",
    },
    {
        "id": "white_moon",
        "cli": "white_moon_eastern_corner_unify.py",
        "catalog": "white_moon_eastern_corner.json",
        "role": "eastern_corner_weave",
    },
    {
        "id": "discord",
        "cli": "discord_asuna_point0_unify.py",
        "catalog": "discord_asuna_point0_unification.json",
        "role": "status_notify_paused",
    },
    {
        "id": "kimi3",
        "cli": "kimi3_asuna_point0_unify.py",
        "catalog": "kimi3_asuna_point0_unification.json",
        "role": "third_leverage_local_open_weights_transition",
    },
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def run_surface(cli_name: str) -> dict[str, Any]:
    script = WHA / "tools" / cli_name
    if not script.is_file():
        return {"ok": False, "error": f"missing {cli_name}"}
    proc = subprocess.run(
        [sys.executable, str(script), "write"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        cwd=str(WHA),
    )
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "ok": proc.returncode == 0,
            "error": "json_parse_failed",
            "exit": proc.returncode,
        }


def stripe_scaffold_status() -> dict[str, Any]:
    server = WHA / "tools" / "stripe_local" / "server.mjs"
    cfg = WHA / "src" / "adapters" / "stripeConfig.js"
    return {
        "id": "stripe",
        "role": "payments_dry_run_scaffold",
        "ok": server.is_file() and cfg.is_file(),
        "server": str(server),
        "config": str(cfg),
        "live_default": False,
        "bind": "127.0.0.1:4242",
    }


def summarize(surface: dict[str, str], payload: dict[str, Any]) -> dict[str, Any]:
    metrics = payload.get("metrics") or {}
    return {
        "id": surface["id"],
        "role": surface["role"],
        "ok": bool(payload.get("ok")),
        "schema": payload.get("schema"),
        "vector_count": metrics.get("vector_count")
        or metrics.get("corner_vector_sum")
        or len(payload.get("vectors") or []),
        "catalog": str(
            WHA / "shadow_garden_handoff" / "bridges" / surface["catalog"]
        ),
        "cli": f"python3 tools/{surface['cli']} write",
    }


def build_central() -> dict[str, Any]:
    surfaces: list[dict[str, Any]] = []
    for spec in SURFACES:
        raw = run_surface(spec["cli"])
        surfaces.append(summarize(spec, raw))
    stripe = stripe_scaffold_status()
    surfaces.append(stripe)

    bedrock = SG / "live" / "spacetime_alchemy" / "PERPLEXITY_CONTEXT_BEDROCK.md"
    compact = SG / "live" / "spacetime_alchemy" / "fable5-compact.json"
    ok_count = sum(1 for s in surfaces if s.get("ok"))
    vector_sum = sum(int(s.get("vector_count") or 0) for s in surfaces)
    deepseek = next((s for s in surfaces if s["id"] == "deepseek"), {})
    discord = next((s for s in surfaces if s["id"] == "discord"), {})
    white_moon = next((s for s in surfaces if s["id"] == "white_moon"), {})
    kimi3 = next((s for s in surfaces if s["id"] == "kimi3"), {})

    payload = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "central_control": {
            "name": "perplexity_asuna_point_0",
            "point_0": "HOME",
            "archetype": "angela_asuna_home",
            "scene_id": "kitchen_log_cabin_floor_22",
            "lane": "perplexity_fable5_synthesis",
            "role": "unification_lever",
            "completion_bridge": "kimi3_third_leverage",
            "transition_target": "local_open_weights_mesh",
        },
        "perplexity": {
            "bedrock": str(bedrock),
            "bedrock_exists": bedrock.is_file(),
            "compact": str(compact),
            "compact_exists": compact.is_file(),
            "bulk_upload_requires_explicit_approval": True,
        },
        "surfaces": surfaces,
        "leverage_stack": {
            "1": "deepseek_local_open_weights",
            "2": "grok_xai_harmony_6_white_moon",
            "3": "kimi3_completion_to_local_open_weights",
        },
        "emphasis": {
            "deepseek": deepseek,
            "discord": discord,
            "eastern_white_moon": white_moon,
            "kimi3": kimi3,
        },
        "metrics": {
            "surface_count": len(surfaces),
            "surfaces_ok": ok_count,
            "vector_sum": vector_sum,
            "deepseek_ok": bool(deepseek.get("ok")),
            "discord_ok": bool(discord.get("ok")),
            "white_moon_ok": bool(white_moon.get("ok")),
            "kimi3_ok": bool(kimi3.get("ok")),
            "all_core_ok": ok_count >= 6,
        },
        "controls": {
            "provider_calls": False,
            "credential_logging": False,
            "content_neutral": True,
            "symbolic_only": True,
            "discord_webhook_post": False,
            "bulk_upload_perplexity": False,
            "local_open_weights_preferred": True,
        },
        "cli": {
            "central": "python3 tools/perplexity_asuna_central_control.py write",
            "deepseek": "python3 tools/deepseek_asuna_point0_unify.py write",
            "discord": "python3 tools/discord_asuna_point0_unify.py write",
            "kimi3": "python3 tools/kimi3_asuna_point0_unify.py write",
            "packet": "python3 tools/shadow_garden_packet.py write",
        },
    }
    payload["ok"] = bool(payload["metrics"]["all_core_ok"])
    return payload


def write_outputs(payload: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for path in (STATUS_OUT, DEFAULT_OUT, MIRROR_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Perplexity Asuna central control unification ledger"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test"],
    )
    args = parser.parse_args(argv)
    payload = build_central()
    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": payload.get("ok"),
                    "central_control": payload.get("central_control"),
                    "metrics": payload.get("metrics"),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload["schema"] == SCHEMA
        assert payload["metrics"]["surface_count"] >= 5
        assert payload["controls"]["discord_webhook_post"] is False
        print(json.dumps({"ok": True, "metrics": payload["metrics"]}, indent=2))
        return 0 if payload.get("ok") else 1
    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
