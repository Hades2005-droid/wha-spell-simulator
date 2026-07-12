#!/usr/bin/env python3
"""beforeShellExecution: block commands with raw secrets or credential dumps."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _secret_patterns import find_shell_secret_risks, unique  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"permission": "allow"}))
        return 0

    command = payload.get("command") or ""
    if not isinstance(command, str):
        command = str(command)

    hits = unique(find_shell_secret_risks(command))
    if hits:
        print(
            json.dumps(
                {
                    "permission": "deny",
                    "user_message": (
                        "Blocked shell command: apparent raw secret or credential-store "
                        f"dump ({', '.join(hits)}). Use environment variables "
                        "(e.g. \"$XAI_API_KEY\") and never echo/cat auth files or .env "
                        "contents into the terminal."
                    ),
                    "agent_message": (
                        "A secrets hook denied this shell command. Rephrase without "
                        "embedding credential values; reference env vars by name only."
                    ),
                }
            )
        )
        return 0

    print(json.dumps({"permission": "allow"}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
