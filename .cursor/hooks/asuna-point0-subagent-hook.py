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
ROOT = Path(__file__).resolve().parents[2]
BRIDGES = ROOT / "shadow_garden_handoff" / "bridges"
CATALOG = BRIDGES / "github_asuna_point0_unification.json"
DEEPSEEK_CATALOG = BRIDGES / "deepseek_asuna_point0_unification.json"
GROK_CATALOG = BRIDGES / "grok_xai_asuna_point0_unification.json"
CORNER_CATALOG = BRIDGES / "white_moon_eastern_corner.json"
DISCORD_CATALOG = BRIDGES / "discord_asuna_point0_unification.json"
CENTRAL_CATALOG = BRIDGES / "perplexity_asuna_central_control.json"
KIMI3_CATALOG = BRIDGES / "kimi3_asuna_point0_unification.json"

ROUTE = (
    "Asuna Point-0 subagent lane: prefer "
    "python3 tools/github_asuna_point0_unify.py write → "
    "python3 tools/deepseek_asuna_point0_unify.py write → "
    "python3 tools/grok_xai_asuna_point0_unify.py write → "
    "python3 tools/white_moon_eastern_corner_unify.py write → "
    "python3 tools/discord_asuna_point0_unify.py write → "
    "python3 tools/kimi3_asuna_point0_unify.py write "
    "(3rd leverage → local_open_weights_mesh) → "
    "python3 tools/perplexity_asuna_central_control.py write "
    "(central lever → Perplexity) → compact+bedrock → shadow_garden_packet write. "
    "HOME point-0 (kitchen_log_cabin_floor_22). "
    "Prefer 127.0.0.1:11434 Ollama; remote APIs opt-in via env only. "
    "Discord PAUSED by default; Kimi3 transition needs KIMI3_TRANSITION_ARMED=1. "
    "Metadata only; env-var names only; one bounded cycle; "
    "no adult scrape; no bulk chat upload; no infinite recursive loops."
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def vector_count(path: Path) -> int | None:
    if not path.is_file():
        return None
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        if "vectors" in doc:
            return len(doc.get("vectors") or [])
        return (doc.get("metrics") or {}).get("vector_count") or (
            doc.get("metrics") or {}
        ).get("corner_vector_sum")
    except (OSError, json.JSONDecodeError):
        return None


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

    vectors = vector_count(CATALOG)
    deepseek_vectors = vector_count(DEEPSEEK_CATALOG)
    grok_vectors = vector_count(GROK_CATALOG)
    corner_sum = vector_count(CORNER_CATALOG)
    discord_vectors = vector_count(DISCORD_CATALOG)
    kimi3_vectors = vector_count(KIMI3_CATALOG)
    central_sum = None
    if CENTRAL_CATALOG.is_file():
        try:
            doc = json.loads(CENTRAL_CATALOG.read_text(encoding="utf-8"))
            central_sum = (doc.get("metrics") or {}).get("vector_sum")
        except (OSError, json.JSONDecodeError):
            central_sum = None

    event = {
        "ts": utc_now(),
        "event": "asuna_point0_subagent_start",
        "subagent_type": sub_type,
        "task_len": len(task),
        "catalog_exists": CATALOG.is_file(),
        "vectors": vectors,
        "deepseek_catalog_exists": DEEPSEEK_CATALOG.is_file(),
        "deepseek_vectors": deepseek_vectors,
        "grok_catalog_exists": GROK_CATALOG.is_file(),
        "grok_vectors": grok_vectors,
        "corner_catalog_exists": CORNER_CATALOG.is_file(),
        "corner_vector_sum": corner_sum,
        "discord_catalog_exists": DISCORD_CATALOG.is_file(),
        "discord_vectors": discord_vectors,
        "kimi3_catalog_exists": KIMI3_CATALOG.is_file(),
        "kimi3_vectors": kimi3_vectors,
        "central_catalog_exists": CENTRAL_CATALOG.is_file(),
        "central_vector_sum": central_sum,
        "permission": "allow",
    }
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with TELEMETRY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass

    bits = []
    if vectors is not None:
        bits.append(f" Catalog vectors={vectors}.")
    if deepseek_vectors is not None:
        bits.append(f" DeepSeek vectors={deepseek_vectors}.")
    if grok_vectors is not None:
        bits.append(f" Grok vectors={grok_vectors}.")
    if corner_sum is not None:
        bits.append(f" Eastern white-moon sum={corner_sum}.")
    if discord_vectors is not None:
        bits.append(f" Discord vectors={discord_vectors}.")
    if kimi3_vectors is not None:
        bits.append(f" Kimi3 vectors={kimi3_vectors}.")
    if central_sum is not None:
        bits.append(f" Central vector_sum={central_sum}.")

    out = {
        "permission": "allow",
        "agent_message": ROUTE + "".join(bits),
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
