#!/usr/bin/env python3
"""Validate authority-package text files are ASCII-only (Copilot request-body guard)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MON = ROOT
FED = MON / "live" / "ai_memory_federation"
GV = Path("/Users/fredwashere/Movies/Grok-Videos")
SG = Path("/Users/fredwashere/ShadowGarden")

TEXT_SUFFIXES = {".md", ".txt", ".json", ".py", ".sh", ".mjs", ".js", ".yaml", ".yml"}

AUTHORITY_RELATIVE = [
    "live/sovereign_42_authority.json",
    "live/grok_terminal_authority.json",
    "live/ai_memory_federation/perplexity_eden_fusion_task.json",
    "live/ai_memory_federation/perplexity_persona_prep_stack.md",
    "live/ai_memory_federation/federation_manifest.json",
    "live/ai_memory_federation/manual_imports/spacetime_alchemy_42_sovereign_codex_sanitized.md",
    "live/PERPLEXITY_FINAL_LAUNCH_CODE.txt",
]

AUTHORITY_ABSOLUTE = [
    GV / "eden_shadow_garden_fusion" / "PERPLEXITY_INSTALL_BUNDLE.md",
    GV / "eden_shadow_garden_fusion" / "PERPLEXITY_FUSION_HANDOFF.md",
    GV / "eden_shadow_garden_fusion" / "spacetime_alchemy_42_sovereign_codex_sanitized.md",
    GV / "eden_shadow_garden_fusion" / "eden_grok_replica_fuse.json",
    SG / "live" / "spacetime_alchemy" / "PERPLEXITY_CONTEXT_BEDROCK.md",
]


def tracked_files() -> list[Path]:
    files: list[Path] = []
    for rel in AUTHORITY_RELATIVE:
        p = MON / rel
        if p.is_file():
            files.append(p)
    for p in AUTHORITY_ABSOLUTE:
        if p.is_file():
            files.append(p)
    return sorted(set(files))


def validate(paths: list[Path] | None = None) -> dict:
    paths = paths or tracked_files()
    non_ascii: list[str] = []
    missing: list[str] = []
    checked: list[str] = []

    for p in paths:
        if not p.is_file():
            missing.append(str(p))
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        text = p.read_text(encoding="utf-8")
        if any(ord(ch) > 127 for ch in text):
            non_ascii.append(str(p.relative_to(MON)) if str(p).startswith(str(MON)) else str(p))
        checked.append(str(p))

    return {
        "ok": not non_ascii,
        "checked": checked,
        "missing": missing,
        "non_ascii": non_ascii,
        "count": len(checked),
    }


def main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    result = validate()
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())