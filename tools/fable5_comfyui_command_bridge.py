#!/usr/bin/env python3
"""
Local Fable 5 + ComfyUI command bridge.

Indexes only explicit allowlisted pointers, compiles a deterministic status
pack (schema shadow_garden.integration_repo_roots.v1), and optionally probes
localhost HTTP. Never reads or writes secret values.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
HOME = Path.home()
DEFAULT_OUTBOX = ROOT / "shadow_garden_handoff" / "terminal_auto" / "outbox"
DEFAULT_TMP = Path("/tmp/shadow_garden_fable5_comfyui_bridge_status.json")

# Allowlisted local roots (no home-wide crawl).
REPO_ROOTS: list[dict[str, str]] = [
    {"id": "wha_spell_simulator", "path": str(ROOT), "role": "spell_compiler_bridge"},
    {
        "id": "shadow_garden",
        "path": str(HOME / "ShadowGarden"),
        "role": "hub_spacetime_export",
    },
    {
        "id": "shadow_garden_mesh",
        "path": str(HOME / "shadow_garden_mesh"),
        "role": "github_help_mesh",
    },
    {
        "id": "monitoring",
        "path": str(HOME / "shadow_garden_may30_monitoring"),
        "role": "daemons_fable5_server",
    },
    {
        "id": "gitmynotes",
        "path": str(HOME / "shadow_garden_mesh" / "gitmynotes"),
        "role": "notes_asana",
    },
    {
        "id": "flux_klein_local",
        "path": str(HOME / "shadow_garden_mesh" / "flux_klein_local"),
        "role": "image_hud",
    },
]

COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8188").rstrip("/")
_comfyui_endpoint = urlparse(COMFYUI_URL)
COMFYUI_PORT = _comfyui_endpoint.port or (
    443 if _comfyui_endpoint.scheme == "https" else 80
)

LOCAL_SERVICES: list[dict[str, Any]] = [
    {"id": "fable5_game", "url": "http://127.0.0.1:5619/", "port": 5619},
    {"id": "comfyui", "url": f"{COMFYUI_URL}/", "port": COMFYUI_PORT},
    {
        "id": "comfyui_system_stats",
        "url": f"{COMFYUI_URL}/system_stats",
        "port": COMFYUI_PORT,
    },
    {"id": "eden_burst_alpha", "url": "http://127.0.0.1:8791/", "port": 8791},
    {"id": "void_ignition", "url": "http://127.0.0.1:8790/api/health", "port": 8790},
    {"id": "ollama", "url": "http://127.0.0.1:11434/api/tags", "port": 11434},
]

POINTERS: dict[str, str] = {
    "fable5_compact": str(
        HOME / "ShadowGarden" / "live" / "spacetime_alchemy" / "fable5-compact.json"
    ),
    "perplexity_bedrock": str(
        HOME
        / "ShadowGarden"
        / "live"
        / "spacetime_alchemy"
        / "PERPLEXITY_CONTEXT_BEDROCK.md"
    ),
    "jing_power_latest": str(
        HOME / "ShadowGarden" / "live" / "spacetime_alchemy" / "jing_power_latest.json"
    ),
    "comfyui_context_pack": str(
        HOME
        / "ShadowGarden"
        / "exports"
        / "comfyui_fable5_context"
        / "comfyui_fable5_context_pack.json"
    ),
    "mesh_registry": str(HOME / "shadow_garden_mesh" / "MESH_REGISTRY.json"),
    "chronology_doc": str(ROOT / "docs" / "chronology-recursive-bridge.md"),
    "gate_10": str(ROOT / "shadow_garden_handoff" / "gates" / "GATE_10_OPEN.md"),
    "perplexity_open_merge_task": (
        "https://www.perplexity.ai/computer/tasks/"
        "37bce2fb-1ba6-471f-854f-3871d9c19947?view=thread"
    ),
    "deepseek_testament_share": "https://chat.deepseek.com/share/t3aum0slci9ny6c9bi",
}

ENV_NAMES_ONLY = [
    "XAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "ANTHROPIC_API_KEY",
    "ELEVENLABS_API_KEY",
    "STABLE_HORDE_API_KEY",
    "COMFYUI_URL",
    "GITHUB_TOKEN",
    "GH_TOKEN",
    "GITHUB_OWNER",
    "GITHUB_REPO",
    "ATLASSIAN_API_TOKEN",
    "ATLASSIAN_EMAIL",
    "ATLASSIAN_DOMAIN",
    "JIRA_BASE_URL",
    "JIRA_PROJECT_KEY",
    "CONFLUENCE_BASE_URL",
    "CONFLUENCE_SPACE_KEY",
    "X_API_KEY",
    "X_API_SECRET",
    "X_ACCESS_TOKEN",
    "X_ACCESS_SECRET",
    "X_BEARER_TOKEN",
    "QDRANT_URL",
    "QDRANT_API_KEY",
    "QDRANT_COLLECTION",
    "LINEAR_API_KEY",
    "SLACK_BOT_TOKEN",
    "SLACK_APP_TOKEN",
    "HARPA_API_URL",
    "HARPA_API_KEY",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def port_open(port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout):
            return True
    except OSError:
        return False


def http_code(url: str, timeout: float = 2.0) -> int:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return int(resp.status)
    except urllib.error.HTTPError as exc:
        return int(exc.code)
    except Exception:
        return 0


def env_presence() -> dict[str, bool]:
    return {name: bool(os.environ.get(name)) for name in ENV_NAMES_ONLY}


def build_status(*, probe: bool = True) -> dict[str, Any]:
    roots = []
    for item in REPO_ROOTS:
        p = Path(item["path"])
        roots.append(
            {
                **item,
                "exists": p.is_dir(),
            }
        )

    services = []
    for svc in LOCAL_SERVICES:
        entry: dict[str, Any] = {
            "id": svc["id"],
            "url": svc["url"],
            "port": svc["port"],
            "port_open": port_open(int(svc["port"])) if probe else None,
        }
        if probe:
            entry["http_code"] = http_code(svc["url"])
        services.append(entry)

    pointers = {
        k: {"path": v, "exists": Path(v).exists() if not v.startswith("http") else None}
        for k, v in POINTERS.items()
    }

    jing = None
    jing_path = Path(POINTERS["jing_power_latest"])
    if jing_path.is_file():
        try:
            raw = json.loads(jing_path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                jing = {
                    "jing_power": raw.get("jing_power"),
                    "grok_ok": raw.get("grok_ok"),
                    "comfyui_ok": raw.get("comfyui_ok"),
                    "sampled_at": raw.get("sampled_at") or raw.get("ts"),
                }
        except Exception:
            jing = {"error": "unreadable"}

    return {
        "schema": "shadow_garden.integration_repo_roots.v1",
        "format_version": "1.0",
        "generated_at": utc_now(),
        "secrets_policy": "env_only",
        "lanes": {
            "perplexity": "fable5_synthesis",
            "fable5_game": "local_5619",
            "comfyui": "local_8188",
            "claude": "front_review_opt_in",
            "grok_xai": "back_lane_env",
            "spacetime_alchemy": "catalyst_export",
            "jing_power": "technical_telemetry",
        },
        "repo_roots": roots,
        "services": services,
        "pointers": pointers,
        "env_key_presence": env_presence(),
        "jing_power_summary": jing,
        "guardrails": [
            "no_secret_values_in_status",
            "no_home_wide_crawl",
            "no_comfy_prompt_without_approval",
            "no_perplexity_scrape",
            "symbolic_chronology_only",
        ],
    }


def write_status(status: dict[str, Any], out: Path) -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fable5 + ComfyUI allowlisted command bridge")
    parser.add_argument("command", choices=["status", "write"], help="status | write")
    parser.add_argument("--no-probe", action="store_true", help="skip localhost HTTP probes")
    parser.add_argument(
        "--out",
        default="",
        help="optional output path (default: tmp + handoff outbox)",
    )
    args = parser.parse_args(argv)

    status = build_status(probe=not args.no_probe)
    text = json.dumps(status, indent=2)

    if args.command == "status":
        print(text)
        return 0

    paths = []
    if args.out:
        paths.append(Path(args.out))
    else:
        paths.append(DEFAULT_TMP)
        paths.append(DEFAULT_OUTBOX / "fable5_comfyui_bridge_status.json")

    for path in paths:
        write_status(status, path)
        print(f"wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
