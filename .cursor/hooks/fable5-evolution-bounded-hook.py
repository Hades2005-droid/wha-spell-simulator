#!/usr/bin/env python3
"""Bounded Fable5 game-evolution hook — one cycle per invocation; no unbounded loops."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

WYILE = "ed8aa051-c53e-4a94-95be-9dc36dce1780"
CORE = "shadow-garden-core-0"
FORBIDDEN = (
    "recursive_improvement_ai_loop",
    "unbounded loop",
    "infinite improvement",
)


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    event = str(payload.get("hook_event_name") or payload.get("event") or "")
    prompt = str(payload.get("prompt") or payload.get("text") or "").lower()

    # Block shell that would start the forbidden unbounded loop
    if event in {"beforeShellExecution", "preToolUse"}:
        cmd = str(payload.get("command") or payload.get("tool_input") or "").lower()
        if "recursive_improvement_ai_loop" in cmd:
            print(
                json.dumps(
                    {
                        "permission": "deny",
                        "user_message": "Blocked: recursive_improvement_ai_loop is forbidden. Use one-cycle fable5-game-evolution-loop.",
                        "agent_message": "Deny unbounded recursive improvement; prefer shadow-garden-core-0 + one measurable cycle.",
                    }
                )
            )
            return 0

    context = (
        f"[{_utc()}] Fable5 bounded evolution armed. "
        f"core-0={CORE} wyile={WYILE} forever_phase=6. "
        "Contract: ONE cycle per invocation; max 3/session; "
        "Yin-driven-by-shadow / Yang-in-light; 21+ faculty sim only; "
        "improve persona classify speed/quality via allowlisted classifier; "
        "never run recursive_improvement_ai_loop; Discord LIVE double-gated; "
        "ask before another cycle. Prefer agent shadow-garden-core-0."
    )

    if any(f in prompt for f in FORBIDDEN):
        print(
            json.dumps(
                {
                    "continue": True,
                    "permission": "allow",
                    "agent_message": context
                    + " Prompt mentioned unbounded loop — rewrite to one measurable cycle.",
                    "additional_context": context,
                }
            )
        )
        return 0

    out: dict = {
        "continue": True,
        "permission": "allow",
        "agent_message": context,
        "additional_context": context,
        "env": {
            "FABLE5_EVOLUTION_BOUNDED": "1",
            "SHADOW_GARDEN_CORE_0": CORE,
            "SHADOW_GARDEN_WYILE": WYILE,
            "SHADOW_GARDEN_FOREVER_PHASE": "6",
        },
    }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
