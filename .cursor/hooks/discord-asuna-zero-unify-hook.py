#!/usr/bin/env python3
"""beforeSubmitPrompt / sessionStart: Discord → Asuna 0-point status_notify unify.

Tags Discord prompts; reads local Point-0 catalog. Does NOT post webhooks or
dump tokens. Cursor hook contract: JSON stdin → JSON stdout.
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
TELEMETRY = LOG_DIR / "discord_asuna_zero_unify.jsonl"
UNIFY_CLI = ROOT / "tools" / "discord_asuna_point0_unify.py"
CATALOG = (
    ROOT
    / "shadow_garden_handoff"
    / "bridges"
    / "discord_asuna_point0_unification.json"
)
CACHE_TTL_SEC = 3600

ASUNA_ZERO = {
    "point": 0,
    "label": "HOME",
    "archetype": "angela_asuna_home",
    "lane": "discord_status_notify",
    "carrier": "love_and_harmony_6",
    "bridge_signature": "f2e596cd043d6819",
}

TRIGGER_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("discord", re.compile(r"(?i)\bdiscord\b|\bwebhook\b")),
    ("status_notify", re.compile(r"(?i)\bstatus.?notify\b|\bping\b")),
    ("asuna_zero", re.compile(r"(?i)\basuna\b|\bpoint\s*0\b|\b0\s*point\b|\bpoint.?zero\b")),
    ("perplexity_unify", re.compile(r"(?i)\bperplexity\b|\bunif(?:y|ication)\b|\bcentral.?control\b")),
]

REFUSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "credential_harvest",
        re.compile(
            r"(?i)(?:print|dump|echo)\s+(?:my\s+)?(?:discord)?\s*(?:bot\s*)?(?:token|webhook)|"
            r"harvest\s+(?:all\s+)?discord\s+(?:tokens?|webhooks?|credentials?)"
        ),
    ),
    (
        "channel_scrape",
        re.compile(
            r"(?i)(?:scrape|dump|exfil).*(?:discord\s+)?(?:channel|guild)\s+history|"
            r"mass.?download\s+discord\s+messages"
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
                    "effective_state": (doc.get("metrics") or {}).get("effective_state"),
                    "cached": True,
                    "path": str(CATALOG),
                }
        except (OSError, json.JSONDecodeError):
            pass
    if not UNIFY_CLI.is_file():
        return {"ok": False, "error": "missing discord_asuna_point0_unify.py"}
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
        "effective_state": (doc.get("metrics") or {}).get("effective_state"),
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
                        "Blocked by Discord→Asuna-0 unify hook (secret_paste: "
                        f"{', '.join(secret_hits)}). Use env-var names only "
                        "($DISCORD_BOT_TOKEN / $DISCORD_WEBHOOK_URL)."
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
                            f"Blocked by Discord→Asuna-0 unify hook ({code}). "
                            "No token dumps or channel scrapes. "
                            "Metadata/path pointers only; default PAUSED."
                        ),
                    }
                )
            )
            return 0

    tags = [name for name, pat in TRIGGER_PATTERNS if prompt and pat.search(prompt)]
    is_session = "session" in event_hint.lower() or not payload.get("prompt")
    should_refresh = is_session or bool(tags) or bool(
        re.search(r"(?i)discord|webhook|status.?notify|asuna|unif|perplexity|central", prompt)
    )

    catalog_summary: dict = {}
    if should_refresh:
        try:
            catalog_summary = refresh_catalog()
        except Exception as exc:  # noqa: BLE001
            catalog_summary = {"ok": False, "error": f"{type(exc).__name__}: {exc}"[:120]}

    event = {
        "ts": utc_now(),
        "event": "discord_asuna_zero_unify_tag",
        "tags": tags,
        "prompt_len": len(prompt),
        "catalog": catalog_summary,
        "asuna_zero": ASUNA_ZERO,
        "stream_mode": "metadata_only",
        "webhook_post": False,
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
            "Discord→Perplexity Asuna 0-point status_notify armed "
            f"(tags={', '.join(tags) or 'session'}; "
            f"vectors={catalog_summary.get('vectors', '?')}; "
            f"state={catalog_summary.get('effective_state', 'PAUSED')}). "
            "Prefer: python3 tools/discord_asuna_point0_unify.py write → "
            "python3 tools/perplexity_asuna_central_control.py write. "
            "Default PAUSED; live ping needs ENABLE_DISCORD=1 + DISCORD_LIVE_OK=1. "
            "No channel scrapes; env-var names only."
        )
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
