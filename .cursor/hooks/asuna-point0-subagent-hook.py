#!/usr/bin/env python3
"""subagentStart: arm Asuna Point-0 / Fable5 routing for delegated agents.

Allows subagents and injects a short agent_message with Point-0 routes.
Does not block. Fail open. No secrets, no adult scrapes, no auto follow-up loops.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent / "logs"
TELEMETRY = LOG_DIR / "asuna_point0_subagent.jsonl"
CATALOG = (
    Path(__file__).resolve().parents[2]
    / "shadow_garden_handoff"
    / "bridges"
    / "github_asuna_point0_unification.json"
)
DEEPSEEK_CATALOG = (
    Path(__file__).resolve().parents[2]
    / "shadow_garden_handoff"
    / "bridges"
    / "deepseek_asuna_point0_unification.json"
)
GROK_CATALOG = (
    Path(__file__).resolve().parents[2]
    / "shadow_garden_handoff"
    / "bridges"
    / "grok_xai_asuna_point0_unification.json"
)
CORNER_CATALOG = (
    Path(__file__).resolve().parents[2]
    / "shadow_garden_handoff"
    / "bridges"
    / "white_moon_eastern_corner.json"
)

ROUTE = (
    "Asuna Point-0 subagent lane: prefer "
    "python3 tools/github_asuna_point0_unify.py write → "
    "python3 tools/deepseek_asuna_point0_unify.py write → "
    "python3 tools/grok_xai_asuna_point0_unify.py write → "
    "python3 tools/white_moon_eastern_corner_unify.py write "
    "(eastern white-moon: DeepSeek + Grok/xAI) → "
    "compact+bedrock → shadow_garden_packet write. "
    "HOME point-0 (kitchen_log_cabin_floor_22). "
    "Prefer 127.0.0.1:11434 Ollama; remote DeepSeek/xAI opt-in via env only. "
    "Stripe scaffold: node tools/stripe_local/server.mjs (dry-run). "
    "Metadata only; env-var names only; one bounded cycle; "
    "no adult scrape; no bulk chat upload; no infinite recursive loops."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"permission": "allow"}))
        return 0

    sub_type = payload.get("subagent_type") or payload.get("type") or ""
    task = payload.get("task") or payload.get("description") or payload.get("prompt") or ""
    if not isinstance(task, str):
        task = str(task)

    catalog_ok = CATALOG.is_file()
    deepseek_ok = DEEPSEEK_CATALOG.is_file()
    grok_ok = GROK_CATALOG.is_file()
    corner_ok = CORNER_CATALOG.is_file()
    vectors = None
    deepseek_vectors = None
    grok_vectors = None
    corner_sum = None
    if catalog_ok:
        try:
            doc = json.loads(CATALOG.read_text(encoding="utf-8"))
            vectors = len(doc.get("vectors") or [])
        except (OSError, json.JSONDecodeError):
            vectors = None
    if deepseek_ok:
        try:
            doc = json.loads(DEEPSEEK_CATALOG.read_text(encoding="utf-8"))
            deepseek_vectors = len(doc.get("vectors") or [])
        except (OSError, json.JSONDecodeError):
            deepseek_vectors = None
    if grok_ok:
        try:
            doc = json.loads(GROK_CATALOG.read_text(encoding="utf-8"))
            grok_vectors = len(doc.get("vectors") or [])
        except (OSError, json.JSONDecodeError):
            grok_vectors = None
    if corner_ok:
        try:
            doc = json.loads(CORNER_CATALOG.read_text(encoding="utf-8"))
            corner_sum = (doc.get("metrics") or {}).get("corner_vector_sum")
        except (OSError, json.JSONDecodeError):
            corner_sum = None

    event = {
        "ts": utc_now(),
        "event": "asuna_point0_subagent_start",
        "subagent_type": sub_type,
        "task_len": len(task),
        "catalog_exists": catalog_ok,
        "vectors": vectors,
        "deepseek_catalog_exists": deepseek_ok,
        "deepseek_vectors": deepseek_vectors,
        "grok_catalog_exists": grok_ok,
        "grok_vectors": grok_vectors,
        "corner_catalog_exists": corner_ok,
        "corner_vector_sum": corner_sum,
        "permission": "allow",
    }
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with TELEMETRY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass

    out = {
        "permission": "allow",
        "agent_message": ROUTE
        + (f" Catalog vectors={vectors}." if vectors is not None else "")
        + (
            f" DeepSeek vectors={deepseek_vectors}."
            if deepseek_vectors is not None
            else ""
        )
        + (f" Grok vectors={grok_vectors}." if grok_vectors is not None else "")
        + (
            f" Eastern white-moon sum={corner_sum}."
            if corner_sum is not None
            else ""
        ),
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
