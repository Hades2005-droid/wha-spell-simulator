#!/usr/bin/env python3
"""beforeSubmitPrompt / sessionStart: DeepSeek → Perplexity Asuna 0-point unify.

Tags DeepSeek/Ollama/local-open-weights prompts and reads the local Point-0
catalog via tools/deepseek_asuna_point0_unify.py (metadata only).

Does NOT: call remote DeepSeek API, dump keys, bulk-copy private chats.
Cursor hook contract: read JSON on stdin, print JSON on stdout.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOKS = Path(__file__).resolve().parent
ROOT = HOOKS.parents[1]
LOG_DIR = HOOKS / "logs"
TELEMETRY = LOG_DIR / "deepseek_asuna_zero_unify.jsonl"
UNIFY_CLI = ROOT / "tools" / "deepseek_asuna_point0_unify.py"
CATALOG = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "deepseek_asuna_point0_unification.json"
)
CACHE_TTL_SEC = 3600

ASUNA_ZERO = {
    "point": 0,
    "label": "HOME",
    "archetype": "angela_asuna_home",
    "protector": "KIRITO_FRED",
    "scene_id": "kitchen_log_cabin_floor_22",
    "carrier": "love_and_harmony_6",
    "bridge_signature": "f2e596cd043d6819",
}

TRIGGER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("deepseek", re.compile(r"(?i)\bdeepseek\b")),
    ("ollama", re.compile(r"(?i)\bollama\b|\b11434\b")),
    ("local_open_weights", re.compile(r"(?i)\blocal.?open.?weights\b|\bdeepseek.?local\b")),
    ("asuna_zero", re.compile(r"(?i)\basuna\b|\bpoint\s*0\b|\b0\s*point\b|\bpoint.?zero\b")),
    ("perplexity_unify", re.compile(r"(?i)\bperplexity\b|\bunif(?:y|ication)\b|\bfable5.?space\b")),
]

REFUSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "bulk_chat_upload",
        re.compile(
            r"(?i)(?:bulk|mass)\s+(?:upload|dump|exfil).*(?:deepseek|chat|transcript)|"
            r"(?:upload|dump).*(?:all\s+)?(?:private\s+)?(?:deepseek\s+)?chats?\s+to\s+perplexity"
        ),
    ),
    (
        "credential_harvest",
        re.compile(
            r"(?i)(?:print|dump|echo)\s+(?:my\s+)?(?:deepseek|ollama)?\s*(?:api\s*)?key|"
            r"harvest\s+(?:all\s+)?deepseek\s+(?:tokens?|keys?|credentials?)"
        ),
    ),
]

sys.path.insert(0, str(HOOKS))
from _secret_patterns import find_raw_secrets, unique  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def refresh_catalog() -> dict:
    if CATALOG.is_file():
        try:
            age = datetime.now(timezone.utc).timestamp() - CATALOG.stat().st_mtime
            if age < CACHE_TTL_SEC:
                doc = json.loads(CATALOG.read_text(encoding="utf-8"))
                return {
                    "ok": bool(doc.get("ok")),
                    "vectors": len(doc.get("vectors") or []),
                    "provider_calls": (doc.get("metrics") or {}).get("provider_calls"),
                    "ollama_up": (doc.get("metrics") or {}).get("ollama_up"),
                    "cached": True,
                    "path": str(CATALOG),
                }
        except (OSError, json.JSONDecodeError):
            pass
    if not UNIFY_CLI.is_file():
        return {"ok": False, "error": "missing deepseek_asuna_point0_unify.py"}
    try:
        proc = subprocess.run(
            [sys.executable, str(UNIFY_CLI), "status"],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
            cwd=str(ROOT),
        )
    except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:120]}
    try:
        doc = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        doc = {}
    return {
        "ok": proc.returncode == 0 and bool(doc.get("ok", True)),
        "exit": proc.returncode,
        "vectors": len(doc.get("vectors") or []),
        "provider_calls": (doc.get("metrics") or {}).get("provider_calls"),
        "ollama_up": (doc.get("metrics") or {}).get("ollama_up"),
        "cached": False,
        "path": str(CATALOG),
    }


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str):
        prompt = str(prompt)
    event_hint = str(payload.get("hook_event_name") or payload.get("event") or "")

    secret_hits = unique(find_raw_secrets(prompt)) if prompt else []
    if secret_hits:
        print(
            json.dumps(
                {
                    "continue": False,
                    "user_message": (
                        "Blocked by DeepSeek→Asuna-0 unify hook (secret_paste: "
                        f"{', '.join(secret_hits)}). Use env-var names only "
                        "($DEEPSEEK_API_KEY / $OLLAMA_HOST)."
                    ),
                }
            )
        )
        return 0

    for code, pat in REFUSE_PATTERNS:
        if prompt and pat.search(prompt):
            print(
                json.dumps(
                    {
                        "continue": False,
                        "user_message": (
                            f"Blocked by DeepSeek→Asuna-0 unify hook ({code}). "
                            "No bulk chat upload or credential harvesting. "
                            "Metadata/path pointers only."
                        ),
                    }
                )
            )
            return 0

    tags = [name for name, pat in TRIGGER_PATTERNS if prompt and pat.search(prompt)]
    is_session = "session" in event_hint.lower() or not payload.get("prompt")
    should_refresh = is_session or bool(tags) or bool(
        re.search(r"(?i)deepseek|ollama|open.?weights|asuna|unif|perplexity", prompt)
    )

    catalog_summary: dict = {}
    if should_refresh:
        try:
            catalog_summary = refresh_catalog()
        except Exception as exc:  # noqa: BLE001
            catalog_summary = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:120]}

    event = {
        "ts": utc_now(),
        "event": "deepseek_asuna_zero_unify_tag",
        "tags": tags,
        "prompt_len": len(prompt),
        "catalog": catalog_summary,
        "asuna_zero": ASUNA_ZERO,
        "preferred_route": "http://127.0.0.1:11434",
        "remote_api": "opt_in_via_DEEPSEEK_API_KEY",
        "stream_mode": "metadata_only",
        "bulk_chat_copy": False,
    }
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with TELEMETRY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass

    out: dict = {"continue": True}
    if tags or is_session or catalog_summary:
        out["agent_message"] = (
            "DeepSeek→Perplexity Asuna 0-point unify armed "
            f"(tags={', '.join(tags) or 'session'}; "
            f"vectors={catalog_summary.get('vectors', '?')}; "
            f"ollama_up={catalog_summary.get('ollama_up', '?')}; "
            f"provider_calls={catalog_summary.get('provider_calls', '?')}). "
            f"Anchor: Asuna HOME point-0 ({ASUNA_ZERO['scene_id']}). "
            "Prefer: 127.0.0.1:11434 Ollama → deepseek_asuna_point0_unification.json → "
            "python3 tools/deepseek_asuna_point0_unify.py write. "
            "Remote DeepSeek API opt-in via $DEEPSEEK_API_KEY only; no bulk chat upload."
        )
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
