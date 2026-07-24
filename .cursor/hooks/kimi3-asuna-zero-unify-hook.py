#!/usr/bin/env python3
"""beforeSubmitPrompt / sessionStart: Kimi 3 → Asuna 0-point 3rd leverage.

Tags Kimi/Moonshot/local-open-weights-transition prompts. Metadata only.
Does NOT call Moonshot API or dump keys.
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
TELEMETRY = LOG_DIR / "kimi3_asuna_zero_unify.jsonl"
UNIFY_CLI = ROOT / "tools" / "kimi3_asuna_point0_unify.py"
CATALOG = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "kimi3_asuna_point0_unification.json"
)
CACHE_TTL_SEC = 3600

ASUNA_ZERO = {
    "point": 0,
    "label": "HOME",
    "archetype": "angela_asuna_home",
    "leverage": "kimi3_third_leverage",
    "transition": "local_open_weights_mesh",
    "carrier": "love_and_harmony_6",
    "bridge_signature": "f2e596cd043d6819",
}

TRIGGER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("kimi", re.compile(r"(?i)\bkimi\b|\bkimi\s*3\b|\bkimi-?k2\b")),
    ("moonshot", re.compile(r"(?i)\bmoonshot\b")),
    ("local_open_weights", re.compile(r"(?i)\blocal.?open.?weights\b|\btransition\b")),
    ("asuna_zero", re.compile(r"(?i)\basuna\b|\bpoint\s*0\b|\b0\s*point\b|\bpoint.?zero\b")),
    ("third_leverage", re.compile(r"(?i)\b3rd\s*leverage\b|\bthird\s*leverage\b")),
]

REFUSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "credential_harvest",
        re.compile(
            r"(?i)(?:print|dump|echo)\s+(?:my\s+)?(?:kimi|moonshot)?\s*(?:api\s*)?key|"
            r"harvest\s+(?:all\s+)?(?:kimi|moonshot)\s+(?:tokens?|keys?|credentials?)"
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
                    "transition_armed": (doc.get("metrics") or {}).get(
                        "transition_armed"
                    ),
                    "cached": True,
                    "path": str(CATALOG),
                }
        except (OSError, json.JSONDecodeError):
            pass
    if not UNIFY_CLI.is_file():
        return {"ok": False, "error": "missing kimi3_asuna_point0_unify.py"}
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
        "transition_armed": (doc.get("transition") or {}).get("armed")
        or (doc.get("metrics") or {}).get("transition_armed"),
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
                        "Blocked by Kimi3→Asuna-0 unify hook (secret_paste: "
                        f"{', '.join(secret_hits)}). Use env-var names only "
                        "($KIMI_API_KEY / $MOONSHOT_API_KEY)."
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
                            f"Blocked by Kimi3→Asuna-0 unify hook ({code}). "
                            "Env-var names only; metadata/path pointers only."
                        ),
                    }
                )
            )
            return 0

    tags = [name for name, pat in TRIGGER_PATTERNS if prompt and pat.search(prompt)]
    is_session = "session" in event_hint.lower() or not payload.get("prompt")
    should_refresh = is_session or bool(tags) or bool(
        re.search(
            r"(?i)kimi|moonshot|local.?open.?weights|3rd\s*leverage|third\s*leverage|asuna|unif|perplexity",
            prompt,
        )
    )

    catalog_summary: dict = {}
    if should_refresh:
        try:
            catalog_summary = refresh_catalog()
        except Exception as exc:  # noqa: BLE001
            catalog_summary = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:120]}

    event = {
        "ts": utc_now(),
        "event": "kimi3_asuna_zero_unify_tag",
        "tags": tags,
        "prompt_len": len(prompt),
        "catalog": catalog_summary,
        "asuna_zero": ASUNA_ZERO,
        "stream_mode": "metadata_only",
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
            "Kimi3→Perplexity Asuna 0-point 3rd leverage armed "
            f"(tags={', '.join(tags) or 'session'}; "
            f"vectors={catalog_summary.get('vectors', '?')}; "
            f"transition_armed={catalog_summary.get('transition_armed', False)}). "
            "Prefer: python3 tools/kimi3_asuna_point0_unify.py write → "
            "python3 tools/perplexity_asuna_central_control.py write. "
            "Completion bridge → local_open_weights_mesh; "
            "arm with $KIMI3_TRANSITION_ARMED=1 after approval. "
            "Prefer 127.0.0.1 Ollama; remote Moonshot opt-in only."
        )
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
