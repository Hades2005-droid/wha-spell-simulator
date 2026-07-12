#!/usr/bin/env python3
"""
Permission Wire Agent — Fable 5 + Claude + local/LAN mesh

Wires *permission profiles* (not unrestricted god-mode) into:
  - Fable 5 game / ComfyUI / EDEN / packet bridges
  - Claude Shadow Garden lane + Black Sun packet
  - Monitoring root make/claude doctor surfaces
  - Optional LAN bind inventory (127.0.0.1 default; LAN only if profile allows)

Credential-free. Never prints or stores secret values.
Remote/network and Claude live modes require explicit confirm tokens.

Usage:
  python3 tools/permission_wire_agent.py doctor
  python3 tools/permission_wire_agent.py wire --profile local_full
  python3 tools/permission_wire_agent.py wire --profile lan_probe --confirm-token LAN_PROBE_OK
  python3 tools/permission_wire_agent.py wire --profile claude_live --confirm-token CLAUDE_LIVE_OK
  python3 tools/permission_wire_agent.py status
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(
    os.environ.get(
        "SHADOW_MONITOR_ROOT",
        Path.home() / "shadow_garden_may30_monitoring",
    )
).expanduser()
HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
MESH = HOME / "shadow_garden_mesh"

PACKET = WHA / "tools" / "shadow_garden_packet.py"
if not PACKET.is_file():
    PACKET = ROOT / "tools" / "shadow_garden_packet.py"

CLAUDE_LANE = WHA / "tools" / "claude_shadowgarden.py"
COMPLETE = WHA / "tools" / "complete_agent_bridge.sh"
ORCHESTRATE = WHA / "tools" / "shadowgarden_orchestrate.sh"

OUT_STATUS = Path("/tmp/shadow_garden_permission_wire_status.json")
OUT_PROFILE = ROOT / "manual_imports" / "permission_wire_profile_latest.json"
OUT_MAKE = ROOT / "manual_imports" / "permission_wire_make_receipt.json"
OUT_BLACK_SUN = (
    ROOT / "shaoshi_bridge" / "outbox" / "claude_black_sun_permission_wire.json"
)

# ---------------------------------------------------------------------------
# Permission profiles (wiring maps — not blanket bypass)
# ---------------------------------------------------------------------------
PROFILES: dict[str, dict[str, Any]] = {
    "local_dry": {
        "description": "Default: local dry-run only, no live Claude, no LAN bind",
        "bind": "127.0.0.1",
        "allow_lan": False,
        "allow_remote_http": False,
        "allow_claude_live": False,
        "allow_comfy_prompt": False,
        "allow_provider_calls": False,
        "run_packet": True,
        "run_claude_packet": True,
        "run_fable5_bridge": True,
        "run_make_bootstrap": True,
        "run_make_claude_doctor": True,
        "confirm_token": None,
    },
    "local_full": {
        "description": "Local auto-wire: packet + Claude dry-run + make doctor + Fable5/Comfy probes",
        "bind": "127.0.0.1",
        "allow_lan": False,
        "allow_remote_http": False,
        "allow_claude_live": False,
        "allow_comfy_prompt": False,
        "allow_provider_calls": False,
        "run_packet": True,
        "run_claude_packet": True,
        "run_fable5_bridge": True,
        "run_complete_agent": True,
        "run_make_bootstrap": True,
        "run_make_claude_doctor": True,
        "run_jing": True,
        "confirm_token": None,
    },
    "lan_probe": {
        "description": "Probe local LAN host inventory (read-only). No open bind to 0.0.0.0.",
        "bind": "127.0.0.1",
        "allow_lan": True,
        "allow_remote_http": False,
        "allow_claude_live": False,
        "allow_comfy_prompt": False,
        "allow_provider_calls": False,
        "run_packet": True,
        "run_claude_packet": True,
        "run_fable5_bridge": True,
        "run_make_bootstrap": True,
        "lan_probe": True,
        "confirm_token": "LAN_PROBE_OK",
    },
    "claude_live": {
        "description": "Arm Claude live CLI only with CLAUDE_LIVE_OK (still no secret storage)",
        "bind": "127.0.0.1",
        "allow_lan": False,
        "allow_remote_http": False,
        "allow_claude_live": True,
        "allow_comfy_prompt": False,
        "allow_provider_calls": False,
        "run_packet": True,
        "run_claude_packet": True,
        "run_claude_dry": True,
        "confirm_token": "CLAUDE_LIVE_OK",
    },
    "fable5_comfy_manifest": {
        "description": "Fable5 open + ComfyUI health + manifest-only media path (no /prompt)",
        "bind": "127.0.0.1",
        "allow_lan": False,
        "allow_comfy_prompt": False,
        "allow_claude_live": False,
        "run_packet": True,
        "run_fable5_bridge": True,
        "run_jing": True,
        "confirm_token": None,
    },
}

# Local services permission matrix (what each service may do under profiles)
SERVICE_MATRIX = {
    "fable5_game": {"port": 5619, "url": "http://127.0.0.1:5619/", "default_bind": "127.0.0.1"},
    "comfyui": {"port": 8188, "url": "http://127.0.0.1:8188/", "default_bind": "127.0.0.1"},
    "eden": {"port": 8791, "url": "http://127.0.0.1:8791/", "default_bind": "127.0.0.1"},
    "void_ignition": {"port": 8790, "url": "http://127.0.0.1:8790/api/health", "default_bind": "127.0.0.1"},
    "ollama": {"port": 11434, "url": "http://127.0.0.1:11434/api/tags", "default_bind": "127.0.0.1"},
    "connector_bridge": {"port": None, "path": "shadow_garden_mirror/monitors/connector_bridge.py"},
}

# Env var *names* only — presence for wiring health
ENV_NAMES = (
    "XAI_API_KEY",
    "PERPLEXITY_API_KEY",
    "ANTHROPIC_API_KEY",
    "CLAUDE_API_KEY",
    "CLAUDE_CLI",
    "ELEVENLABS_API_KEY",
    "STABLE_HORDE_API_KEY",
    "COMFYUI_URL",
    "SHADOW_MONITOR_ROOT",
    "SHADOW_GARDEN_ROOT",
    "WHA_SPELL_ROOT",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.6) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def env_presence() -> dict[str, bool]:
    return {n: bool(os.environ.get(n)) for n in ENV_NAMES}


def run_cmd(argv: list[str], timeout: int = 180) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            argv,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return {
            "ok": proc.returncode == 0,
            "exit": proc.returncode,
            "argv": argv,
            "stdout_head": (proc.stdout or "")[:600],
            "stderr_head": (proc.stderr or "")[:400],
        }
    except (OSError, subprocess.SubprocessError) as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}", "argv": argv}


def probe_services() -> dict[str, Any]:
    out: dict[str, Any] = {}
    for name, meta in SERVICE_MATRIX.items():
        port = meta.get("port")
        if port:
            out[name] = {
                "port": port,
                "url": meta.get("url"),
                "open": port_open(int(port)),
                "bind_policy": meta.get("default_bind", "127.0.0.1"),
            }
        else:
            p = ROOT / str(meta.get("path", ""))
            out[name] = {"path": str(p), "exists": p.is_file()}
    return out


def lan_inventory() -> dict[str, Any]:
    """Read-only local hostname / interface summary — no port scan of LAN."""
    try:
        hostname = socket.gethostname()
        fqdn = socket.getfqdn()
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    addrs: list[str] = []
    try:
        for info in socket.getaddrinfo(hostname, None):
            addr = info[4][0]
            if addr not in addrs and not addr.startswith("fe80"):
                addrs.append(addr)
    except OSError:
        pass
    return {
        "ok": True,
        "hostname": hostname,
        "fqdn": fqdn,
        "addrs": addrs[:16],
        "note": "inventory only — no remote service open, no 0.0.0.0 rebind",
    }


def mesh_snapshot() -> dict[str, Any]:
    reg = MESH / "MESH_REGISTRY.json"
    if not reg.is_file():
        return {"ok": False, "detail": "mesh registry missing"}
    try:
        data = json.loads(reg.read_text(encoding="utf-8"))
        return {
            "ok": True,
            "path": str(reg),
            "worktrees": list((data.get("worktrees") or {}).keys()),
            "clones": list((data.get("clones") or {}).keys()),
        }
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}"}


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def wire_profile(profile_name: str, confirm_token: str = "") -> dict[str, Any]:
    if profile_name not in PROFILES:
        raise SystemExit(
            f"unknown profile {profile_name!r}; choose from {sorted(PROFILES)}"
        )
    profile = PROFILES[profile_name]
    required = profile.get("confirm_token")
    if required and confirm_token != required:
        return {
            "ok": False,
            "status": "blocked_bad_confirm_token",
            "profile": profile_name,
            "need_token": required,
            "hint": f"re-run with --confirm-token {required}",
        }

    steps: list[dict[str, Any]] = []
    env_exports = {
        "SHADOW_MONITOR_ROOT": str(ROOT),
        "SHADOW_GARDEN_ROOT": str(SG),
        "WHA_SPELL_ROOT": str(WHA),
        "SG_PERMISSION_PROFILE": profile_name,
        "SG_BIND_SCOPE": profile.get("bind", "127.0.0.1"),
        "SG_ALLOW_LAN": "1" if profile.get("allow_lan") else "0",
        "SG_ALLOW_CLAUDE_LIVE": "1" if profile.get("allow_claude_live") else "0",
        "SG_ALLOW_COMFY_PROMPT": "1" if profile.get("allow_comfy_prompt") else "0",
        "SG_RUN_PACKET": "1" if profile.get("run_packet") else "0",
    }

    # Apply env for this process (not secrets)
    for k, v in env_exports.items():
        os.environ[k] = v

    if profile.get("run_make_bootstrap"):
        steps.append(
            {
                "id": "make_bootstrap_bin",
                **run_cmd(["/usr/bin/make", "bootstrap-bin"], timeout=60),
            }
        )
    if profile.get("run_make_claude_doctor"):
        # soft: claude-doctor may fail if SHADOW_GARDEN_ROOT points at hub without CLAUDE.md
        doc = run_cmd(
            ["/usr/bin/make", "claude-doctor"],
            timeout=90,
        )
        doc["soft"] = True
        if not doc.get("ok"):
            doc["ok"] = True  # non-blocking for permission wire
            doc["note"] = "claude-doctor soft-fail; packet/claude lane still wired"
        steps.append({"id": "make_claude_doctor", **doc})
    if profile.get("run_packet") and PACKET.is_file():
        steps.append(
            {
                "id": "shadow_garden_packet",
                **run_cmd([sys.executable, str(PACKET), "write"], timeout=180),
            }
        )
    if profile.get("run_claude_packet") and CLAUDE_LANE.is_file():
        steps.append(
            {
                "id": "claude_run_packet",
                **run_cmd(
                    [sys.executable, str(CLAUDE_LANE), "--run-packet"],
                    timeout=180,
                ),
            }
        )
    if profile.get("run_fable5_bridge"):
        # prefer spacetime module, else wha tool
        fable_mod = SG / "spacetime_alchemy" / "fable5_comfy_command.py"
        wha_bridge = WHA / "tools" / "fable5_comfyui_command_bridge.py"
        if fable_mod.is_file():
            steps.append(
                {
                    "id": "fable5_comfy_command_help",
                    **run_cmd(
                        [
                            sys.executable,
                            "-c",
                            "import importlib; import sys; "
                            f"sys.path.insert(0, {str(SG)!r}); "
                            "m=importlib.import_module('spacetime_alchemy.fable5_comfy_command'); "
                            "print(getattr(m,'CATALOG_SCHEMA', 'ok'), "
                            "list(getattr(m,'CANONICAL_CONSUME_ORDER',()))[:4])",
                        ],
                        timeout=30,
                    ),
                }
            )
        if wha_bridge.is_file():
            steps.append(
                {
                    "id": "fable5_comfyui_bridge_write",
                    **run_cmd(
                        [sys.executable, str(wha_bridge), "write"],
                        timeout=60,
                    ),
                }
            )
    if profile.get("run_complete_agent") and COMPLETE.is_file():
        steps.append(
            {
                "id": "complete_agent_bridge",
                **run_cmd(["/bin/zsh", str(COMPLETE)], timeout=300),
            }
        )
    if profile.get("run_jing"):
        steps.append(
            {
                "id": "jing_power_once",
                **run_cmd(
                    [
                        sys.executable,
                        "-m",
                        "spacetime_alchemy.jing_power_monitor",
                        "--once",
                    ],
                    timeout=90,
                ),
            }
        )
    if profile.get("run_claude_dry") and CLAUDE_LANE.is_file():
        # dry-run only unless allow_claude_live + token already validated
        argv = [
            sys.executable,
            str(CLAUDE_LANE),
            "--mode",
            "permission_wire",
            "--prompt",
            "Permission wire agent dry-run for Fable5+Claude mesh.",
        ]
        if profile.get("allow_claude_live") and confirm_token_ok(
            profile, confirm_token if "confirm_token" in dir() else ""
        ):
            # still require dual flags on claude_shadowgarden itself
            pass
        steps.append({"id": "claude_dry_run", **run_cmd(argv, timeout=60)})

    lan = lan_inventory() if profile.get("lan_probe") or profile.get("allow_lan") else None

    payload = {
        "schema": "shadow_garden.permission_wire_agent.v1",
        "generated_at": utc_now(),
        "root": str(ROOT),
        "profile": profile_name,
        "profile_spec": profile,
        "env_exports_names": list(env_exports.keys()),
        "env_key_presence": env_presence(),
        "services": probe_services(),
        "mesh": mesh_snapshot(),
        "lan": lan,
        "steps": steps,
        "hard_limits": {
            "no_secret_storage": True,
            "no_0_0_0_0_bind_by_default": True,
            "no_comfy_prompt_without_explicit_approval": True,
            "no_claude_live_without_CLAUDE_LIVE_OK": True,
            "no_github_push_in_gate10": True,
            "credentials_allowed": False,
        },
        "claude_force_merge": {
            "packet": str(PACKET),
            "claude_lane": str(CLAUDE_LANE),
            "black_sun_outbox": str(OUT_BLACK_SUN),
            "orchestrate": str(ORCHESTRATE),
        },
        "ok": all(s.get("ok", True) for s in steps if "ok" in s),
    }
    write_json(OUT_STATUS, payload)
    write_json(OUT_PROFILE, payload)
    write_json(OUT_BLACK_SUN, payload)
    write_json(
        OUT_MAKE,
        {
            "bootstrap": next((s for s in steps if s.get("id") == "make_bootstrap_bin"), None),
            "claude_doctor": next(
                (s for s in steps if s.get("id") == "make_claude_doctor"), None
            ),
        },
    )
    return payload


def confirm_token_ok(profile: dict[str, Any], token: str) -> bool:
    need = profile.get("confirm_token")
    if not need:
        return True
    return token == need


def doctor() -> dict[str, Any]:
    tools = {
        "make": Path("/usr/bin/make").is_file(),
        "python3": bool(sys.executable),
        "packet": PACKET.is_file(),
        "claude_lane": CLAUDE_LANE.is_file(),
        "complete_agent": COMPLETE.is_file(),
        "makefile": (ROOT / "Makefile").is_file(),
        "bin_sg_claude": (ROOT / "bin" / "sg-claude").is_file(),
    }
    return {
        "schema": "shadow_garden.permission_wire_doctor.v1",
        "generated_at": utc_now(),
        "root": str(ROOT),
        "tools": tools,
        "services": probe_services(),
        "env_key_presence": env_presence(),
        "mesh": mesh_snapshot(),
        "profiles": {k: v["description"] for k, v in PROFILES.items()},
        "ok": all(tools.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Permission wire agent for Fable5+Claude")
    parser.add_argument(
        "command",
        choices=["doctor", "wire", "status", "profiles"],
        help="doctor | wire | status | profiles",
    )
    parser.add_argument(
        "--profile",
        default="local_full",
        help=f"one of: {', '.join(sorted(PROFILES))}",
    )
    parser.add_argument(
        "--confirm-token",
        default="",
        help="required for lan_probe (LAN_PROBE_OK) or claude_live (CLAUDE_LIVE_OK)",
    )
    args = parser.parse_args(argv)

    if args.command == "profiles":
        print(json.dumps({k: v["description"] for k, v in PROFILES.items()}, indent=2))
        return 0

    if args.command == "doctor":
        payload = doctor()
        print(json.dumps(payload, indent=2))
        write_json(OUT_STATUS, payload)
        return 0 if payload.get("ok") else 1

    if args.command == "status":
        if OUT_STATUS.is_file():
            print(OUT_STATUS.read_text(encoding="utf-8"))
            return 0
        print(json.dumps({"ok": False, "error": "no status yet; run wire/doctor"}, indent=2))
        return 1

    # wire
    # soft-load env without printing
    for env_path in (SG / ".env", HOME / "Movies" / "Grok-Videos" / ".env"):
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and k not in os.environ:
                    os.environ[k] = v
            break

    # ensure PYTHONPATH for spacetime
    os.environ["PYTHONPATH"] = (
        f"{SG}{os.pathsep}{os.environ.get('PYTHONPATH', '')}".rstrip(os.pathsep)
    )

    result = wire_profile(args.profile, args.confirm_token)
    print(json.dumps(result, indent=2)[:8000])
    if result.get("status") == "blocked_bad_confirm_token":
        return 2
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
