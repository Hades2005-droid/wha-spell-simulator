#!/usr/bin/env python3
"""Dry-run status for star-fusion trinity MCP lanes (GitHub + Asana + Perplexity).

Content-neutral metadata only. Never prints secret values. No watchers enabled.
Writes: shadow_garden_handoff/bridges/star_fusion_trinity_mcp_status.json
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
STATUS_PATH = (
    REPO_ROOT / "shadow_garden_handoff" / "bridges" / "star_fusion_trinity_mcp_status.json"
)
MCP_JSON = Path.home() / ".cursor" / "mcp.json"
SECRETS = Path.home() / ".cursor" / "secrets.env"
GITHUB_LAUNCHER = Path.home() / ".cursor" / "bin" / "github-mcp-stdio.sh"
ASANA_PREPARE = Path.home() / ".cursor" / "bin" / "asana-mcp-prepare.sh"
DEVIN_BRIDGE = Path.home() / "shadow_garden_may30_monitoring" / "DevinTerminalBridge"
DEVIN_WORKFLOW = REPO_ROOT / ".devin" / "workflows" / "shadowgarden.md"
PERPLEXITY_POINTER = (
    REPO_ROOT / "shadow_garden_handoff" / "bridges" / "perplexity_asuna_central_control.json"
)
MAC_INTAKE = Path.home() / "Desktop" / "shadow-jing-garden" / "mac_intake"


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _secret_presence(name: str) -> str:
    """Return set|empty|missing for a key in secrets.env — never the value."""
    if not SECRETS.is_file():
        return "missing_file"
    try:
        for line in SECRETS.read_text(encoding="utf-8").splitlines():
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, val = raw.split("=", 1)
            if key.strip() != name:
                continue
            cleaned = val.strip().strip('"').strip("'")
            return "set" if cleaned else "empty"
    except OSError:
        return "unreadable"
    return "missing"


def _mcp_servers() -> dict[str, Any]:
    if not MCP_JSON.is_file():
        return {}
    try:
        data = json.loads(MCP_JSON.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    servers = data.get("mcpServers")
    return servers if isinstance(servers, dict) else {}


def build_status() -> dict[str, Any]:
    servers = _mcp_servers()
    asana_cfg = servers.get("asana") if isinstance(servers.get("asana"), dict) else {}
    github_cfg = servers.get("github") if isinstance(servers.get("github"), dict) else {}
    perplexity_docs = "perplexity-docs" in servers
    perplexity_tools = "perplexity-tools" in servers

    asana_id = _secret_presence("ASANA_CLIENT_ID")
    asana_secret = _secret_presence("ASANA_CLIENT_SECRET")
    github_pat = _secret_presence("GITHUB_MCP_PAT")

    asana_wired = (
        asana_cfg.get("url") == "https://mcp.asana.com/v2/mcp"
        and isinstance(asana_cfg.get("auth"), dict)
        and asana_cfg["auth"].get("CLIENT_ID") == "${env:ASANA_CLIENT_ID}"
        and asana_cfg["auth"].get("CLIENT_SECRET") == "${env:ASANA_CLIENT_SECRET}"
    )

    return {
        "schema": "shadow_garden.star_fusion_trinity_mcp_status.v1",
        "generated_at": _utc_now(),
        "mode": "dry_run_metadata",
        "symbolic_name": "star_fusion_trinity",
        "meaning": (
            "Local simulation unification of GitHub (code) + Asana (ops) + "
            "Perplexity (synthesis) feeding Cursor; content-neutral; "
            "metadata/index first; ahead of later local open-weights."
        ),
        "policy": {
            "writes_gated": True,
            "github_mcp_read_only": True,
            "asana_destructive_confirm_required": True,
            "no_secrets_in_repo": True,
            "mac_intake_watchers": "paused_do_not_enable",
            "master_mcp_router": "not_built_scaffolding_only",
            "perplexity_asana_independent": "do_not_break",
        },
        "lanes": {
            "github": {
                "role": "code",
                "mcp_server_key": "github",
                "status": "ready" if github_cfg and GITHUB_LAUNCHER.is_file() else "incomplete",
                "launcher": str(GITHUB_LAUNCHER),
                "launcher_exists": GITHUB_LAUNCHER.is_file(),
                "pat_slot": github_pat,
                "read_only": True,
                "leave_intact": True,
            },
            "linear": {
                "role": "ops_adjacent",
                "mcp_server_key": "plugin-linear-linear",
                "status": "ready_marketplace",
                "note": "Stale OAuth cleared; marketplace Linear works. Leave intact.",
                "leave_intact": True,
            },
            "asana": {
                "role": "ops",
                "mcp_server_key": "asana",
                "status": (
                    "awaiting_user_oauth"
                    if asana_wired and asana_id == "set" and asana_secret == "set"
                    else "awaiting_credentials"
                    if asana_wired
                    else "wiring_incomplete"
                ),
                "mcp_url": "https://mcp.asana.com/v2/mcp",
                "redirect_uri": "cursor://anysphere.cursor-mcp/oauth/callback",
                "app_name_hint": "Cursor Shadow Garden MCP",
                "wired_in_mcp_json": asana_wired,
                "client_id_slot": asana_id,
                "client_secret_slot": asana_secret,
                "prepare_script": str(ASANA_PREPARE),
                "prepare_script_exists": ASANA_PREPARE.is_file(),
                "marketplace_plugin": "plugin-asana-asana",
                "docs": (
                    "https://developers.asana.com/docs/"
                    "connecting-mcp-clients-to-asanas-v2-server"
                ),
            },
            "perplexity": {
                "role": "synthesis",
                "mcp_server_keys": ["perplexity-docs", "perplexity-tools"],
                "status": "ready" if perplexity_docs and perplexity_tools else "partial",
                "docs_mcp": perplexity_docs,
                "tools_mcp": perplexity_tools,
                "pointer": str(PERPLEXITY_POINTER),
                "pointer_exists": PERPLEXITY_POINTER.is_file(),
                "asana_via_perplexity": "independent_leave_intact",
            },
        },
        "devin": {
            "role": "coordination_notes_dry_run_only",
            "workflow": str(DEVIN_WORKFLOW),
            "workflow_exists": DEVIN_WORKFLOW.is_file(),
            "terminal_bridge": str(DEVIN_BRIDGE),
            "terminal_bridge_exists": DEVIN_BRIDGE.is_dir(),
            "unbounded_loops": False,
        },
        "mac_intake": {
            "path": str(MAC_INTAKE),
            "present": MAC_INTAKE.is_dir(),
            "activation": "paused",
            "watchers_50k": "do_not_enable",
        },
        "next_steps": [
            "Paste ASANA_CLIENT_ID and ASANA_CLIENT_SECRET into ~/.cursor/secrets.env",
            "Run ~/.cursor/bin/asana-mcp-prepare.sh --apply-gui-env",
            "Fully quit and reopen Cursor → Tools & MCP → asana → Connect",
            "Later: master MCP router (not in this scaffolding pass)",
        ],
        "artifacts": {
            "status_json": str(STATUS_PATH),
            "cli": "python3 tools/star_fusion_trinity_status.py",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write status JSON under shadow_garden_handoff/bridges/",
    )
    parser.add_argument(
        "--print",
        dest="do_print",
        action="store_true",
        default=True,
        help="Print status JSON to stdout (default)",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Do not print JSON (useful with --write)",
    )
    args = parser.parse_args()
    status = build_status()
    if args.write:
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.write_text(
            json.dumps(status, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    if not args.quiet:
        print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
