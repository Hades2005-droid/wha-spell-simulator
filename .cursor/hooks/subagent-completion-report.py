#!/usr/bin/env python3
"""subagentStop: append a local completion report (no auto follow-up loop)."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print("{}")
        return 0

    log_dir = Path(__file__).resolve().parent / "logs"
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        entry = {
            "recorded_at": datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z"),
            "hook_event_name": payload.get("hook_event_name") or "subagentStop",
            "status": payload.get("status"),
            "subagent_type": payload.get("subagent_type") or payload.get("type"),
            "task": payload.get("task") or payload.get("description"),
            "loop_count": payload.get("loop_count"),
            "conversation_id": payload.get("conversation_id"),
            "generation_id": payload.get("generation_id"),
        }
        log_path = log_dir / "subagent-stop.jsonl"
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
        latest = log_dir / "subagent-stop-latest.json"
        latest.write_text(json.dumps(entry, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    except OSError:
        # Observational only — never block subagent completion.
        pass

    # Do not set followup_message: Fable 5 / Shadow Garden policy is one cycle
    # unless the user explicitly asks for another.
    print("{}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
