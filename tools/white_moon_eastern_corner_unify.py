#!/usr/bin/env python3
"""
Eastern white-moon corner weave: DeepSeek + Grok/xAI → Asuna Point-0.

Aggregates DeepSeek (local-open-weights east) and Grok/xAI (Harmony-6 moon)
catalogs into one corner ledger leveraged by Perplexity Asuna Point-0.
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

SCHEMA = "shadow_garden.white_moon_eastern_corner.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CORNER_ID = "eastern_white_moon"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "white_moon_eastern_corner.json"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "white_moon_eastern_corner.json"
STATUS_OUT = Path("/tmp/shadow_garden_white_moon_eastern_corner.json")

DEEPSEEK_CLI = WHA / "tools" / "deepseek_asuna_point0_unify.py"
GROK_CLI = WHA / "tools" / "grok_xai_asuna_point0_unify.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def run_unify(script: Path) -> dict[str, Any]:
    if not script.is_file():
        return {"ok": False, "error": f"missing {script.name}"}
    proc = subprocess.run(
        [sys.executable, str(script), "write"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=str(WHA),
    )
    # Prefer stdout JSON (tools print payload to stdout)
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "ok": proc.returncode == 0,
            "error": "json_parse_failed",
            "exit": proc.returncode,
            "stderr_head": (proc.stderr or "")[:200],
        }


def build_corner() -> dict[str, Any]:
    deepseek = run_unify(DEEPSEEK_CLI)
    grok = run_unify(GROK_CLI)
    ds_vectors = len(deepseek.get("vectors") or [])
    gx_vectors = len(grok.get("vectors") or [])
    payload = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "corner": {
            "id": CORNER_ID,
            "label": "Eastern White Moon",
            "tarot": "Moon_18",
            "yin_yang": "yin_white_moon_east",
            "partners": {
                "deepseek": "local_open_weights_east",
                "grok_xai": "harmony_6_white_moon",
            },
            "leveraged_by": "perplexity_asuna_point_0",
            "carrier": CARRIER,
            "bridge_signature": BRIDGE_SIGNATURE,
        },
        "deepseek": {
            "ok": bool(deepseek.get("ok")),
            "schema": deepseek.get("schema"),
            "vector_count": ds_vectors,
            "catalog": str(
                WHA
                / "shadow_garden_handoff"
                / "bridges"
                / "deepseek_asuna_point0_unification.json"
            ),
            "metrics": deepseek.get("metrics"),
        },
        "grok_xai": {
            "ok": bool(grok.get("ok")),
            "schema": grok.get("schema"),
            "vector_count": gx_vectors,
            "catalog": str(
                WHA
                / "shadow_garden_handoff"
                / "bridges"
                / "grok_xai_asuna_point0_unification.json"
            ),
            "metrics": grok.get("metrics"),
        },
        "asuna_point0": {
            "point_0": "HOME",
            "archetype": "angela_asuna_home",
            "lane": "perplexity_fable5_synthesis",
            "role": "unification_lever",
        },
        "metrics": {
            "deepseek_vectors": ds_vectors,
            "grok_vectors": gx_vectors,
            "corner_vector_sum": ds_vectors + gx_vectors,
            "both_ok": bool(deepseek.get("ok") and grok.get("ok")),
        },
        "controls": {
            "provider_calls": False,
            "credential_logging": False,
            "content_neutral": True,
            "symbolic_only": True,
            "bulk_upload_perplexity": False,
        },
        "cli": {
            "deepseek": "python3 tools/deepseek_asuna_point0_unify.py write",
            "grok_xai": "python3 tools/grok_xai_asuna_point0_unify.py write",
            "corner": "python3 tools/white_moon_eastern_corner_unify.py write",
        },
    }
    payload["ok"] = bool(payload["metrics"]["both_ok"])
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
        description="Weave DeepSeek + Grok/xAI as eastern white-moon Asuna corner"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test"],
    )
    args = parser.parse_args(argv)
    payload = build_corner()
    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": payload.get("ok"),
                    "corner": payload.get("corner"),
                    "metrics": payload.get("metrics"),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload["schema"] == SCHEMA
        assert payload["corner"]["id"] == CORNER_ID
        assert payload["metrics"]["corner_vector_sum"] >= 8
        print(json.dumps({"ok": True, "metrics": payload["metrics"]}, indent=2))
        return 0 if payload.get("ok") else 1
    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
