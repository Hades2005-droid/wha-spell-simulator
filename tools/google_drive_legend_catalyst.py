#!/usr/bin/env python3
"""
Google Drive legend catalyst (Catalyst 3) — local CloudStorage index.

Google Drive *MCP* is not currently wired in Cursor. This tool uses the
Desktop/CloudStorage sync root as the legend catalyst surface until an MCP
server is added. Metadata + content digests only; no uploads; no secret values.

Legend sources (Drive My Drive):
  - local-ai-stack-decision-shadow-garden.md  → Qwen3-8B default decision
  - CATALYST_UNIFIED.md                      → Catalyst 3 unified package
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.google_drive_legend_catalyst.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CATALYST_ORDINAL = 3

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
DEFAULT_DRIVE_ROOT = Path(
    os.environ.get(
        "GOOGLE_DRIVE_ROOT",
        str(HOME / "Library/CloudStorage/GoogleDrive-frederickpr10@gmail.com"),
    )
)
MY_DRIVE = DEFAULT_DRIVE_ROOT / "My Drive"

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "google_drive_legend_catalyst.json"
)
STATUS_OUT = Path("/tmp/shadow_garden_google_drive_legend_catalyst.json")

LEGEND_FILES = (
    {
        "id": "local_ai_stack_decision",
        "rel": "local-ai-stack-decision-shadow-garden.md",
        "role": "qwen3_8b_default_decision_legend",
        "preferred_model": "qwen3:8b",
    },
    {
        "id": "catalyst_unified",
        "rel": "CATALYST_UNIFIED.md",
        "role": "catalyst_3_unified_technical_package",
        "preferred_model": None,
    },
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha16(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()[:16]
    except OSError:
        return None


def index_legend(drive_root: Path) -> dict[str, Any]:
    my = drive_root / "My Drive"
    items = []
    for spec in LEGEND_FILES:
        path = my / spec["rel"]
        exists = path.is_file()
        item: dict[str, Any] = {
            "id": spec["id"],
            "role": spec["role"],
            "rel": spec["rel"],
            "path": str(path),
            "exists": exists,
            "preferred_model": spec["preferred_model"],
            "sha256_16": sha16(path) if exists else None,
            "bytes": path.stat().st_size if exists else None,
        }
        if exists and path.suffix == ".md":
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
                # First non-empty heading / executive line only — content-neutral excerpt
                for line in text.splitlines():
                    s = line.strip()
                    if s.startswith("#"):
                        item["title"] = s.lstrip("#").strip()[:160]
                        break
            except OSError:
                pass
        items.append(item)

    qwen_decision = next(
        (i for i in items if i["id"] == "local_ai_stack_decision"), {}
    )
    return {
        "drive_root": str(drive_root),
        "my_drive": str(my),
        "my_drive_exists": my.is_dir(),
        "items": items,
        "qwen_default": {
            "from_legend": bool(qwen_decision.get("exists")),
            "ollama_tag": "qwen3:8b",
            "family": "qwen3",
            "role": "always_on_local_open_weights",
            "source_doc": qwen_decision.get("rel"),
        },
        "mcp": {
            "google_drive_mcp_configured": False,
            "note": (
                "No Google Drive MCP server is active in Cursor. "
                "This catalyst uses local CloudStorage sync. "
                "When a Drive MCP is added, point GOOGLE_DRIVE_ROOT and reload MCP."
            ),
            "suggested_env": ["GOOGLE_DRIVE_ROOT", "GOOGLE_DRIVE_MCP_ENABLED"],
        },
    }


def build(drive_root: Path | None = None) -> dict[str, Any]:
    root = drive_root or DEFAULT_DRIVE_ROOT
    legend = index_legend(root)
    present = sum(1 for i in legend["items"] if i.get("exists"))
    payload = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "catalyst": {
            "ordinal": CATALYST_ORDINAL,
            "id": "catalyst_3_google_drive_legend",
            "label": "Google Drive legend catalyst 3",
            "paired_local_spell": "shadow_garden_handoff/terminal_auto/outbox/catalyst_spell_3.json",
            "meaning": (
                "Drive-synced legend docs steer local open-weights defaults "
                "(Qwen3-8B) and Catalyst 3 package provenance — metadata only."
            ),
        },
        "legend": legend,
        "polymarket_handoff": {
            "role": "entropy_oracle_feeds_qwen_local",
            "oracle_cli": "tools/polymarket_oracle.mjs",
            "bridge_cli": "tools/polymarket_qwen_open_weights_bridge.py",
            "preferred_model": "qwen3:8b",
        },
        "controls": {
            "uploads": False,
            "provider_calls": False,
            "credential_logging": False,
            "content_neutral": True,
            "arm_transition": False,
            "secrets_in_artifacts": False,
        },
        "cli": {
            "status": "python3 tools/google_drive_legend_catalyst.py status",
            "write": "python3 tools/google_drive_legend_catalyst.py write",
        },
        "metrics": {
            "vector_count": present + 3,
            "legend_files_present": present,
            "legend_files_total": len(LEGEND_FILES),
            "qwen_decision_present": bool(legend["qwen_default"]["from_legend"]),
        },
    }
    payload["ok"] = present >= 1 and legend["my_drive_exists"]
    return payload


def write_outputs(payload: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for path in (STATUS_OUT, DEFAULT_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Google Drive legend catalyst 3")
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test"],
    )
    parser.add_argument("--drive-root", default=None)
    args = parser.parse_args(argv)
    root = Path(args.drive_root).expanduser() if args.drive_root else None
    payload = build(root)
    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": payload.get("ok"),
                    "catalyst": payload.get("catalyst"),
                    "qwen_default": payload["legend"]["qwen_default"],
                    "mcp": payload["legend"]["mcp"],
                    "metrics": payload.get("metrics"),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload["schema"] == SCHEMA
        assert payload["catalyst"]["ordinal"] == 3
        assert payload["controls"]["uploads"] is False
        print(json.dumps({"ok": True, "metrics": payload["metrics"]}, indent=2))
        return 0 if payload.get("ok") else 1
    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
