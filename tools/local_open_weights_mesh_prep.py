#!/usr/bin/env python3
"""
Local open-weights mesh preparation — Asuna Point-0 → complete local system.

Prepares (does not force-arm) the full local-based transition:
  - Probes loopback ports (Fable5/EDEN/Comfy/portal/Ollama/Stripe)
  - Inventories Ollama tags (deepseek/kimi families)
  - Refreshes Point-0 catalogs + central control
  - Writes readiness checklist + mesh ledger
  - Optionally refreshes shadow_garden_packet

Arming the final cutover still requires operator-set KIMI3_TRANSITION_ARMED=1.
This tool is the prep stage: LOCAL_MESH_PREP=1 marks prep complete.

Never prints secrets. Never calls remote provider APIs.
"""

from __future__ import annotations

import argparse
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.local_open_weights_mesh_prep.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
MESH_ID = "local_open_weights_mesh"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "local_open_weights_mesh_prep.json"
)
CHECKLIST_OUT = (
    WHA
    / "shadow_garden_handoff"
    / "bridges"
    / "local_open_weights_mesh_checklist.md"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "local_open_weights_mesh_prep.json"
STATUS_OUT = Path("/tmp/shadow_garden_local_open_weights_mesh_prep.json")

LOCAL_PORTS: dict[str, int] = {
    "fable5": 5619,
    "comfyui": 8189,
    "comfyui_alt": 8188,
    "eden": 8791,
    "void_ignition": 8790,
    "portal": 8760,
    "ollama": 11434,
    "stripe_local": 4242,
    "vite_dev": 5173,
    "sillytavern": 8000,
}

REFRESH_CLIS = [
    "deepseek_asuna_point0_unify.py",
    "grok_xai_asuna_point0_unify.py",
    "white_moon_eastern_corner_unify.py",
    "discord_asuna_point0_unify.py",
    "kimi3_asuna_point0_unify.py",
    "perplexity_asuna_central_control.py",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def port_open(port: int, host: str = "127.0.0.1", timeout: float = 0.5) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def probe_ports() -> dict[str, Any]:
    results = {name: port_open(port) for name, port in LOCAL_PORTS.items()}
    core = ["fable5", "eden", "comfyui", "ollama", "portal"]
    core_up = sum(1 for n in core if results.get(n))
    return {
        "bind": "127.0.0.1",
        "ports": {n: {"port": LOCAL_PORTS[n], "up": results[n]} for n in LOCAL_PORTS},
        "core_up": core_up,
        "core_total": len(core),
        "comfy_preferred": 8189,
        "comfy_alt_up": results.get("comfyui_alt", False),
        "ok": core_up >= 1,  # soft: at least one core local service
    }


def probe_ollama() -> dict[str, Any]:
    host = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")
    url = f"{host}/api/tags"
    out: dict[str, Any] = {
        "url": url,
        "up": False,
        "models": [],
        "deepseek_tags": [],
        "kimi_tags": [],
        "model_count": 0,
    }
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            doc = json.loads(resp.read().decode("utf-8", errors="replace"))
        models = []
        for item in doc.get("models") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("model") or "").strip()
            if not name:
                continue
            models.append(name)
        out["up"] = True
        out["models"] = models
        out["model_count"] = len(models)
        out["deepseek_tags"] = [m for m in models if "deepseek" in m.lower()]
        out["kimi_tags"] = [
            m for m in models if "kimi" in m.lower() or "moonshot" in m.lower()
        ]
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        out["error"] = f"{type(exc).__name__}"[:80]
    return out


def env_presence() -> dict[str, Any]:
    names = [
        "KIMI3_TRANSITION_ARMED",
        "LOCAL_MESH_PREP",
        "DEEPSEEK_LOCAL_ENABLED",
        "KIMI_LOCAL_ENABLED",
        "DEEPSEEK_API_KEY",
        "KIMI_API_KEY",
        "MOONSHOT_API_KEY",
        "XAI_API_KEY",
        "PERPLEXITY_API_KEY",
        "ENABLE_DISCORD",
        "DISCORD_LIVE_OK",
        "STRIPE_LIVE_OK",
        "OLLAMA_HOST",
        "COMFYUI_URL",
        "SG_RUN_CONNECT",
        "SG_RUN_EXTENSION",
    ]
    present = {n: bool(os.environ.get(n)) for n in names}
    return {
        "mode": "env_names_only",
        "present": present,
        "transition_armed": os.environ.get("KIMI3_TRANSITION_ARMED") == "1",
        "prep_marked": os.environ.get("LOCAL_MESH_PREP") == "1",
        "remote_keys_present": any(
            present.get(k)
            for k in (
                "DEEPSEEK_API_KEY",
                "KIMI_API_KEY",
                "MOONSHOT_API_KEY",
                "XAI_API_KEY",
                "PERPLEXITY_API_KEY",
            )
        ),
        "local_flags": {
            "DEEPSEEK_LOCAL_ENABLED": os.environ.get("DEEPSEEK_LOCAL_ENABLED"),
            "KIMI_LOCAL_ENABLED": os.environ.get("KIMI_LOCAL_ENABLED"),
        },
    }


def run_cli(name: str) -> dict[str, Any]:
    script = WHA / "tools" / name
    if not script.is_file():
        return {"ok": False, "cli": name, "error": "missing"}
    proc = subprocess.run(
        [sys.executable, str(script), "write"],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        cwd=str(WHA),
    )
    ok = proc.returncode == 0
    vectors = None
    try:
        doc = json.loads(proc.stdout or "{}")
        ok = ok and bool(doc.get("ok", True))
        metrics = doc.get("metrics") or {}
        vectors = (
            metrics.get("vector_count")
            or metrics.get("corner_vector_sum")
            or metrics.get("vector_sum")
        )
    except json.JSONDecodeError:
        pass
    return {
        "ok": ok,
        "cli": name,
        "exit": proc.returncode,
        "vector_count": vectors,
    }


def refresh_catalogs() -> list[dict[str, Any]]:
    results = []
    for name in REFRESH_CLIS:
        try:
            results.append(run_cli(name))
        except (OSError, subprocess.SubprocessError, TimeoutError) as exc:
            results.append({"ok": False, "cli": name, "error": type(exc).__name__})
    return results


def refresh_packet() -> dict[str, Any]:
    script = WHA / "tools" / "shadow_garden_packet.py"
    if not script.is_file():
        return {"ok": False, "error": "missing packet"}
    proc = subprocess.run(
        [sys.executable, str(script), "write"],
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
        cwd=str(WHA),
    )
    bridge = WHA / "shadow_garden_handoff" / "bridges" / "shadow_garden_packet.json"
    return {
        "ok": proc.returncode == 0 and bridge.is_file(),
        "exit": proc.returncode,
        "bridge": str(bridge),
        "exists": bridge.is_file(),
    }


def existing_catalog_health() -> list[dict[str, Any]]:
    pairs = [
        ("deepseek", "deepseek_asuna_point0_unification.json"),
        ("grok_xai", "grok_xai_asuna_point0_unification.json"),
        ("white_moon", "white_moon_eastern_corner.json"),
        ("discord", "discord_asuna_point0_unification.json"),
        ("kimi3", "kimi3_asuna_point0_unification.json"),
        ("central", "perplexity_asuna_central_control.json"),
    ]
    out = []
    for sid, name in pairs:
        path = WHA / "shadow_garden_handoff" / "bridges" / name
        ok = False
        vectors = None
        if path.is_file():
            try:
                doc = json.loads(path.read_text(encoding="utf-8"))
                ok = bool(doc.get("ok", True))
                metrics = doc.get("metrics") or {}
                vectors = (
                    metrics.get("vector_count")
                    or metrics.get("corner_vector_sum")
                    or metrics.get("vector_sum")
                )
            except (OSError, json.JSONDecodeError):
                ok = False
        out.append(
            {
                "ok": ok,
                "cli": f"cached:{sid}",
                "catalog": str(path),
                "vector_count": vectors,
                "cached": True,
            }
        )
    return out


def build_checklist(
    *,
    ports: dict[str, Any],
    ollama: dict[str, Any],
    env: dict[str, Any],
    catalogs: list[dict[str, Any]],
    packet: dict[str, Any],
) -> list[dict[str, Any]]:
    catalog_ok_count = sum(1 for c in catalogs if c.get("ok"))
    packet_skipped = bool(packet.get("skipped"))
    packet_bridge = (
        WHA / "shadow_garden_handoff" / "bridges" / "shadow_garden_packet.json"
    )
    items = [
        {
            "id": "bind_loopback",
            "ok": True,
            "detail": "All prep routes use 127.0.0.1",
        },
        {
            "id": "ollama_up",
            "ok": bool(ollama.get("up")),
            "detail": f"Ollama tags reachable ({ollama.get('model_count', 0)} models)",
        },
        {
            "id": "deepseek_local_tag",
            "ok": bool(ollama.get("deepseek_tags")),
            "detail": (
                f"deepseek tags={ollama.get('deepseek_tags')}"
                if ollama.get("deepseek_tags")
                else "Pull a local deepseek model when ready (optional for prep)"
            ),
            "blocking": False,
        },
        {
            "id": "kimi_local_tag",
            "ok": bool(ollama.get("kimi_tags")),
            "detail": (
                f"kimi tags={ollama.get('kimi_tags')}"
                if ollama.get("kimi_tags")
                else "Pull a local kimi/moonshot model before full cutover (optional for prep)"
            ),
            "blocking": False,
        },
        {
            "id": "comfy_8189",
            "ok": True,
            "detail": "Prefer COMFYUI_URL=http://127.0.0.1:8189 (alt 8188 noted if up)",
            "blocking": False,
        },
        {
            "id": "catalogs_refreshed",
            "ok": catalog_ok_count >= 4,
            "detail": f"{catalog_ok_count}/{len(catalogs) or 0} catalogs ok",
        },
        {
            "id": "packet_refreshed",
            "ok": bool(packet.get("ok"))
            or (packet_skipped and packet_bridge.is_file()),
            "detail": (
                "shadow_garden_packet write"
                if not packet_skipped
                else f"packet artifact present={packet_bridge.is_file()} (refresh skipped)"
            ),
        },
        {
            "id": "remote_keys_unset_preferred",
            "ok": not bool(env.get("remote_keys_present")),
            "detail": (
                "No remote provider keys in process env (good for local-only)"
                if not env.get("remote_keys_present")
                else "Remote provider key names present — leave unset for pure local"
            ),
            "blocking": False,
        },
        {
            "id": "discord_paused",
            "ok": os.environ.get("ENABLE_DISCORD") != "1",
            "detail": "Discord status_notify remains paused by default",
        },
        {
            "id": "stripe_dry_run",
            "ok": os.environ.get("STRIPE_LIVE_OK") != "1",
            "detail": "Stripe stays dry-run unless STRIPE_LIVE_OK=1",
        },
        {
            "id": "transition_arm_gate",
            "ok": True,
            "detail": (
                "KIMI3_TRANSITION_ARMED=1 already set"
                if env.get("transition_armed")
                else "Final cutover still requires KIMI3_TRANSITION_ARMED=1 after approval"
            ),
            "blocking": False,
        },
        {
            "id": "sg_connect_off",
            "ok": os.environ.get("SG_RUN_CONNECT", "0") != "1",
            "detail": "SG_RUN_CONNECT should stay 0 unless explicitly reviewed",
        },
    ]
    return items


def readiness_score(checklist: list[dict[str, Any]]) -> dict[str, Any]:
    blocking = [i for i in checklist if i.get("blocking", True)]
    soft = [i for i in checklist if not i.get("blocking", True)]
    blocking_ok = sum(1 for i in blocking if i.get("ok"))
    soft_ok = sum(1 for i in soft if i.get("ok"))
    prep_ready = blocking_ok == len(blocking) and blocking_ok >= 5
    return {
        "blocking_ok": blocking_ok,
        "blocking_total": len(blocking),
        "soft_ok": soft_ok,
        "soft_total": len(soft),
        "prep_ready": prep_ready,
        "cutover_ready": bool(
            prep_ready
            and any(
                i["id"] == "kimi_local_tag" and i.get("ok") for i in checklist
            )
        ),
    }


def write_checklist_md(payload: dict[str, Any]) -> str:
    lines = [
        "# Local open-weights mesh — readiness checklist",
        "",
        f"Generated: `{payload.get('generated_at')}`",
        f"Mesh: `{MESH_ID}` · Carrier: `{CARRIER}`",
        f"Prep ready: **{payload.get('readiness', {}).get('prep_ready')}** · "
        f"Cutover ready: **{payload.get('readiness', {}).get('cutover_ready')}**",
        "",
        "## Checklist",
        "",
    ]
    for item in payload.get("checklist") or []:
        mark = "x" if item.get("ok") else " "
        block = " (blocking)" if item.get("blocking", True) else " (soft)"
        lines.append(f"- [{mark}] `{item['id']}`{block} — {item.get('detail')}")
    lines.extend(
        [
            "",
            "## Local ports",
            "",
        ]
    )
    for name, info in ((payload.get("ports") or {}).get("ports") or {}).items():
        up = "UP" if info.get("up") else "down"
        lines.append(f"- `{name}` :{info.get('port')} — {up}")
    lines.extend(
        [
            "",
            "## Operator cutover (after prep)",
            "",
            "1. Optionally pull local models: `ollama pull deepseek-r1` / kimi-class tag.",
            "2. Leave remote API keys unset in the shell.",
            "3. `export LOCAL_MESH_PREP=1`",
            "4. After approval: `export KIMI3_TRANSITION_ARMED=1`",
            "5. `python3 tools/kimi3_asuna_point0_unify.py write`",
            "6. `python3 tools/local_open_weights_mesh_prep.py write`",
            "7. `python3 tools/perplexity_asuna_central_control.py write`",
            "8. `python3 tools/shadow_garden_packet.py write`",
            "9. Keep Discord paused; Stripe dry-run; `SG_RUN_CONNECT=0`.",
            "",
        ]
    )
    return "\n".join(lines) + "\n"


def local_lanes() -> dict[str, str]:
    return {
        "mesh": MESH_ID,
        "fable5_game": "local_5619",
        "eden": "local_8791",
        "comfyui": "local_8189_manifest_only",
        "portal": "local_8760",
        "ollama": "local_11434",
        "deepseek": "local_ollama_preferred",
        "kimi3": "local_transition_bridge",
        "grok": "harmony_6_metadata_opt_in_remote",
        "perplexity": "bedrock_compact_local_pointers",
        "discord": "status_notify_paused",
        "stripe": "local_4242_dry_run",
        "claude": "front_review_local_handoff",
    }


def build_prep(*, refresh: bool, write_packet: bool) -> dict[str, Any]:
    ports = probe_ports()
    ollama = probe_ollama()
    env = env_presence()
    catalogs: list[dict[str, Any]] = []
    if refresh:
        catalogs = refresh_catalogs()
    else:
        catalogs = existing_catalog_health()
    packet = refresh_packet() if write_packet else {"ok": None, "skipped": True}
    checklist = build_checklist(
        ports=ports, ollama=ollama, env=env, catalogs=catalogs, packet=packet
    )
    readiness = readiness_score(checklist)
    payload = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "mesh_id": MESH_ID,
        "phase": "prepare",
        "asuna_point0": {
            "point_0": "HOME",
            "label": "perplexity_asuna_point_0",
            "completion_bridge": "kimi3_third_leverage",
            "transition_target": MESH_ID,
        },
        "leverage_stack": {
            "1": "deepseek_local_open_weights",
            "2": "grok_xai_harmony_6_white_moon",
            "3": "kimi3_completion_to_local_open_weights",
        },
        "lanes": local_lanes(),
        "ports": ports,
        "ollama": ollama,
        "env": env,
        "catalog_refresh": catalogs,
        "packet": packet,
        "checklist": checklist,
        "readiness": readiness,
        "controls": {
            "provider_calls": False,
            "credential_logging": False,
            "content_neutral": True,
            "remote_default": False,
            "local_bind_only": True,
            "discord_webhook_post": False,
            "stripe_live_default": False,
            "final_cutover_requires_KIMI3_TRANSITION_ARMED": True,
        },
        "cli": {
            "prep": "python3 tools/local_open_weights_mesh_prep.py write",
            "status": "python3 tools/local_open_weights_mesh_prep.py status",
            "kimi3": "python3 tools/kimi3_asuna_point0_unify.py write",
            "central": "python3 tools/perplexity_asuna_central_control.py write",
            "packet": "python3 tools/shadow_garden_packet.py write",
            "permission_wire": "python3 tools/permission_wire_agent.py wire --profile local_full",
        },
    }
    payload["ok"] = bool(readiness.get("prep_ready"))
    return payload


def write_outputs(payload: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for path in (STATUS_OUT, DEFAULT_OUT, MIRROR_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    CHECKLIST_OUT.parent.mkdir(parents=True, exist_ok=True)
    CHECKLIST_OUT.write_text(write_checklist_md(payload), encoding="utf-8")
    written.append(str(CHECKLIST_OUT))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Prepare complete local open-weights mesh transition"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test", "probe"],
    )
    parser.add_argument(
        "--no-refresh",
        action="store_true",
        help="Skip re-running Point-0 unify CLIs",
    )
    parser.add_argument(
        "--no-packet",
        action="store_true",
        help="Skip shadow_garden_packet write",
    )
    args = parser.parse_args(argv)

    if args.command == "probe":
        print(json.dumps({"ports": probe_ports(), "ollama": probe_ollama()}, indent=2))
        return 0

    refresh = not args.no_refresh and args.command in ("write", "self-test")
    write_packet = not args.no_packet and args.command in ("write", "self-test")
    # self-test should be fast — skip heavy refresh
    if args.command == "self-test":
        refresh = False
        write_packet = False

    payload = build_prep(refresh=refresh, write_packet=write_packet)

    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": payload.get("ok"),
                    "mesh_id": MESH_ID,
                    "readiness": payload.get("readiness"),
                    "ports_core": (payload.get("ports") or {}).get("core_up"),
                    "ollama_up": (payload.get("ollama") or {}).get("up"),
                    "transition_armed": (payload.get("env") or {}).get(
                        "transition_armed"
                    ),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1

    if args.command == "self-test":
        assert payload["schema"] == SCHEMA
        assert payload["mesh_id"] == MESH_ID
        assert payload["controls"]["provider_calls"] is False
        assert payload["controls"]["local_bind_only"] is True
        assert len(payload["checklist"]) >= 8
        print(json.dumps({"ok": True, "readiness": payload["readiness"]}, indent=2))
        return 0

    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
