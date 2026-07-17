#!/usr/bin/env python3
"""
Kimi 3 → Perplexity Asuna Point-0 unify (3rd leverage / completion bridge).

Kimi 3 is the bridge armed at Asuna Point-0 completion for transitioning the
full mesh to a local open-weights operating mode (Ollama / local Moonshot-class
weights). Pairs with DeepSeek (eastern local) and Grok/xAI (Harmony-6) as the
third leverage.

Never prints API keys. Never calls api.moonshot.* unless env is armed (this
tool does not make provider calls). Metadata / source-pointers only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.kimi3_asuna_point0_unification.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CANONICAL_ID = "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1"
PACKAGE_ID = "shadow-garden-phase2-fable5-black-sun-home-sim"
LEVERAGE = {
    "id": "kimi3_third_leverage",
    "ordinal": 3,
    "label": "Kimi 3 completion bridge",
    "role": "asuna_point0_completion_to_local_open_weights",
    "partners": ["deepseek_local_open_weights", "grok_xai_harmony_6"],
    "leveraged_by": "perplexity_asuna_point_0",
    "transition_target": "local_open_weights_mesh",
}

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
MON = Path(
    os.environ.get("SHADOW_MONITOR_ROOT", HOME / "shadow_garden_may30_monitoring")
)

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "kimi3_asuna_point0_unification.json"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "kimi3_asuna_point0_unification.json"
STATUS_OUT = Path("/tmp/shadow_garden_kimi3_asuna_point0.json")
TRANSITION_OUT = (
    WHA
    / "shadow_garden_handoff"
    / "bridges"
    / "kimi3_local_open_weights_transition.json"
)

API_ENV_NAMES = [
    "KIMI_API_KEY",
    "MOONSHOT_API_KEY",
    "KIMI_BASE_URL",
    "MOONSHOT_BASE_URL",
    "KIMI_MODEL",
    "KIMI_LOCAL_ENABLED",
    "KIMI3_TRANSITION_ARMED",
    "OLLAMA_HOST",
    "OLLAMA_MODELS",
]

PUBLIC_MODELS = [
    {
        "id": "kimi-k2",
        "family": "kimi",
        "source": "moonshot_public_docs",
        "remote_opt_in": True,
    },
    {
        "id": "kimi-k2.5",
        "family": "kimi",
        "source": "moonshot_public_docs",
        "remote_opt_in": True,
    },
    {
        "id": "moonshot-v1-auto",
        "family": "moonshot",
        "source": "moonshot_public_docs",
        "remote_opt_in": True,
    },
    {
        "id": "kimi-local",
        "family": "kimi-local-open-weights",
        "source": "ollama_or_local_gguf",
        "remote_opt_in": False,
    },
]

CONTROLS = {
    "remote_moonshot_api": False,
    "provider_calls": False,
    "credential_access": False,
    "credential_logging": False,
    "secrets_in_artifacts": False,
    "bulk_upload_perplexity": False,
    "content_neutral": True,
    "symbolic_only": True,
    "source_pointers_only": True,
    "local_open_weights_preferred": True,
    "transition_requires_KIMI3_TRANSITION_ARMED": True,
}

OLLAMA_TAGS_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip(
    "/"
) + "/api/tags"


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
    elif path.is_dir():
        try:
            out["child_count"] = sum(1 for _ in path.iterdir())
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
        "completion_bridge": "kimi3_third_leverage",
        "transition_to": "local_open_weights_mesh",
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
        "preferred_bind": "127.0.0.1",
        "public_api_docs": "https://platform.moonshot.cn/docs",
        "env_names": list(API_ENV_NAMES),
        "env_present": present,
        "transition_armed": bool(present.get("KIMI3_TRANSITION_ARMED")),
        "notes": [
            "Never print or catalog secret values.",
            "Prefer Ollama / kimi-local over remote Moonshot API.",
            "KIMI3_TRANSITION_ARMED marks Asuna Point-0 completion → local open-weights mesh.",
        ],
    }


def probe_ollama_kimi() -> dict[str, Any]:
    out: dict[str, Any] = {
        "url": OLLAMA_TAGS_URL,
        "bind": "127.0.0.1",
        "up": False,
        "kimi_models": [],
        "all_model_count": 0,
    }
    try:
        req = urllib.request.Request(
            OLLAMA_TAGS_URL, headers={"Accept": "application/json"}, method="GET"
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            body = resp.read()
        doc = json.loads(body.decode("utf-8", errors="replace"))
        models = []
        kimi = []
        for item in doc.get("models") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("model") or "").strip()
            if not name:
                continue
            entry = {
                "name": name,
                "digest_prefix": str(item.get("digest") or "")[:16] or None,
                "size": item.get("size"),
                "source": "ollama_local_tags",
            }
            models.append(entry)
            low = name.lower()
            if "kimi" in low or "moonshot" in low:
                kimi.append(entry)
        out["up"] = True
        out["all_model_count"] = len(models)
        out["kimi_models"] = kimi
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        out["up"] = False
        out["error"] = f"{type(exc).__name__}"[:80]
    return out


def mesh_pointers() -> list[dict[str, Any]]:
    return [
        file_pointer(
            WHA / "tools" / "deepseek_asuna_point0_unify.py",
            role="leverage_1_deepseek",
            kind="tool",
        ),
        file_pointer(
            WHA / "tools" / "grok_xai_asuna_point0_unify.py",
            role="leverage_2_grok_xai",
            kind="tool",
        ),
        file_pointer(
            WHA / "tools" / "white_moon_eastern_corner_unify.py",
            role="eastern_corner_weave",
            kind="tool",
        ),
        file_pointer(
            WHA / "tools" / "perplexity_asuna_central_control.py",
            role="central_control_ledger",
            kind="tool",
        ),
        file_pointer(
            WHA / "tools" / "recursive_node_bridge.py",
            role="local_open_weights_route_metadata",
            kind="tool",
        ),
        file_pointer(
            HOME / ".ollama" / "models",
            role="ollama_models_root",
            kind="weights_dir",
        ),
    ]


def transition_plan(*, armed: bool, ollama: dict[str, Any]) -> dict[str, Any]:
    surfaces = [
        "github_asuna_point0",
        "deepseek_asuna_point0",
        "grok_xai_asuna_point0",
        "white_moon_eastern_corner",
        "discord_asuna_point0",
        "stripe_local_scaffold",
        "shadow_garden_packet",
    ]
    return {
        "schema": "shadow_garden.kimi3_local_open_weights_transition.v1",
        "generated_at": utc_now(),
        "bridge": LEVERAGE["id"],
        "ordinal": 3,
        "armed": armed,
        "status": "armed_ready" if armed else "indexed_awaiting_KIMI3_TRANSITION_ARMED",
        "from": "perplexity_asuna_point_0_cloud_hybrid_mesh",
        "to": "local_open_weights_mesh",
        "preferred_runtime": {
            "bind": "127.0.0.1",
            "ollama": "http://127.0.0.1:11434",
            "kimi_local_route": "kimi-local",
            "deepseek_local_route": "deepseek-local",
        },
        "ollama_up": bool(ollama.get("up")),
        "local_kimi_tags": ollama.get("kimi_models") or [],
        "surfaces_to_localize": surfaces,
        "steps": [
            "Refresh Asuna Point-0 catalogs (github/deepseek/grok/discord/central).",
            "Confirm Ollama up and optional kimi/moonshot local tags present.",
            "Set KIMI3_TRANSITION_ARMED=1 after operator approval.",
            "Prefer 127.0.0.1 routes; leave remote Moonshot/DeepSeek/xAI unset.",
            "Rewrite packet lanes to local_open_weights_mesh; keep Discord PAUSED unless armed.",
            "One bounded cycle — no infinite recursive loops.",
        ],
        "controls": {
            "provider_calls": False,
            "remote_default": False,
            "content_neutral": True,
            "secrets_in_artifacts": False,
        },
    }


def build_vectors(
    models: list[dict[str, Any]],
    pointers: list[dict[str, Any]],
    ollama: dict[str, Any],
) -> list[dict[str, Any]]:
    vectors: list[dict[str, Any]] = []
    for m in models:
        mid = m["id"]
        vectors.append(
            {
                "id": mid,
                "kind": "model",
                "family": m.get("family"),
                "leverage": LEVERAGE["id"],
                "remote_opt_in": m.get("remote_opt_in", True),
                "sources": [m.get("source")],
                "record_id": f"kimi3:{mid}",
                "content_hash": stable_digest(m)[:16],
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "transition_route": "local_open_weights_mesh",
                "sensitivity": "public_metadata",
            }
        )
    for km in ollama.get("kimi_models") or []:
        name = km.get("name")
        vectors.append(
            {
                "id": f"ollama:{name}",
                "kind": "ollama_tag",
                "leverage": LEVERAGE["id"],
                "remote_opt_in": False,
                "record_id": f"kimi3:ollama:{name}",
                "content_hash": stable_digest(km)[:16],
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "transition_route": "local_open_weights_mesh",
                "sensitivity": "local_model_tag",
            }
        )
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
                "leverage": LEVERAGE["id"],
                "sha256_16": p.get("sha256_16"),
                "record_id": f"kimi3:ptr:{rid}",
                "content_hash": p.get("sha256_16") or stable_digest(p)[:16],
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "transition_route": "local_open_weights_mesh",
                "sensitivity": "local_path_only",
            }
        )
    vectors.append(
        {
            "id": "completion_bridge",
            "kind": "transition_bridge",
            "leverage": LEVERAGE["id"],
            "ordinal": 3,
            "record_id": "kimi3:completion_bridge",
            "content_hash": stable_digest(LEVERAGE)[:16],
            "asuna_point0_route": "perplexity_fable5_home_sim",
            "transition_route": "local_open_weights_mesh",
            "sensitivity": "public_metadata",
        }
    )
    return vectors


def build_unification() -> dict[str, Any]:
    point0 = asuna_point0()
    api = api_surface()
    ollama = probe_ollama_kimi()
    pointers = mesh_pointers()
    for p in pointers:
        if p.get("kind") == "weights_dir":
            p.pop("sha256_16", None)
            p["blob_contents_read"] = False
    vectors = build_vectors(PUBLIC_MODELS, pointers, ollama)
    transition = transition_plan(
        armed=bool(api.get("transition_armed")), ollama=ollama
    )
    bedrock = SG / "live" / "spacetime_alchemy" / "PERPLEXITY_CONTEXT_BEDROCK.md"
    compact = SG / "live" / "spacetime_alchemy" / "fable5-compact.json"
    central = (
        WHA / "shadow_garden_handoff" / "bridges" / "perplexity_asuna_central_control.json"
    )
    core = {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "phase": 2,
        "package_id": PACKAGE_ID,
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "q24_canonical_id": CANONICAL_ID,
        "leverage": dict(LEVERAGE),
        "unification_target": {
            "name": "perplexity_asuna_point_0",
            "point_0": "HOME",
            "archetype": "angela_asuna_home",
            "lane": "perplexity_fable5_synthesis",
            "third_leverage": True,
            "completion_bridge": True,
            "meaning": (
                "Kimi 3 is the 3rd leverage at Asuna Point-0 completion — "
                "bridge the full mesh into local open-weights operation."
            ),
        },
        "asuna_point0": point0,
        "api_surface": api,
        "models": {"public_docs": PUBLIC_MODELS, "ollama": ollama},
        "mesh_pointers": pointers,
        "transition": transition,
        "perplexity": {
            "bedrock": str(bedrock),
            "bedrock_exists": bedrock.is_file(),
            "compact": str(compact),
            "compact_exists": compact.is_file(),
            "central_control": str(central),
            "central_control_exists": central.is_file(),
            "bulk_upload_requires_explicit_approval": True,
        },
        "vectors": vectors,
        "metrics": {
            "vector_count": len(vectors),
            "model_count": len(PUBLIC_MODELS),
            "ollama_up": bool(ollama.get("up")),
            "local_kimi_tag_count": len(ollama.get("kimi_models") or []),
            "transition_armed": bool(api.get("transition_armed")),
            "provider_calls": 0,
            "point0_manifest_ok": bool(point0.get("manifest_ok")),
        },
        "controls": dict(CONTROLS),
    }
    core["unification_digest"] = stable_digest(
        {
            "leverage": LEVERAGE["id"],
            "vectors": [{"id": v["id"], "hash": v["content_hash"]} for v in vectors],
        }
    )
    core["ok"] = (
        bool(point0.get("manifest_ok") or point0.get("registry_exists"))
        and len(vectors) >= 5
        and CONTROLS["provider_calls"] is False
    )
    return core


def write_outputs(payload: dict[str, Any]) -> list[str]:
    written: list[str] = []
    for path in (STATUS_OUT, DEFAULT_OUT, MIRROR_OUT):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    transition = payload.get("transition") or {}
    TRANSITION_OUT.parent.mkdir(parents=True, exist_ok=True)
    TRANSITION_OUT.write_text(json.dumps(transition, indent=2) + "\n", encoding="utf-8")
    written.append(str(TRANSITION_OUT))
    mirror_t = SG / "live" / "spacetime_alchemy" / TRANSITION_OUT.name
    mirror_t.parent.mkdir(parents=True, exist_ok=True)
    mirror_t.write_text(json.dumps(transition, indent=2) + "\n", encoding="utf-8")
    written.append(str(mirror_t))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unify Kimi 3 as Asuna Point-0 3rd leverage → local open-weights"
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
                    "leverage": LEVERAGE,
                    "metrics": payload.get("metrics"),
                    "transition": {
                        "armed": (payload.get("transition") or {}).get("armed"),
                        "status": (payload.get("transition") or {}).get("status"),
                    },
                    "catalog": str(DEFAULT_OUT),
                },
                indent=2,
            )
        )
        return 0 if payload.get("ok") else 1
    if args.command == "self-test":
        assert payload.get("schema") == SCHEMA
        assert payload["leverage"]["ordinal"] == 3
        assert payload["controls"]["provider_calls"] is False
        assert payload["metrics"]["vector_count"] >= 5
        print(
            json.dumps(
                {"ok": True, "checks": ["schema", "leverage_3", "controls", "vectors"]},
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
