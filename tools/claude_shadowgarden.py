#!/usr/bin/env python3
"""Credential-safe local Claude Code lane for the Shadow Garden mesh.

Mirrors the Devin lane (`shadow_garden_may30_monitoring/tools/devin_integration.py`)
but targets the new Claude Code cloud environment integrated with Shadow Garden.

Design goals:
  * Dry-run by default. Live execution requires BOTH
        --execute-claude --confirm-token CLAUDE_LIVE_OK
  * Never store or print secrets. Secret material stays in the environment
    (ANTHROPIC_API_KEY / CLAUDE_API_KEY) and is only referenced by name.
  * Emits a concrete Claude Code command plan as JSON for downstream executors
    (Shadow Garden bridge, mesh diagnostics UI, C# terminal bridge).
  * Live mode only ever runs a single local CLI resolved from CLAUDE_CLI
    (or `claude` discovered on PATH). If none is found -> blocked_claude_cli_missing.
  * Writes a status JSON and a JSONL event log to /tmp by default so the
    browser-side mesh bridge can pick them up via the local Shadow Garden
    Control endpoint.
  * Produces route hints for the bridge feedback lane.

No network calls are made by this script itself.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

CONFIRM_TOKEN = "CLAUDE_LIVE_OK"

DEFAULT_STATUS_FILE = "/tmp/shadow_garden_claude_status.json"
DEFAULT_OUTPUT_LOG = "/tmp/shadow_garden_claude_events.jsonl"
DEFAULT_SNAPSHOT_FILE = "/tmp/shadow_garden_claude_snapshot.json"
DEFAULT_COMMAND_OUT = "/tmp/shadow_garden_claude_commands.json"
DEFAULT_EXTENSION_WORKSPACE = "/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3"

# Names of env vars that may carry secrets. Only PRESENCE is reported.
SECRET_ENV_NAMES = (
    "ANTHROPIC_API_KEY",
    "CLAUDE_API_KEY",
    "CLAUDE_CODE_TOKEN",
    "SHADOWGARDEN_CLAUDE_TOKEN",
    "ANTHROPIC_OAUTH_TOKEN",
    "ANTHROPIC_API_KEY_ID",
)

ANTHROPIC_ADMIN_BASE = "https://api.anthropic.com/v1/organizations/api_keys"
ANTHROPIC_API_VERSION = "2023-06-01"


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _redacted_env_presence() -> dict[str, bool]:
    return {name: bool(os.environ.get(name)) for name in SECRET_ENV_NAMES}


def _load_snapshot(path: str) -> dict[str, Any]:
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {"_raw": data}
    except (OSError, json.JSONDecodeError) as exc:
        return {"_snapshot_error": f"{type(exc).__name__}: could not parse snapshot"}


def _append_jsonl(path: str, event: dict[str, Any]) -> None:
    if not path:
        return
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _write_json(path: str, payload: dict[str, Any]) -> None:
    if not path:
        return
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def build_command_plan(prompt: str, mode: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    """Build a concrete, non-secret Claude Code command plan.

    argv-style commands are used so downstream executors can run them without a
    shell and avoid injection. ${CLAUDE_CLI} / ${ANTHROPIC_API_KEY} etc. are
    placeholders resolved at run time by the operator's environment; this
    script never expands them.
    """
    project_root = snapshot.get(
        "project_root", "/Users/fredwashere/wha-spell-simulator"
    )
    shadow_root = snapshot.get(
        "shadow_root", "/Users/fredwashere/shadow_garden_may30_monitoring"
    )
    session_label = snapshot.get("session_label", "shadow-garden-claude")
    model = snapshot.get("model", os.environ.get("CLAUDE_MODEL", "claude-sonnet-4-5"))
    extension_workspace = snapshot.get(
        "extension_workspace",
        os.environ.get("SG_EXTENSION_WORKSPACE", DEFAULT_EXTENSION_WORKSPACE),
    )

    context_prompt = (
        f"[Shadow Garden / Claude Code lane] mode={mode}. "
        f"Primary workspace: {project_root}. Shadow Garden root: {shadow_root}. "
        f"Comet extension workspace: {extension_workspace}. "
        "Coordinate with existing lanes (Grok mesh sovereign, Devin lane, "
        "Perplexity review, Cursor loop, bridge feedback, Comet extension workspace). Focus on code "
        "authorship, mesh bridge wiring, spell compiler improvements, Manifest V3 review, and "
        "reliability/observability. Emit structured diffs and command plans; "
        "never inline secrets. Keep browser-extension clone/install/build actions explicit and gated. "
        "Boundary for extension work: user-confirmed lawful personal-use only; no DRM, paywall, auth bypass, or hidden scraping support. "
        f"Task: {prompt}"
    )

    commands: list[dict[str, Any]] = [
        {
            "id": "verify_cli",
            "description": "Confirm the local Claude Code CLI is resolvable.",
            "argv": ["${CLAUDE_CLI}", "--version"],
            "requires_live": False,
        },
        {
            "id": "configure_workspace",
            "description": "Point Claude Code at the wha-spell-simulator workspace.",
            "argv": ["${CLAUDE_CLI}", "config", "set", "workspace", project_root],
            "requires_live": True,
        },
        {
            "id": "configure_shadow_context",
            "description": "Register the Shadow Garden monitoring root as a context path.",
            "argv": [
                "${CLAUDE_CLI}",
                "config",
                "set",
                "context.shadow_garden",
                shadow_root,
            ],
            "requires_live": True,
        },
        {
            "id": "configure_extension_context",
            "description": "Register the dedicated Comet extension workspace as optional review context.",
            "argv": [
                "${CLAUDE_CLI}",
                "config",
                "set",
                "context.comet_extension_workspace",
                extension_workspace,
            ],
            "requires_live": True,
        },
        {
            "id": "inspect_extension_status",
            "description": "Emit local Comet extension workspace readiness and Perplexity review prompt.",
            "argv": [
                "python3",
                f"{project_root}/tools/extension_workspace_status.py",
                "--workspace",
                extension_workspace,
            ],
            "requires_live": False,
        },
        {
            "id": "run_gate10_packet",
            "description": "Gate-10-clean unified packet self-test (engine + Claude agent + bridges).",
            "argv": [
                "python3",
                f"{project_root}/tools/shadow_garden_packet.py",
                "write",
            ],
            "requires_live": False,
        },
        {
            "id": "configure_model",
            "description": "Pin the Claude model for this session.",
            "argv": ["${CLAUDE_CLI}", "config", "set", "model", model],
            "requires_live": True,
        },
        {
            "id": "run_session",
            "description": "Launch a Claude Code working session with composed context.",
            "argv": [
                "${CLAUDE_CLI}",
                "run",
                "--session",
                session_label,
                "--prompt",
                context_prompt,
            ],
            "requires_live": True,
        },
    ]

    return {
        "kind": "shadow_garden_claude_command_plan",
        "generated_at": _utc_now(),
        "mode": mode,
        "session_label": session_label,
        "project_root": project_root,
        "shadow_root": shadow_root,
        "extension_workspace": extension_workspace,
        "model": model,
        "context_prompt": context_prompt,
        "commands": commands,
        "notes": [
            "argv entries use ${ENV_VAR} placeholders; secrets are never inlined.",
            "Commands with requires_live=true only run under --execute-claude.",
            "Bridge feedback lane consumes route_hints in the status payload.",
        ],
    }


def verify_anthropic_admin_key(timeout_s: float = 5.0) -> dict[str, Any]:
    """Query the Anthropic Admin API for the configured API key metadata.

    Uses ANTHROPIC_OAUTH_TOKEN (Bearer) + ANTHROPIC_API_KEY_ID from env. Never
    logs the token or the key value. Returns a redacted summary suitable for
    inclusion in the status payload.

    Mirrors:
        curl https://api.anthropic.com/v1/organizations/api_keys/$API_KEY_ID \
             -H 'anthropic-version: 2023-06-01' \
             -H "Authorization: Bearer $ANTHROPIC_OAUTH_TOKEN"
    """
    oauth = os.environ.get("ANTHROPIC_OAUTH_TOKEN")
    key_id = os.environ.get("ANTHROPIC_API_KEY_ID")
    if not oauth or not key_id:
        return {
            "checked": False,
            "reason": "ANTHROPIC_OAUTH_TOKEN / ANTHROPIC_API_KEY_ID not set",
        }

    url = f"{ANTHROPIC_ADMIN_BASE}/{key_id}"
    req = urllib.request.Request(
        url,
        headers={
            "anthropic-version": ANTHROPIC_API_VERSION,
            "Authorization": f"Bearer {oauth}",
            "Accept": "application/json",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310 - HTTPS to fixed host
            status_code = resp.status
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return {
            "checked": True,
            "ok": False,
            "http_status": exc.code,
            "error": f"HTTP {exc.code}",
        }
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return {
            "checked": True,
            "ok": False,
            "error": f"{type(exc).__name__}",
        }

    try:
        payload = json.loads(body) if body else {}
    except json.JSONDecodeError:
        payload = {}

    # Redacted summary: never echo the raw key or token.
    return {
        "checked": True,
        "ok": 200 <= status_code < 300,
        "http_status": status_code,
        "key_id": payload.get("id") or key_id,
        "name": payload.get("name"),
        "status": payload.get("status"),
        "workspace_id": payload.get("workspace_id"),
        "created_at": payload.get("created_at"),
        "partial_key_hint": payload.get("partial_key_hint"),
    }


def resolve_claude_cli() -> tuple[str | None, str]:
    """Resolve the local Claude Code CLI path.

    Priority: CLAUDE_CLI env var (must be an executable file), then `claude`
    on PATH. Returns (path_or_None, reason).
    """
    env_cli = os.environ.get("CLAUDE_CLI")
    if env_cli:
        if os.path.isfile(env_cli) and os.access(env_cli, os.X_OK):
            return env_cli, "resolved_from_CLAUDE_CLI"
        return None, "CLAUDE_CLI set but not an executable file"
    discovered = shutil.which("claude")
    if discovered:
        return discovered, "discovered_on_PATH"
    return None, "no CLAUDE_CLI and no `claude` on PATH"


def build_route_hints(mode: str, status: str, snapshot: dict[str, Any]) -> dict[str, Any]:
    return {
        "target_lane": "bridge_feedback",
        "source_lane": "claude",
        "mode": mode,
        "status": status,
        "suggested_routes": [
            {"lane": "grok_mesh", "reason": "share Claude session outcome with Grok sovereign"},
            {"lane": "devin", "reason": "cross-verify command plan against Devin lane"},
            {"lane": "perplexity", "reason": "queue Claude output and Comet extension review prompt for Perplexity review"},
            {"lane": "comet_extension", "reason": "surface browser-extension workspace readiness and lawful-use gate"},
            {"lane": "cursor_loop", "reason": "hand off code edits to Cursor loop if produced"},
        ],
        "snapshot_present": bool(snapshot) and "_snapshot_error" not in snapshot,
    }


def _run_live(cli_path: str, plan: dict[str, Any], log_path: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    overall_ok = True
    for cmd in plan["commands"]:
        argv = [cli_path if tok == "${CLAUDE_CLI}" else tok for tok in cmd["argv"]]
        try:
            proc = subprocess.run(  # noqa: S603 - argv list, shell=False
                argv,
                capture_output=True,
                text=True,
                timeout=120,
                check=False,
            )
            ok = proc.returncode == 0
            overall_ok = overall_ok and ok
            entry = {
                "id": cmd["id"],
                "returncode": proc.returncode,
                "ok": ok,
                "stdout_head": (proc.stdout or "")[:500],
                "stderr_head": (proc.stderr or "")[:500],
            }
        except (OSError, subprocess.SubprocessError) as exc:
            overall_ok = False
            entry = {"id": cmd["id"], "ok": False, "error": f"{type(exc).__name__}"}
        results.append(entry)
        _append_jsonl(log_path, {"ts": _utc_now(), "event": "live_command", **entry})
        if not entry.get("ok"):
            break
    return {"executed": True, "overall_ok": overall_ok, "results": results}


def run_packet_self_test() -> dict[str, Any]:
    """Force-merge entry: run Gate-10-clean shadow_garden_packet self-test.

    Credential-free. Content-neutral. Writes packet status for Black Sun bridge.
    """
    packet_path = Path(__file__).resolve().parent / "shadow_garden_packet.py"
    if not packet_path.is_file():
        return {
            "ok": False,
            "error": "shadow_garden_packet.py missing",
            "path": str(packet_path),
        }
    try:
        proc = subprocess.run(  # noqa: S603
            [sys.executable, str(packet_path), "write"],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return {
            "ok": proc.returncode == 0,
            "exit": proc.returncode,
            "path": str(packet_path),
            "stdout_head": (proc.stdout or "")[:800],
            "stderr_head": (proc.stderr or "")[:400],
            "lane": "claude_black_sun_packet",
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}", "path": str(packet_path)}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Credential-safe local Claude Code lane for the Shadow Garden mesh.",
    )
    p.add_argument(
        "--prompt",
        default="Improve Shadow Garden mesh wiring, spell compiler, and Claude Code integration.",
    )
    p.add_argument("--mode", default="auto", help="Lane mode label (auto, configure, run, ...).")
    p.add_argument("--status-file", default=DEFAULT_STATUS_FILE)
    p.add_argument("--output-log", default=DEFAULT_OUTPUT_LOG)
    p.add_argument("--snapshot-file", default=DEFAULT_SNAPSHOT_FILE)
    p.add_argument("--command-out", default=DEFAULT_COMMAND_OUT)
    p.add_argument(
        "--run-packet",
        action="store_true",
        help="Run Gate-10 shadow_garden_packet self-test (engine+agent+bridge) then exit.",
    )
    p.add_argument("--execute-claude", action="store_true", help="Arm live execution.")
    p.add_argument(
        "--confirm-token",
        default="",
        help=f"Must equal {CONFIRM_TOKEN} for live mode.",
    )
    p.add_argument(
        "--verify-admin-key",
        action="store_true",
        help=(
            "Hit the Anthropic Admin API to verify the configured API key "
            "metadata. Requires ANTHROPIC_OAUTH_TOKEN + ANTHROPIC_API_KEY_ID."
        ),
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    # Gate-10 packet force-merge: engine + agent + bridge self-test
    if getattr(args, "run_packet", False):
        packet_result = run_packet_self_test()
        _write_json(
            args.status_file,
            {
                "kind": "shadow_garden_claude_status",
                "generated_at": _utc_now(),
                "status": "packet_ok" if packet_result.get("ok") else "packet_failed",
                "mode": "black_sun_packet",
                "dry_run": True,
                "packet": packet_result,
                "route_hints": build_route_hints(
                    "black_sun_packet",
                    "packet_ok" if packet_result.get("ok") else "packet_failed",
                    {},
                ),
            },
        )
        _append_jsonl(
            args.output_log,
            {"ts": _utc_now(), "event": "packet_self_test", **packet_result},
        )
        print(
            f"[claude_shadowgarden] packet "
            f"{'OK' if packet_result.get('ok') else 'FAIL'} "
            f"path={packet_result.get('path')}"
        )
        return 0 if packet_result.get("ok") else 1

    snapshot = _load_snapshot(args.snapshot_file)
    plan = build_command_plan(args.prompt, args.mode, snapshot)

    admin_key_check = verify_anthropic_admin_key() if args.verify_admin_key else {"checked": False, "reason": "--verify-admin-key not set"}

    _write_json(args.command_out, plan)

    live_requested = args.execute_claude
    token_ok = args.confirm_token == CONFIRM_TOKEN
    armed = live_requested and token_ok

    _append_jsonl(
        args.output_log,
        {
            "ts": _utc_now(),
            "event": "lane_start",
            "mode": args.mode,
            "live_requested": live_requested,
            "token_ok": token_ok,
            "secret_env_present": _redacted_env_presence(),
            "snapshot_present": bool(snapshot),
        },
    )

    execution: dict[str, Any]
    if not armed:
        if live_requested and not token_ok:
            status = "blocked_bad_confirm_token"
        else:
            status = "dry_run"
        execution = {"executed": False, "reason": status}
    else:
        cli_path, reason = resolve_claude_cli()
        if cli_path is None:
            status = "blocked_claude_cli_missing"
            execution = {"executed": False, "reason": reason}
        else:
            run_result = _run_live(cli_path, plan, args.output_log)
            execution = run_result
            status = "live_ok" if run_result["overall_ok"] else "live_failed"

    route_hints = build_route_hints(args.mode, status, snapshot)

    status_payload = {
        "kind": "shadow_garden_claude_status",
        "generated_at": _utc_now(),
        "status": status,
        "mode": args.mode,
        "dry_run": not armed,
        "model": plan["model"],
        "session_label": plan["session_label"],
        "command_out": args.command_out,
        "command_count": len(plan["commands"]),
        "extension_workspace": plan["extension_workspace"],
        "secret_env_present": _redacted_env_presence(),
        "snapshot_present": bool(snapshot),
        "execution": execution,
        "admin_key_check": admin_key_check,
        "route_hints": route_hints,
        "capabilities": [
            "code",
            "tool_use",
            "long_context",
            "shadow_garden_bridge",
            "comet_extension_workspace_review",
        ],
    }
    _write_json(args.status_file, status_payload)
    _append_jsonl(args.output_log, {"ts": _utc_now(), "event": "lane_end", "status": status})

    print(f"[claude_shadowgarden] status={status} dry_run={not armed} mode={args.mode}")
    print(
        f"[claude_shadowgarden] command plan -> {args.command_out} "
        f"({len(plan['commands'])} cmds)"
    )
    print(f"[claude_shadowgarden] status file -> {args.status_file}")
    print(f"[claude_shadowgarden] event log   -> {args.output_log}")
    if status == "blocked_claude_cli_missing":
        print(
            "[claude_shadowgarden] BLOCKED: no Claude CLI "
            "(set CLAUDE_CLI or install `claude`)."
        )

    if status in ("dry_run", "live_ok"):
        return 0
    if status == "blocked_bad_confirm_token":
        return 2
    if status == "blocked_claude_cli_missing":
        return 3
    return 1


if __name__ == "__main__":
    sys.exit(main())
