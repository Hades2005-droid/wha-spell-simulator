#!/usr/bin/env python3
"""Passkeys Shared approval-gate hook — fail-closed for auto-bridge.

Reads ~/.cursor/passkeys/<gate_id>/gate.json when present.
When armed and admin_board_auto_connect_approved is false, deny shell/Task
paths that look like silent auto-connect / auto_bridge.

Legitimate user-gesture passkey work (Create Account / Sign In mentions without
auto-bridge verbs) is allowed; context is injected on sessionStart / triggers.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

AGENT = "passkeys-shared-approval-gate"
SAMPLE = "/Users/fredwashere/Downloads/ConnectingToAServiceWithPasskeys/Shared/"
GATE_ID = "shared-approval-gate.68821061-7-=3"
GATE_DIR = Path.home() / ".cursor" / "passkeys" / GATE_ID
GATE_JSON = GATE_DIR / "gate.json"

TRIGGERS = re.compile(
    r"(?i)\b("
    r"passkey|passkeys|webauthn|webcredentials|"
    r"accountmanager|sign\s*in\s*view\s*controller|"
    r"connectingtoaservicewithpasskeys|"
    r"auto[-_\s]?connect|auto[-_\s]?bridge|approval\s*gate|"
    r"white\s*moon|black\s*sun|eastern[-_\s]?white[-_\s]?moon"
    r")\b"
)

# Silent connector / bridge attempts (forbidden without board approval)
AUTO_BRIDGE = re.compile(
    r"(?i)("
    r"auto[-_]?connect|auto[-_]?bridge|silent[-_]?link|"
    r"without[-_]?approval|skip[-_]?approval|"
    r"admin_board_auto_connect_approved\s*=\s*true|"
    r"grantAdminBoardApproval|"
    r"preferImmediatelyAvailableCredentials\s*[:=]\s*true|"
    r"allowsLaunchAutoSignIn\s*[:=]\s*true"
    r")"
)


def _utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _load_gate() -> dict:
    """Fail-closed: missing/unreadable gate → treat as armed + unapproved."""
    try:
        if GATE_JSON.is_file():
            data = json.loads(GATE_JSON.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {
        "armed": True,
        "admin_board_auto_connect_approved": False,
        "default_policy": "deny",
        "gate_id": GATE_ID,
        "_load_error": True,
    }


def _auto_connect_allowed(gate: dict) -> bool:
    if not bool(gate.get("armed", True)):
        # Disarmed gate: still default deny auto-bridge unless explicitly approved
        return bool(gate.get("admin_board_auto_connect_approved")) is True
    return bool(gate.get("admin_board_auto_connect_approved")) is True


def _text_blob(payload: dict) -> str:
    parts = [
        str(payload.get("command") or ""),
        str(payload.get("prompt") or ""),
        str(payload.get("text") or ""),
        str(payload.get("tool_name") or ""),
        str(payload.get("tool_input") or ""),
        str(payload.get("subagent_type") or ""),
        str(payload.get("description") or ""),
    ]
    # Nested tool input (preToolUse / Task)
    ti = payload.get("tool_input")
    if isinstance(ti, dict):
        parts.append(json.dumps(ti, default=str))
    elif ti is not None and not isinstance(ti, str):
        parts.append(str(ti))
    return "\n".join(parts)


def _deny(msg_user: str, msg_agent: str) -> int:
    print(
        json.dumps(
            {
                "permission": "deny",
                "user_message": msg_user,
                "agent_message": msg_agent,
            }
        )
    )
    return 0


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        # Fail-closed for parse errors on gate-sensitive events is handled via
        # hooks.json failClosed; here allow so benign events are not hard-blocked.
        print(json.dumps({"continue": True, "permission": "allow"}))
        return 0

    if not isinstance(payload, dict):
        print(json.dumps({"continue": True, "permission": "allow"}))
        return 0

    event = str(payload.get("hook_event_name") or payload.get("event") or "")
    blob = _text_blob(payload)
    gate = _load_gate()
    approved = _auto_connect_allowed(gate)
    gate_id = str(gate.get("gate_id") or GATE_ID)

    context = (
        f"[{_utc()}] Passkeys Shared approval-gate `{gate_id}` "
        f"armed={bool(gate.get('armed'))} "
        f"admin_board_auto_connect_approved={approved}. "
        f"Prefer agent `{AGENT}`. Sample Shared/: `{SAMPLE}`. "
        "Policy: no silent auto-connect; board approval required before auto_bridge. "
        "User-gesture Create Account / Sign In OK. Do not force approval flags."
    )

    # Gate risky auto-bridge on shell / tool / subagent start
    if event in {
        "beforeShellExecution",
        "preToolUse",
        "subagentStart",
        "beforeSubmitPrompt",
    } and AUTO_BRIDGE.search(blob):
        if not approved:
            return _deny(
                (
                    "Denied: auto-connect / auto_bridge while PasskeyApprovalGate is "
                    f"armed and unapproved (`{gate_id}`). "
                    "Admin/board must set admin_board_auto_connect_approved=true "
                    "in gate.json only after explicit approval."
                ),
                (
                    f"Fail-closed passkeys gate. Use `{AGENT}`. "
                    "Do not flip approval flags. Keep auto_bridge blocked. "
                    "Legitimate path: user taps Create Account / Sign In in Shiny."
                ),
            )

    # subagentStart: always inject policy when this specialist starts
    subagent = str(payload.get("subagent_type") or "")
    if event == "subagentStart" and (
        subagent == AGENT or "passkeys" in subagent.lower()
    ):
        print(
            json.dumps(
                {
                    "permission": "allow",
                    "user_message": (
                        f"Passkeys gate `{gate_id}`: auto-connect "
                        f"{'ALLOWED' if approved else 'DENIED (fail-closed)'}."
                    ),
                    "agent_message": context,
                }
            )
        )
        return 0

    hit = bool(TRIGGERS.search(blob)) or event == "sessionStart"
    out: dict = {"continue": True, "permission": "allow"}
    if hit:
        out["additional_context"] = context
        out["agent_message"] = context
        out["env"] = {
            "PASSKEYS_APPROVAL_GATE": "1",
            "PASSKEYS_SHARED_SAMPLE": SAMPLE,
            "PASSKEYS_GATE_ID": gate_id,
            "PASSKEYS_GATE_ARMED": "1" if gate.get("armed") else "0",
            "PASSKEYS_AUTO_CONNECT_APPROVED": "1" if approved else "0",
            "PASSKEYS_PARALLEL_LANES": "white_moon,black_sun",
        }
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
