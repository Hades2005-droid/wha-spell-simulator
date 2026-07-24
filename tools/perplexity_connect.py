#!/usr/bin/env python3
"""
Perplexity auto-connect for WHA / Polymarket oracle work.

Uses certifi CA bundle to avoid macOS Python SSL issuer failures seen by MCP.
Never prints API key values — presence + health only.
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.perplexity_connect.v1"
DEFAULT_BASE = "https://api.perplexity.ai"
DEFAULT_MODEL = "sonar-pro"

ENV_NAMES = (
    "PERPLEXITY_API_KEY",
    "PPLX_API_KEY",
    "PERPLEXITY_BASE_URL",
    "PERPLEXITY_MODEL",
    "ENABLE_PERPLEXITY",
    "PERPLEXITY_LIVE_OK",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def ssl_context() -> ssl.SSLContext:
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:  # noqa: BLE001
        return ssl.create_default_context()


def api_key() -> str | None:
    for name in ("PERPLEXITY_API_KEY", "PPLX_API_KEY"):
        v = (os.environ.get(name) or "").strip()
        if v and not v.startswith("your-") and v not in {"changeme", "TODO"}:
            return v
    return None


def live_allowed() -> bool:
    # Auto-connect for research is allowed when key present OR explicit live gates.
    if api_key():
        return True
    return (
        os.environ.get("ENABLE_PERPLEXITY") == "1"
        and os.environ.get("PERPLEXITY_LIVE_OK") == "1"
    )


def health() -> dict[str, Any]:
    key = api_key()
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "ok": bool(key),
        "api_key_present": bool(key),
        "api_key_source": next(
            (n for n in ("PERPLEXITY_API_KEY", "PPLX_API_KEY") if os.environ.get(n)),
            None,
        ),
        "base_url": os.environ.get("PERPLEXITY_BASE_URL") or DEFAULT_BASE,
        "default_model": os.environ.get("PERPLEXITY_MODEL") or DEFAULT_MODEL,
        "live_allowed": live_allowed(),
        "ssl": "certifi_or_default",
        "env_names": list(ENV_NAMES),
        "auto_connect_for": [
            "polymarket_api_research",
            "entropy_oracle_hardening",
            "discord_status_notify_metadata",
        ],
        "controls": {
            "secret_logging": False,
            "content_neutral": True,
            "bulk_upload_requires_approval": True,
        },
    }


def chat(message: str, *, system: str | None = None, max_tokens: int = 1200) -> dict[str, Any]:
    key = api_key()
    if not key:
        return {
            "ok": False,
            "error": "missing_PERPLEXITY_API_KEY",
            "hint": "Export PERPLEXITY_API_KEY (never commit).",
        }
    base = (os.environ.get("PERPLEXITY_BASE_URL") or DEFAULT_BASE).rstrip("/")
    model = os.environ.get("PERPLEXITY_MODEL") or DEFAULT_MODEL
    body: dict[str, Any] = {
        "model": model,
        "messages": [],
        "max_tokens": max_tokens,
    }
    if system:
        body["messages"].append({"role": "system", "content": system})
    body["messages"].append({"role": "user", "content": message})
    req = urllib.request.Request(
        f"{base}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, context=ssl_context(), timeout=60) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", errors="replace")[:400]
        return {"ok": False, "error": f"http_{e.code}", "detail": detail}
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": "request_failed", "detail": str(e)}

    choices = payload.get("choices") if isinstance(payload, dict) else None
    text = ""
    if isinstance(choices, list) and choices:
        msg = choices[0].get("message") if isinstance(choices[0], dict) else {}
        text = str((msg or {}).get("content") or "")
    return {
        "ok": True,
        "model": model,
        "answer": text,
        "citations": payload.get("citations") if isinstance(payload, dict) else None,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Perplexity auto-connect (certifi SSL)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("health", help="Credential presence + SSL readiness")
    p_s = sub.add_parser("search", help="Sonar research query")
    p_s.add_argument("--query", required=True)
    p_s.add_argument("--max-tokens", type=int, default=1200)
    p_c = sub.add_parser("chat", help="Chat completion")
    p_c.add_argument("--message", required=True)
    p_c.add_argument("--system", default=None)
    p_c.add_argument("--max-tokens", type=int, default=1200)
    args = parser.parse_args(argv)

    if args.cmd == "health":
        doc = health()
        print(json.dumps(doc, indent=2))
        return 0 if doc.get("ok") else 1
    if args.cmd == "search":
        result = chat(
            args.query,
            system=(
                "You are a technical research assistant for Polymarket APIs and "
                "prediction-market data quality. Be precise; cite official docs when possible."
            ),
            max_tokens=args.max_tokens,
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    if args.cmd == "chat":
        result = chat(args.message, system=args.system, max_tokens=args.max_tokens)
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
