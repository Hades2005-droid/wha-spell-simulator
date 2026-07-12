#!/usr/bin/env python3
"""Local self-test for secrets hooks (does not print raw secrets to stdout)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HOOKS = Path(__file__).resolve().parent


def run(script: str, payload: dict) -> dict:
    proc = subprocess.run(
        [sys.executable, str(HOOKS / script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    return json.loads(proc.stdout)


def main() -> int:
    # Safe: env-name only
    out = run("scan-prompt-secrets.py", {"prompt": "use $XAI_API_KEY and LINEAR_API_KEY"})
    assert out.get("continue") is True, out

    # Fake raw key — constructed so this source file itself is less grep-noisy
    fake_pplx = "pplx-" + ("a" * 24)
    out = run("scan-prompt-secrets.py", {"prompt": f"key={fake_pplx}"})
    assert out.get("continue") is False, out

    out = run("scan-shell-secrets.py", {"command": 'printf "%s" "$XAI_API_KEY" | wc -c'})
    assert out.get("permission") == "allow", out

    out = run("scan-shell-secrets.py", {"command": "cat ~/.grok/auth.json"})
    assert out.get("permission") == "deny", out

    fake_xai = "xai-" + ("b" * 24)
    out = run(
        "scan-shell-secrets.py",
        {"command": f"export XAI_API_KEY={fake_xai}"},
    )
    assert out.get("permission") == "deny", out

    out = run(
        "subagent-completion-report.py",
        {
            "status": "completed",
            "subagent_type": "explore",
            "task": "mesh scan",
            "loop_count": 0,
        },
    )
    assert out == {}, out
    latest = HOOKS / "logs" / "subagent-stop-latest.json"
    assert latest.is_file(), latest

    print("hooks selftest OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
