#!/usr/bin/env python3
"""Passkeys Shared approval-gate hook — parallel to white moon / black sun.

Injects context when prompts mention passkeys / Shared / auto-connect.
Asks before shell that looks like silent auto-bridge wiring.
Fail-open except intentional deny for recursive unbounded loops (handled elsewhere).
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone

AGENT = "passkeys-shared-approval-gate"
SAMPLE = "/Users/fredwashere/Downloads/ConnectingToAServiceWithPasskeys/Shared/"

TRIGGERS = re.compile(
    r"(?i)\b("
    r"passkey|passkeys|webauthn|webcredentials|"
    r"accountmanager|sign\s*in\s*view\s*controller|"
    r"connectingtoaservicewithpasskeys|"
    r"auto[-_\s]?connect|auto[-_\s]?bridge|approval\s*gate|"
    r"white\s*moon|black\s*sun|eastern[-_\s]?white[-_\s]?moon"
    r")\b"
)

AUTO_BRIDGE_SHELL = re.compile(
    r"(?i)("
    r"auto[-_]?connect|auto[-_]?bridge|silent[-_]?link|"
    r"without[-_]?approval|skip[-_]?approval"
    r")"
)


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        print(json.dumps({"continue": True}))
        return 0

    event = str(payload.get("hook_event_name") or payload.get("event") or "")
    prompt = str(payload.get("prompt") or payload.get("text") or "")
    command = str(payload.get("command") or "")

    context = (
        f"[{_utc()}] Passkeys Shared approval-gate armed (parallel white moon / black sun). "
        f"Prefer agent `{AGENT}`. Sample Shared/: `{SAMPLE}`. "
        "Policy: no silent auto-connect; admin/board approval required before any "
        "auto-bridge; LaunchScreen=0 blank is OK; keep Base.lproj assets unless user "
        "asks to strip. Env-var names only for secrets. Discord LIVE still double-gated."
    )

    # Gate risky shell that tries to force auto-connect without approval
    if event in {"beforeShellExecution", "preToolUse"} and AUTO_BRIDGE_SHELL.search(
        command
    ):
        print(
            json.dumps(
                {
                    "permission": "ask",
                    "user_message": (
                        "This command looks like an auto-connect / auto-bridge path. "
                        "Passkeys Shared policy requires explicit admin/board approval."
                    ),
                    "agent_message": (
                        "Ask user before silent connector wiring. Use "
                        f"`{AGENT}`; default deny/off for auto_bridge."
                    ),
                }
            )
        )
        return 0

    hit = bool(TRIGGERS.search(prompt)) or event == "sessionStart"
    out: dict = {"continue": True, "permission": "allow"}
    if hit or TRIGGERS.search(command):
        out["additional_context"] = context
        out["agent_message"] = context
        out["env"] = {
            "PASSKEYS_APPROVAL_GATE": "1",
            "PASSKEYS_SHARED_SAMPLE": SAMPLE,
            "PASSKEYS_PARALLEL_LANES": "white_moon,black_sun",
        }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
