#!/usr/bin/env python3
"""
Polymarket entropy → local Qwen3:8B open-weights bridge (prep, not cutover).

Uses Google Drive legend catalyst (Qwen3-8B default) + Polymarket oracle sample
to build a local Ollama chat packet. Never arms KIMI3_TRANSITION_ARMED.
Live Polymarket requires ENABLE_POLYMARKET=1; live Ollama generate is opt-in
via --invoke-local (still loopback only).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.polymarket_qwen_open_weights_bridge.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
PREFERRED_MODEL = "qwen3:8b"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
DEFAULT_OUT = (
    WHA
    / "shadow_garden_handoff"
    / "bridges"
    / "polymarket_qwen_open_weights_bridge.json"
)
STATUS_OUT = Path("/tmp/shadow_garden_polymarket_qwen_open_weights_bridge.json")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def live_polymarket() -> bool:
    return os.environ.get("ENABLE_POLYMARKET") == "1" or os.environ.get(
        "POLYMARKET_LIVE_OK"
    ) == "1"


def probe_ollama_model(tag: str) -> dict[str, Any]:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    out: dict[str, Any] = {
        "host": host,
        "preferred": tag,
        "up": False,
        "tag_present": False,
        "qwen_tags": [],
    }
    try:
        req = urllib.request.Request(
            f"{host}/api/tags", headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            doc = json.loads(resp.read().decode("utf-8", errors="replace"))
        names = []
        for item in doc.get("models") or []:
            if isinstance(item, dict):
                name = str(item.get("name") or "").strip()
                if name:
                    names.append(name)
        out["up"] = True
        out["qwen_tags"] = [n for n in names if "qwen" in n.lower()]
        out["tag_present"] = tag in names or any(
            n.startswith(f"{tag}:") or n == tag for n in names
        )
        # Exact match preferred; also accept qwen3:8b variants
        if not out["tag_present"]:
            out["tag_present"] = any(
                n.split(":")[0] == "qwen3" and "8b" in n.lower() for n in names
            )
            if out["tag_present"]:
                out["resolved_tag"] = next(
                    n for n in names if n.split(":")[0] == "qwen3" and "8b" in n.lower()
                )
        else:
            out["resolved_tag"] = tag
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        out["error"] = type(exc).__name__
    return out


def run_polymarket_sample() -> dict[str, Any]:
    cli = WHA / "tools" / "polymarket_oracle.mjs"
    if not cli.is_file():
        return {"ok": False, "error": "missing_oracle_cli"}
    if not live_polymarket():
        return {
            "ok": False,
            "degraded": True,
            "error": "live_disabled",
            "hint": "Set ENABLE_POLYMARKET=1 for a live entropy sample",
        }
    env = os.environ.copy()
    env["ENABLE_POLYMARKET"] = "1"
    proc = subprocess.run(
        [
            "node",
            "--experimental-strip-types",
            str(cli),
            "sample",
            "--enrich-clob",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=str(WHA),
        env=env,
    )
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {
            "ok": False,
            "error": "sample_parse_failed",
            "exit": proc.returncode,
        }


def run_drive_legend() -> dict[str, Any]:
    script = WHA / "tools" / "google_drive_legend_catalyst.py"
    if not script.is_file():
        return {"ok": False, "error": "missing_drive_legend_cli"}
    proc = subprocess.run(
        [sys.executable, str(script), "write"],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        cwd=str(WHA),
    )
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"ok": False, "error": "legend_parse_failed", "exit": proc.returncode}


def build_prompt(sample: dict[str, Any], model: str) -> dict[str, Any]:
    probs = sample.get("probabilities") or []
    question = sample.get("question") or "(no market)"
    market_id = sample.get("marketId")
    bits = sample.get("entropyBits")
    seed = sample.get("seedHex") or ""
    system = (
        "You are the local open-weights orchestration layer for Shadow Garden. "
        "Stay content-neutral and technical. Use the Polymarket entropy sample "
        "only as structured probability / seed metadata — do not invent trades "
        "or place orders. Prefer local loopback tools."
    )
    user = (
        f"Preferred local model: {model}\n"
        f"Market id: {market_id}\n"
        f"Question: {question}\n"
        f"Probabilities: {probs}\n"
        f"Entropy bits: {bits}\n"
        f"Seed hex (first 16): {seed[:16]}\n"
        f"Quality: {json.dumps(sample.get('quality') or {}, sort_keys=True)}\n\n"
        "Task: propose a short local-only sim routing note (JSON keys: "
        "route, seed_use, risk_flags, next_local_step). No remote calls."
    )
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "stream": False,
        "options": {"temperature": 0.2},
    }


def invoke_ollama(packet: dict[str, Any]) -> dict[str, Any]:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    body = json.dumps(packet).encode("utf-8")
    req = urllib.request.Request(
        f"{host}/api/chat",
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            doc = json.loads(resp.read().decode("utf-8", errors="replace"))
        msg = (doc.get("message") or {}) if isinstance(doc, dict) else {}
        return {
            "ok": True,
            "model": doc.get("model") if isinstance(doc, dict) else packet.get("model"),
            "content": msg.get("content"),
            "done": doc.get("done") if isinstance(doc, dict) else None,
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": type(exc).__name__, "detail": str(exc)[:200]}


def build(*, invoke_local: bool = False, force_sample: bool = False) -> dict[str, Any]:
    legend = run_drive_legend()
    ollama = probe_ollama_model(PREFERRED_MODEL)
    model = ollama.get("resolved_tag") or PREFERRED_MODEL
    sample: dict[str, Any]
    if force_sample or live_polymarket():
        sample = run_polymarket_sample()
    else:
        sample = {
            "ok": False,
            "degraded": True,
            "error": "live_disabled",
            "schema": "shadow_garden.polymarket_entropy_sample.v1",
        }

    chat_packet = build_prompt(sample if isinstance(sample, dict) else {}, model)
    invocation = None
    if invoke_local:
        if not ollama.get("up") or not ollama.get("tag_present"):
            invocation = {
                "ok": False,
                "error": "ollama_or_qwen_tag_missing",
                "ollama": ollama,
            }
        elif not sample.get("ok") and not sample.get("degraded"):
            invocation = {"ok": False, "error": "no_entropy_sample"}
        else:
            invocation = invoke_ollama(chat_packet)

    payload = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "phase": "prepare",
        "lane": {
            "id": "polymarket_to_qwen3_8b_local",
            "from": "polymarket_entropy_oracle",
            "to": "local_open_weights_qwen3_8b",
            "catalyst": "google_drive_legend_catalyst_3",
            "cutover_gate": "KIMI3_TRANSITION_ARMED",
            "armed": False,
        },
        "preferred_model": PREFERRED_MODEL,
        "resolved_model": model,
        "drive_legend": {
            "ok": bool(legend.get("ok")),
            "qwen_default": (legend.get("legend") or {}).get("qwen_default"),
            "mcp_note": ((legend.get("legend") or {}).get("mcp") or {}).get("note"),
        },
        "ollama": ollama,
        "entropy_sample": {
            "ok": bool(sample.get("ok")),
            "degraded": bool(sample.get("degraded")),
            "marketId": sample.get("marketId"),
            "question": sample.get("question"),
            "entropyBits": sample.get("entropyBits"),
            "seedHex16": (sample.get("seedHex") or "")[:16] or None,
            "error": sample.get("error"),
            "quality_ok": (sample.get("quality") or {}).get("ok"),
        },
        "chat_packet": chat_packet,
        "invocation": invocation,
        "controls": {
            "provider_calls": False,
            "remote_default": False,
            "kimi3_transition_armed": os.environ.get("KIMI3_TRANSITION_ARMED") == "1",
            "polymarket_live": live_polymarket(),
            "invoke_local": bool(invoke_local),
            "content_neutral": True,
            "secrets_in_artifacts": False,
        },
        "cli": {
            "write": "python3 tools/polymarket_qwen_open_weights_bridge.py write",
            "status": "python3 tools/polymarket_qwen_open_weights_bridge.py status",
            "invoke": (
                "ENABLE_POLYMARKET=1 python3 tools/polymarket_qwen_open_weights_bridge.py "
                "write --invoke-local"
            ),
            "drive_legend": "python3 tools/google_drive_legend_catalyst.py write",
            "mesh_prep": "python3 tools/local_open_weights_mesh_prep.py write",
        },
    }
    payload["ok"] = bool(ollama.get("up") and legend.get("ok") and ollama.get("tag_present"))
    payload["metrics"] = {
        "vector_count": 6,
        "ollama_up": bool(ollama.get("up")),
        "qwen8b_present": bool(ollama.get("tag_present")),
        "legend_ok": bool(legend.get("ok")),
        "sample_ok": bool(sample.get("ok")),
        "prep_ready": bool(
            ollama.get("up") and ollama.get("tag_present") and legend.get("ok")
        ),
        "cutover_ready": False,
    }
    return payload


def write_outputs(payload: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for path in (STATUS_OUT, DEFAULT_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Polymarket → Qwen3:8B local open-weights bridge"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test"],
    )
    parser.add_argument(
        "--invoke-local",
        action="store_true",
        help="POST chat packet to local Ollama (127.0.0.1 only)",
    )
    parser.add_argument(
        "--force-sample",
        action="store_true",
        help="Attempt Polymarket sample even if ENABLE_POLYMARKET unset",
    )
    args = parser.parse_args(argv)
    payload = build(invoke_local=args.invoke_local, force_sample=args.force_sample)
    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": payload.get("ok"),
                    "lane": payload.get("lane"),
                    "resolved_model": payload.get("resolved_model"),
                    "metrics": payload.get("metrics"),
                    "controls": payload.get("controls"),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload["schema"] == SCHEMA
        assert payload["preferred_model"] == PREFERRED_MODEL
        assert payload["metrics"]["cutover_ready"] is False
        assert payload["lane"]["armed"] is False
        print(json.dumps({"ok": True, "metrics": payload["metrics"]}, indent=2))
        return 0 if payload.get("ok") else 1
    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
