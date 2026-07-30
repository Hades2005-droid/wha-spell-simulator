#!/usr/bin/env python3
"""
Discord → Perplexity Asuna Point-0 unification (status_notify lane).

Indexes env-name Discord surface, MCP registry, catalyst pause state, and
local path pointers into Spacetime Alchemy metadata. Default: PAUSED —
no webhook posts, no channel scrapes, no credential logging.

Never prints tokens or webhook URLs. Metadata / source-pointers only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.discord_asuna_point0_unification.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CANONICAL_ID = "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1"
PACKAGE_ID = "shadow-garden-phase2-fable5-black-sun-home-sim"
LANE = {
    "id": "discord_status_notify",
    "domain": "status_notify",
    "transport": "webhook_or_bot_api",
    "default_state": "PAUSED",
    "leveraged_by": "perplexity_asuna_point_0",
}

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
MON = Path(
    os.environ.get("SHADOW_MONITOR_ROOT", HOME / "shadow_garden_may30_monitoring")
)

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "discord_asuna_point0_unification.json"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "discord_asuna_point0_unification.json"
STATUS_OUT = Path("/tmp/shadow_garden_discord_asuna_point0.json")

API_ENV_NAMES = [
    "ENABLE_DISCORD",
    "DISCORD_WEBHOOK_URL",
    "DISCORD_BOT_TOKEN",
    "DISCORD_TOKEN",
    "DISCORD_CHANNEL_ID",
    "DISCORD_GUILD_ID",
]

CONTROLS = {
    "webhook_post": False,
    "bot_api_calls": False,
    "scrape_channel_history": False,
    "credential_access": False,
    "credential_logging": False,
    "secrets_in_artifacts": False,
    "allowed_mentions": False,
    "broadcast_credentials": False,
    "bulk_upload_perplexity": False,
    "content_neutral": True,
    "symbolic_only": True,
    "source_pointers_only": True,
    "default_lane": "read_only",
    "paused_by_default": True,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def stable_digest(payload: Any) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def file_pointer(path: Path, *, role: str, kind: str) -> dict[str, Any]:
    out: dict[str, Any] = {
        "role": role,
        "kind": kind,
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "content_inlined": False,
    }
    if path.is_file():
        try:
            data = path.read_bytes()
            out["size_bytes"] = len(data)
            out["sha256_16"] = hashlib.sha256(data).hexdigest()[:16]
        except OSError as exc:
            out["error"] = f"{type(exc).__name__}"[:80]
    return out


def asuna_point0() -> dict[str, Any]:
    registry = MON / "shaoshi_bridge" / "south_star" / "home_black_sun_registry.py"
    out: dict[str, Any] = {
        "point_0": "HOME",
        "label": "perplexity_asuna_point_0",
        "resident_archetype": "angela_asuna_home",
        "protector_label": "KIRITO_FRED",
        "scene_id": "kitchen_log_cabin_floor_22",
        "symbolic_only": True,
        "not_claim_about_real_people": True,
        "registry_path": str(registry),
        "registry_exists": registry.is_file(),
        "status_notify_lane": True,
    }
    if not registry.is_file():
        return out
    try:
        proc = subprocess.run(
            [os.environ.get("PYTHON", "python3"), str(registry), "--manifest"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode == 0:
            manifest = json.loads(proc.stdout or "{}")
            out["home_protected"] = manifest.get("home_protected") or {}
            out["q24_canonical_id"] = manifest.get("q24_canonical_id")
            out["anchor"] = manifest.get("anchor")
            out["phase"] = manifest.get("phase")
            out["manifest_ok"] = True
        else:
            out["manifest_ok"] = False
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        out["manifest_ok"] = False
        out["error"] = f"{type(exc).__name__}: {exc}"[:160]
    return out


def api_surface() -> dict[str, Any]:
    present = {
        name: (name in os.environ and bool(os.environ.get(name)))
        for name in API_ENV_NAMES
    }
    enabled = bool(present.get("ENABLE_DISCORD"))
    return {
        "mode": "env_names_only",
        "transport": "webhook_or_bot_api",
        "public_docs": "https://discord.com/developers/docs",
        "env_names": list(API_ENV_NAMES),
        "env_present": present,
        "enable_discord_armed": enabled,
        "notes": [
            "Never print or catalog token/webhook values.",
            "Default PAUSED; ENABLE_DISCORD only arms status_notify after approval.",
            "No channel history scrape; no mass broadcast.",
        ],
    }


def catalyst_connector_state() -> dict[str, Any]:
    path = (
        WHA
        / "shadow_garden_handoff"
        / "terminal_auto"
        / "outbox"
        / "catalyst_spell_3.json"
    )
    out: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "state": "PAUSED",
        "source": "catalyst_spell_3_default",
    }
    if not path.is_file():
        return out
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
        connectors = doc.get("connectors") or {}
        discord = connectors.get("discord") if isinstance(connectors, dict) else None
        if isinstance(discord, dict):
            out["state"] = str(discord.get("state") or "PAUSED")
            out["source"] = "catalyst_spell_3.json"
            out["mutation_attempted"] = bool(discord.get("mutation_attempted", False))
    except (OSError, json.JSONDecodeError):
        pass
    return out


def mesh_pointers() -> list[dict[str, Any]]:
    return [
        file_pointer(
            WHA / "tools" / "mcp_router_registry.json",
            role="mcp_discord_registry",
            kind="config",
        ),
        file_pointer(
            WHA / "tools" / "fable5_comfyui_command_bridge.py",
            role="bridge_env_names_surface",
            kind="code",
        ),
        file_pointer(
            WHA / "docs" / "mcp-router-policy.md",
            role="mcp_policy_doc",
            kind="doc",
        ),
        file_pointer(
            WHA
            / "shadow_garden_handoff"
            / "terminal_auto"
            / "outbox"
            / "catalyst_spell_3.json",
            role="catalyst_discord_paused",
            kind="handoff",
        ),
        file_pointer(
            WHA / "tools" / "discord_local" / "notify.py",
            role="discord_local_dry_run",
            kind="tool",
        ),
    ]


def build_vectors(
    api: dict[str, Any],
    connector: dict[str, Any],
    pointers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    vectors: list[dict[str, Any]] = [
        {
            "id": "discord_env_surface",
            "kind": "env_surface",
            "lane": LANE["id"],
            "env_name_count": len(API_ENV_NAMES),
            "enable_armed": api.get("enable_discord_armed"),
            "record_id": "discord:env_surface",
            "content_hash": stable_digest(api.get("env_present"))[:16],
            "asuna_point0_route": "perplexity_fable5_home_sim",
            "sensitivity": "env_names_only",
        },
        {
            "id": "discord_connector",
            "kind": "connector_pause",
            "lane": LANE["id"],
            "state": connector.get("state"),
            "record_id": "discord:connector",
            "content_hash": stable_digest(
                {"state": connector.get("state"), "path": connector.get("path")}
            )[:16],
            "asuna_point0_route": "perplexity_fable5_home_sim",
            "sensitivity": "local_metadata",
        },
        {
            "id": "discord_mcp_domain",
            "kind": "mcp_registry",
            "lane": LANE["id"],
            "domain": "status_notify",
            "record_id": "discord:mcp",
            "content_hash": stable_digest({"id": "discord", "domain": "status_notify"})[
                :16
            ],
            "asuna_point0_route": "perplexity_fable5_home_sim",
            "sensitivity": "public_metadata",
        },
    ]
    for p in pointers:
        if not p.get("exists"):
            continue
        rid = Path(str(p["path"])).name
        vectors.append(
            {
                "id": rid,
                "kind": "path_pointer",
                "role": p.get("role"),
                "path": p.get("path"),
                "lane": LANE["id"],
                "sha256_16": p.get("sha256_16"),
                "record_id": f"discord:ptr:{rid}",
                "content_hash": p.get("sha256_16") or stable_digest(p)[:16],
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "sensitivity": "local_path_only",
            }
        )
    return vectors


def build_unification() -> dict[str, Any]:
    point0 = asuna_point0()
    api = api_surface()
    connector = catalyst_connector_state()
    pointers = mesh_pointers()
    vectors = build_vectors(api, connector, pointers)
    bedrock = SG / "live" / "spacetime_alchemy" / "PERPLEXITY_CONTEXT_BEDROCK.md"
    compact = SG / "live" / "spacetime_alchemy" / "fable5-compact.json"
    state = "PAUSED"
    if api.get("enable_discord_armed") and connector.get("state") != "PAUSED":
        state = "armed_opt_in"
    elif api.get("enable_discord_armed"):
        state = "enable_flag_set_still_paused_default"
    core = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "phase": 2,
        "package_id": PACKAGE_ID,
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "q24_canonical_id": CANONICAL_ID,
        "lane": dict(LANE),
        "connector": {**connector, "effective_state": state},
        "unification_target": {
            "name": "perplexity_asuna_point_0",
            "point_0": "HOME",
            "archetype": "angela_asuna_home",
            "lane": "perplexity_fable5_synthesis",
            "role": "status_notify_surface",
            "meaning": (
                "Index Discord status_notify (paused by default) into Asuna Point-0 "
                "for Perplexity central control — metadata only."
            ),
        },
        "asuna_point0": point0,
        "api_surface": api,
        "mesh_pointers": pointers,
        "perplexity": {
            "bedrock": str(bedrock),
            "bedrock_exists": bedrock.is_file(),
            "compact": str(compact),
            "compact_exists": compact.is_file(),
            "bulk_upload_requires_explicit_approval": True,
        },
        "vectors": vectors,
        "metrics": {
            "vector_count": len(vectors),
            "env_present_count": sum(1 for v in api["env_present"].values() if v),
            "enable_discord_armed": bool(api.get("enable_discord_armed")),
            "connector_state": connector.get("state"),
            "effective_state": state,
            "webhook_posts": 0,
            "provider_calls": 0,
            "point0_manifest_ok": bool(point0.get("manifest_ok")),
        },
        "controls": dict(CONTROLS),
    }
    core["unification_digest"] = stable_digest(
        {
            "lane": LANE["id"],
            "vectors": [{"id": v["id"], "hash": v["content_hash"]} for v in vectors],
        }
    )
    core["ok"] = (
        bool(point0.get("manifest_ok") or point0.get("registry_exists"))
        and len(vectors) >= 3
        and CONTROLS["webhook_post"] is False
        and CONTROLS["scrape_channel_history"] is False
    )
    return core


def write_outputs(payload: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for path in (STATUS_OUT, DEFAULT_OUT, MIRROR_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unify Discord status_notify into Asuna Point-0 (paused default)"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test"],
    )
    args = parser.parse_args(argv)
    payload = build_unification()
    if args.command == "status":
        print(
            json.dumps(
                {
                    "ok": payload.get("ok"),
                    "lane": LANE,
                    "metrics": payload.get("metrics"),
                    "catalog": str(DEFAULT_OUT),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload.get("schema") == SCHEMA
        assert payload["lane"]["id"] == "discord_status_notify"
        assert payload["controls"]["webhook_post"] is False
        assert payload["metrics"]["vector_count"] >= 3
        print(
            json.dumps(
                {"ok": True, "checks": ["schema", "lane", "controls", "vectors"]},
                indent=2,
            )
        )
        return 0
    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
