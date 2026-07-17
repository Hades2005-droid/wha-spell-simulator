#!/usr/bin/env python3
"""
Grok / xAI → Perplexity Asuna Point-0 unification (eastern white-moon corner).

Indexes env-name API surface, public model catalog, local mesh pointers, and
Grok CLI presence into Spacetime Alchemy metadata. Pairs with DeepSeek as the
eastern / white-moon core of Asuna Point-0 Perplexity unification.

Never prints API keys. Never calls api.x.ai unless env is armed (this tool does
not make provider calls). Metadata / source-pointers only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.grok_xai_asuna_point0_unification.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CANONICAL_ID = "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1"
PACKAGE_ID = "shadow-garden-phase2-fable5-black-sun-home-sim"
CORNER = {
    "id": "eastern_white_moon",
    "tarot": "Moon_18",
    "role": "eastern_core_corner",
    "partners": ["deepseek_local_open_weights", "grok_xai"],
    "leveraged_by": "perplexity_asuna_point_0",
}

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
MON = Path(
    os.environ.get("SHADOW_MONITOR_ROOT", HOME / "shadow_garden_may30_monitoring")
)

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "grok_xai_asuna_point0_unification.json"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "grok_xai_asuna_point0_unification.json"
STATUS_OUT = Path("/tmp/shadow_garden_grok_xai_asuna_point0.json")

API_ENV_NAMES = [
    "XAI_API_KEY",
    "XAI_BASE_URL",
    "GROK_TEXT_MODEL",
    "GROK_VOICE_MODEL",
    "GROK_IMAGE_MODEL",
    "GROK_VIDEO_MODEL",
    "GROK_AUDIO_MODEL",
    "GROK_QWEN_MODEL",
    "GROK_QWEN2_MODEL",
    "GROK_QWEN3_MODEL",
]

PUBLIC_MODELS = [
    {"id": "grok-3", "family": "grok-text", "source": "xai_public_docs", "remote_opt_in": True},
    {"id": "grok-4", "family": "grok-text", "source": "xai_public_docs", "remote_opt_in": True},
    {"id": "grok-voice-latest", "family": "grok-voice", "source": "env_default", "remote_opt_in": True},
    {"id": "grok-image-latest", "family": "grok-image", "source": "env_default", "remote_opt_in": True},
    {"id": "grok-video-latest", "family": "grok-video", "source": "env_default", "remote_opt_in": True},
    {"id": "grok-audio-latest", "family": "grok-audio", "source": "env_default", "remote_opt_in": True},
]

CONTROLS = {
    "remote_xai_api": False,
    "provider_calls": False,
    "credential_access": False,
    "credential_logging": False,
    "secrets_in_artifacts": False,
    "bulk_upload_perplexity": False,
    "content_neutral": True,
    "symbolic_only": True,
    "source_pointers_only": True,
    "local_mesh_preferred": True,
}


def stable_digest(payload: Any) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


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
        "eastern_white_moon_corner": True,
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
    return {
        "mode": "env_names_only",
        "remote_default": "opt_in_via_env",
        "public_docs": "https://docs.x.ai/",
        "env_names": list(API_ENV_NAMES),
        "env_present": present,
        "notes": [
            "Never print or catalog secret values.",
            "Grok/xAI is Harmony-6 back lane; DeepSeek is local-open-weights east.",
        ],
    }


def grok_cli_presence() -> dict[str, Any]:
    path = shutil.which("grok")
    out: dict[str, Any] = {"on_path": bool(path), "path": path}
    if not path:
        return out
    try:
        proc = subprocess.run(
            [path, "--version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        out["version_preview"] = ((proc.stdout or proc.stderr or "")[:120]).strip()
        out["ok"] = proc.returncode == 0
    except (OSError, subprocess.SubprocessError) as exc:
        out["ok"] = False
        out["error"] = f"{type(exc).__name__}"[:80]
    return out


def mesh_pointers() -> list[dict[str, Any]]:
    return [
        file_pointer(
            WHA / "tools" / "shadow_garden_bridge.py",
            role="grok_model_env_bridge",
            kind="code",
        ),
        file_pointer(
            WHA
            / "shadow_garden_handoff"
            / "shaoshi_bridge"
            / "outbox"
            / "grok_45_harmony_6_shadow_lane.json",
            role="harmony_6_lane_map",
            kind="handoff",
        ),
        file_pointer(
            SG / "live" / "spacetime_alchemy" / "jing_power_latest.json",
            role="jing_power_fuel",
            kind="telemetry",
        ),
        file_pointer(
            HOME / ".grok",
            role="grok_cli_home",
            kind="dir_pointer",
        ),
    ]


def build_vectors(
    models: list[dict[str, Any]], pointers: list[dict[str, Any]], cli: dict[str, Any]
) -> list[dict[str, Any]]:
    vectors: list[dict[str, Any]] = []
    for m in models:
        mid = m["id"]
        vectors.append(
            {
                "id": mid,
                "kind": "model",
                "family": m.get("family"),
                "corner": CORNER["id"],
                "remote_opt_in": m.get("remote_opt_in", True),
                "sources": [m.get("source")],
                "record_id": f"xai:{mid}",
                "content_hash": stable_digest(m)[:16],
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "sensitivity": "public_metadata",
            }
        )
    for p in pointers:
        if not p.get("exists"):
            continue
        rid = Path(p["path"]).name
        vectors.append(
            {
                "id": rid,
                "kind": "path_pointer",
                "role": p.get("role"),
                "path": p.get("path"),
                "corner": CORNER["id"],
                "sha256_16": p.get("sha256_16"),
                "record_id": f"xai:ptr:{rid}",
                "content_hash": (p.get("sha256_16") or stable_digest(p)[:16]),
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "sensitivity": "local_path_only",
            }
        )
    vectors.append(
        {
            "id": "grok_cli",
            "kind": "cli_presence",
            "on_path": cli.get("on_path"),
            "corner": CORNER["id"],
            "record_id": "xai:cli:grok",
            "content_hash": stable_digest({"on_path": cli.get("on_path")})[:16],
            "asuna_point0_route": "perplexity_fable5_home_sim",
            "sensitivity": "local_tooling",
        }
    )
    return vectors


def build_unification() -> dict[str, Any]:
    point0 = asuna_point0()
    api = api_surface()
    cli = grok_cli_presence()
    pointers = mesh_pointers()
    vectors = build_vectors(PUBLIC_MODELS, pointers, cli)
    bedrock = SG / "live" / "spacetime_alchemy" / "PERPLEXITY_CONTEXT_BEDROCK.md"
    compact = SG / "live" / "spacetime_alchemy" / "fable5-compact.json"
    core = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "phase": 2,
        "package_id": PACKAGE_ID,
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "q24_canonical_id": CANONICAL_ID,
        "corner": dict(CORNER),
        "unification_target": {
            "name": "perplexity_asuna_point_0",
            "point_0": "HOME",
            "archetype": "angela_asuna_home",
            "lane": "perplexity_fable5_synthesis",
            "eastern_white_moon": True,
            "meaning": (
                "Index Grok/xAI (Harmony-6) with DeepSeek local-open-weights as the "
                "eastern white-moon corner leveraged by Asuna Point-0."
            ),
        },
        "asuna_point0": point0,
        "api_surface": api,
        "models": {"public_docs": PUBLIC_MODELS},
        "grok_cli": cli,
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
            "model_count": len(PUBLIC_MODELS),
            "pointer_exists": sum(1 for p in pointers if p.get("exists")),
            "xai_key_present": bool(api["env_present"].get("XAI_API_KEY")),
            "grok_cli_on_path": bool(cli.get("on_path")),
            "point0_manifest_ok": bool(point0.get("manifest_ok")),
        },
        "controls": dict(CONTROLS),
    }
    core["unification_digest"] = stable_digest(
        {
            "corner": CORNER["id"],
            "vectors": [{"id": v["id"], "hash": v["content_hash"]} for v in vectors],
        }
    )
    core["ok"] = bool(
        point0.get("manifest_ok") or point0.get("registry_exists")
    ) and len(vectors) >= 4
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
        description="Unify Grok/xAI into Asuna Point-0 eastern white-moon corner"
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
                    "corner": CORNER,
                    "metrics": payload.get("metrics"),
                    "catalog": str(DEFAULT_OUT),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload.get("schema") == SCHEMA
        assert payload["corner"]["id"] == "eastern_white_moon"
        assert payload["metrics"]["vector_count"] >= 4
        assert payload["controls"]["provider_calls"] is False
        print(json.dumps({"ok": True, "checks": ["schema", "corner", "vectors", "controls"]}, indent=2))
        return 0
    written = write_outputs(payload)
    print(json.dumps(payload, indent=2))
    for w in written:
        print(f"wrote {w}", file=__import__("sys").stderr)
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
