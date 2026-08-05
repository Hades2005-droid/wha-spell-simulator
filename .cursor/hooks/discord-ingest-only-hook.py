#!/usr/bin/env python3
"""Discord ingest-only prompt gate — never arms posts."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INGEST_ARM = ROOT / "shadow_garden_handoff" / "bridges" / "DISCORD_INGEST_ARMED.json"

POST_PAT = re.compile(
    r"(?i)\b(discord\s*(post|send|ping|webhook\s*fire|notify\s*live)|"
    r"chat\.postMessage|execute\s*webhook)\b"
)
INGEST_PAT = re.compile(
    r"(?i)\b(discord\s*ingest|DISCORD_INGEST|docs?\s*index|"
    r"discord_asuna_point0|status_notify\s*ingest)\b"
)


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        payload = {}
    text = " ".join(
        str(payload.get(k, ""))
        for k in ("prompt", "user_prompt", "content", "message", "text")
    )
    if not text.strip():
        text = raw

    armed = INGEST_ARM.is_file()
    if POST_PAT.search(text) and not re.search(
        r"(?i)\b(DISCORD_LIVE_OK\s*=\s*1|ENABLE_DISCORD\s*=\s*1)\b", text
    ):
        out = {
            "permission": "ask",
            "user_message": "Discord posts stay gated. Ingest-only is armed; live send needs ENABLE_DISCORD=1 and DISCORD_LIVE_OK=1.",
            "agent_message": "Blocked Discord post intent without dual live gates. Prefer discord_asuna_point0_unify write / docs ingest.",
        }
        print(json.dumps(out))
        return 0

    if INGEST_PAT.search(text) or armed:
        ctx = (
            "Discord lane: INGEST_ONLY. Artifact DISCORD_INGEST_ARMED.json present={}. "
            "Run python3 tools/discord_asuna_point0_unify.py write. Do not POST."
        ).format(armed)
        print(json.dumps({"permission": "allow", "agent_message": ctx}))
        return 0

    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
