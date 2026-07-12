#!/usr/bin/env python3
"""beforeSubmitPrompt: block prompts that appear to contain raw credentials."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _secret_patterns import find_raw_secrets, unique  # noqa: E402


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        # fail open (hooks.json failClosed=false)
        print(json.dumps({"continue": True}))
        return 0

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str):
        prompt = str(prompt)

    hits = unique(find_raw_secrets(prompt))
    if hits:
        print(
            json.dumps(
                {
                    "continue": False,
                    "user_message": (
                        "Blocked: this prompt looks like it contains a raw credential "
                        f"({', '.join(hits)}). Remove the secret value and use an "
                        "environment variable or Cursor secret instead "
                        "(e.g. $XAI_API_KEY). Env-var *names* and redacted placeholders "
                        "are fine."
                    ),
                }
            )
        )
        return 0

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
