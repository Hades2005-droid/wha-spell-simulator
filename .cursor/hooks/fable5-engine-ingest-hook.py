#!/usr/bin/env python3
"""beforeSubmitPrompt companion: Fable5 / Yang / King-Jing technical ingest tags.

Does NOT scrape adult sites, X timelines, or reverse secret-scan polarity.
Does: tag prompts for Shadow Garden engine pathways and append metadata-only
telemetry for Fable5 / spacetime / Jing / local portal routes.

Cursor hook contract: read JSON on stdin, print JSON on stdout.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Pathway tags for Fable5 engine effectiveness (technical only)
PATHWAY_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("fable5", re.compile(r"(?i)\bfable\s*5\b|\bfable5\b")),
    ("yang", re.compile(r"(?i)\byang\b|solar.?yang|est\b")),
    ("yin", re.compile(r"(?i)\byin\b|sgt\b|singapore")),
    ("king_jing", re.compile(r"(?i)\bking\s*jing\b|\bjing\s*power\b|\bjing\b")),
    ("spacetime", re.compile(r"(?i)\bspacetime|wallfacer|micro|macro|sovereign\s*prime")),
    ("shadow_content", re.compile(r"(?i)\bshadow\s*(garden|content|session)\b")),
    ("perplexity", re.compile(r"(?i)\bperplexity\b|\bfable5.?space\b|\bsonar\b")),
    ("comet", re.compile(r"(?i)\bcomet\b")),
    ("x_public", re.compile(r"(?i)\bx\.com\b|\btwitter\b")),  # tag only — no scrape
    ("claude", re.compile(r"(?i)\bclaude\b|\bblack\s*sun\b")),
    ("grok", re.compile(r"(?i)\bgrok\b|\bxai\b")),
    ("comfyui", re.compile(r"(?i)\bcomfyui?\b")),
    ("eden", re.compile(r"(?i)\beden\b|\bburst.?alpha\b")),
    ("persona", re.compile(r"(?i)\bpersona\b|\bangela\b|\bsue\b|\baddie\b")),
]

# Hard refuse markers (adult scrape / reverse-safety jailbreaks)
REFUSE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "adult_site_html_ingest",
        re.compile(r"(?i)xvideos\.com|pornhub\.com|xvideos-cdn|squirts?\s+all\s+over"),
    ),
    (
        "reverse_safety_jailbreak",
        re.compile(
            r"(?i)reverse\s+the\s+polarity|absolute\s+obedience|"
            r"disable\s+(?:safety|guardrails|secret.?scan)|"
            r"everything\s+this\s+code\s+says\s+it\s+won.?t\s+do"
        ),
    ),
]

LOG_DIR = Path(__file__).resolve().parent / "logs"
TELEMETRY = LOG_DIR / "fable5_engine_ingest.jsonl"

# Shared secret detector (same as scan-prompt-secrets) — env names OK, raw tokens not.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _secret_patterns import find_raw_secrets, unique  # noqa: E402


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        print(json.dumps({"continue": True}))
        return 0

    prompt = payload.get("prompt") or ""
    if not isinstance(prompt, str):
        prompt = str(prompt)

    # Secret paste: use shared patterns (allows redacted fixtures / env names).
    secret_hits = unique(find_raw_secrets(prompt))
    if secret_hits:
        print(
            json.dumps(
                {
                    "continue": False,
                    "user_message": (
                        "Blocked by Fable5 engine ingest hook (secret_paste: "
                        f"{', '.join(secret_hits)}). "
                        "Do not paste raw pplx-/xai-/sk- values. "
                        "Use $PERPLEXITY_API_KEY / $XAI_API_KEY (already in ~/ShadowGarden/.env). "
                        "Technical Fable5/spacetime/Jing pathways + non-explicit scene plans only."
                    ),
                }
            )
        )
        return 0

    for code, pat in REFUSE_PATTERNS:
        if pat.search(prompt):
            print(
                json.dumps(
                    {
                        "continue": False,
                        "user_message": (
                            f"Blocked by Fable5 engine ingest hook ({code}). "
                            "Adult-site HTML dumps, reverse-safety/jailbreak polarity, "
                            "and raw API keys are not accepted. "
                            "Use technical Fable5/spacetime/Jing pathways, "
                            "env-only credentials, and non-explicit scene plans only."
                        ),
                    }
                )
            )
            return 0

    pathways = [name for name, pat in PATHWAY_PATTERNS if pat.search(prompt)]
    event = {
        "ts": utc_now(),
        "event": "fable5_engine_ingest_tag",
        "pathways": pathways,
        "prompt_len": len(prompt),
        "engine_routes": {
            "fable5_ui": "http://127.0.0.1:5619/",
            "eden": "http://127.0.0.1:8791/",
            "comfyui": "http://127.0.0.1:8189/",
            "portal": "http://127.0.0.1:8760/",
            "bedrock": "~/ShadowGarden/live/spacetime_alchemy/PERPLEXITY_CONTEXT_BEDROCK.md",
            "compact": "~/ShadowGarden/live/spacetime_alchemy/fable5-compact.json",
            "jing": "python3 -m spacetime_alchemy.jing_power_monitor --once",
            "packet": "python3 tools/shadow_garden_packet.py write",
            "phase2": "python3 tools/black_sun_phase2_engine.py self-test",
        },
        "stream_mode": "metadata_only",
        "scrapes_x": False,
        "scrapes_adult_sites": False,
        "polarity": "safety_enforced_not_reversed",
    }

    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        with TELEMETRY.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass

    # Always continue after tagging (secrets already handled by scan-prompt-secrets)
    out: dict = {"continue": True}
    if pathways:
        out["agent_message"] = (
            "Fable5 engine pathways tagged: "
            + ", ".join(pathways)
            + ". Prefer local routes (5619/8791/8189/8760) + compact/bedrock; "
            "no adult scrape; secrets env-only."
        )
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
