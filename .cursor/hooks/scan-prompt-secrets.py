#!/usr/bin/env python3
"""beforeSubmitPrompt: block prompts that appear to contain raw credentials."""

from __future__ import annotations

import json
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _secret_patterns import find_raw_secrets, unique  # noqa: E402

LOG_DIR = Path(__file__).resolve().parent / "logs"
BLOCK_LOG = LOG_DIR / "secret_paste_blocks.jsonl"

_REMEDIATION = (
    "Remove the secret *value* (any pplx-… / xai-… / sk-… token). "
    "Env-var *names* are fine: $PERPLEXITY_API_KEY, $XAI_API_KEY. "
    "Redacted placeholders are fine: pplx-[REDACTED], ***REDACTED***. "
    "Keys already live in ~/ShadowGarden/.env — tools load them automatically. "
    "Safe rephrase example: "
    "\"Run perplexity_mesh_adapter dry-run using $PERPLEXITY_API_KEY from env; do not echo the key.\""
)


def _log_block(hits: list[str], request_id: str, prompt_len: int) -> None:
    """Log block metadata only — never the prompt body or secret values."""
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        event = {
            "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            "event": "secret_paste_block",
            "request_id": request_id,
            "hits": hits,
            "prompt_len": prompt_len,
            "remediation": "use_env_var_names_only",
        }
        with BLOCK_LOG.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


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
        request_id = str(uuid.uuid4())
        _log_block(hits, request_id, len(prompt))
        print(
            json.dumps(
                {
                    "continue": False,
                    "user_message": (
                        "Blocked: this prompt looks like it contains a raw credential "
                        f"({', '.join(hits)}). {_REMEDIATION} "
                        f"Request ID: {request_id}"
                    ),
                }
            )
        )
        return 0

    print(json.dumps({"continue": True}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
