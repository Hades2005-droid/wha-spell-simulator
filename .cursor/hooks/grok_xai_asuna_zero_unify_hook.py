#!/usr/bin/env python3
"""beforeSubmitPrompt / sessionStart: Grok/xAI → Asuna 0-point eastern white-moon.

Tags Grok/xAI/Harmony-6 prompts and reads the local Point-0 catalog via
tools/grok_xai_asuna_point0_unify.py (metadata only). Does NOT call api.x.ai
or dump keys. Cursor hook contract: JSON stdin → JSON stdout.
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
TELEMETRY = LOG_DIR / "grok_xai_asuna_zero_unify.jsonl"
UNIFY_CLI = ROOT / "tools" / "grok_xai_asuna_point0_unify.py"
CORNER_CLI = ROOT / "tools" / "white_moon_eastern_corner_unify.py"
CATALOG = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "grok_xai_asuna_point0_unification.json"
)
CACHE_TTL_SEC = 3600

ASUNA_ZERO = {
    "point": 0,
    "label": "HOME",
    "archetype": "angela_asuna_home",
    "corner": "eastern_white_moon",
    "carrier": "love_and_harmony_6",
    "bridge_signature": "f2e596cd043d6819",
}

TRIGGER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("grok", re.compile(r"(?i)\bgrok\b|\bxai\b|\bx\.ai\b")),
    ("white_moon", re.compile(r"(?i)\bwhite\s*moon\b|\beast(?:ern)?\s*(?:white\s*)?moon\b|\bmoon.?18\b")),
    ("harmony_6", re.compile(r"(?i)\bharmony.?6\b|\blove_and_harmony_6\b")),
    ("asuna_zero", re.compile(r"(?i)\basuna\b|\bpoint\s*0\b|\b0\s*point\b|\bpoint.?zero\b")),
    ("perplexity_unify", re.compile(r"(?i)\bperplexity\b|\bunif(?:y|ication)\b")),
]

REFUSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "credential_harvest",
        re.compile(
            r"(?i)(?:print|dump|echo)\s+(?:my\s+)?(?:xai|grok)?\s*(?:api\s*)?key|"
            r"harvest\s+(?:all\s+)?(?:xai|grok)\s+(?:tokens?|keys?|credentials?)"
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
                    "corner": (doc.get("corner") or {}).get("id"),
                    "cached": True,
                    "path": str(CATALOG),
                }
        except (OSError, json.JSONDecodeError):
            pass
    if not UNIFY_CLI.is_file():
        return {"ok": False, "error": "missing grok_xai_asuna_point0_unify.py"}
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
        "vectors": (doc.get("metrics") or {}).get("vector_count"),
        "corner": (doc.get("corner") or {}).get("id"),
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
                        "Blocked by Grok/xAI→Asuna-0 unify hook (secret_paste: "
                        f"{', '.join(secret_hits)}). Use env-var names only "
                        "($XAI_API_KEY / $GROK_TEXT_MODEL)."
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
                            f"Blocked by Grok/xAI→Asuna-0 unify hook ({code}). "
                            "Env-var names only; metadata/path pointers only."
                        ),
                    }
                )
            )
            return 0

    tags = [name for name, pat in TRIGGER_PATTERNS if prompt and pat.search(prompt)]
    is_session = "session" in event_hint.lower() or not payload.get("prompt")
    should_refresh = is_session or bool(tags) or bool(
        re.search(r"(?i)grok|xai|white.?moon|harmony.?6|asuna|unif|perplexity", prompt)
    )

    catalog_summary: dict = {}
    if should_refresh:
        try:
            catalog_summary = refresh_catalog()
        except Exception as exc:  # noqa: BLE001
            catalog_summary = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:120]}

    event = {
        "ts": utc_now(),
        "event": "grok_xai_asuna_zero_unify_tag",
        "tags": tags,
        "prompt_len": len(prompt),
        "catalog": catalog_summary,
        "asuna_zero": ASUNA_ZERO,
        "stream_mode": "metadata_only",
        "corner_cli": str(CORNER_CLI.name) if CORNER_CLI.is_file() else None,
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
            "Grok/xAI→Perplexity Asuna 0-point eastern white-moon armed "
            f"(tags={', '.join(tags) or 'session'}; "
            f"vectors={catalog_summary.get('vectors', '?')}; "
            f"corner={catalog_summary.get('corner', 'eastern_white_moon')}). "
            "Prefer: python3 tools/grok_xai_asuna_point0_unify.py write → "
            "python3 tools/white_moon_eastern_corner_unify.py write "
            "(weaves DeepSeek + Grok under Asuna Point-0). "
            "Remote xAI opt-in via $XAI_API_KEY only; no key dumps."
        )
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
