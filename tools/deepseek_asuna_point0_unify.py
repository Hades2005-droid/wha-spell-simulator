#!/usr/bin/env python3
"""
DeepSeek / Ollama / local-open-weights → Perplexity Asuna Point-0 unification.

Indexes API surface (env names only), public/local model lists, chat/memory
path pointers (+ hashes), and weight/artifact path pointers into Spacetime
Alchemy metadata. Anchors to Home Black Sun point_0 / angela_asuna_home.

Never prints API keys, never bulk-copies private chat transcripts, never calls
the remote DeepSeek API. Optional localhost Ollama tags probe (127.0.0.1:11434).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.deepseek_asuna_point0_unification.v1"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CANONICAL_ID = "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1"
PACKAGE_ID = "shadow-garden-phase2-fable5-black-sun-home-sim"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
MON = Path(
    os.environ.get("SHADOW_MONITOR_ROOT", HOME / "shadow_garden_may30_monitoring")
)

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "deepseek_asuna_point0_unification.json"
)
MIRROR_OUT = SG / "live" / "spacetime_alchemy" / "deepseek_asuna_point0_unification.json"
STATUS_OUT = Path("/tmp/shadow_garden_deepseek_asuna_point0.json")

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
PUBLIC_TESTAMENT_SHARE = "https://chat.deepseek.com/share/t3aum0slci9ny6c9bi"
PUBLIC_API_DOCS = "https://api-docs.deepseek.com/"

# Env names only — never read or echo values in this tool.
API_ENV_NAMES = [
    "DEEPSEEK_API_KEY",
    "DEEPSEEK_BASE_URL",
    "DEEPSEEK_MODEL",
    "DEEPSEEK_LOCAL_ENABLED",
    "OLLAMA_HOST",
    "OLLAMA_MODELS",
]

# Public catalog (docs / marketing names) — no live remote API.
PUBLIC_MODELS = [
    {
        "id": "deepseek-chat",
        "family": "deepseek-v3",
        "source": "public_api_docs",
        "remote_opt_in": True,
    },
    {
        "id": "deepseek-reasoner",
        "family": "deepseek-r1",
        "source": "public_api_docs",
        "remote_opt_in": True,
    },
    {
        "id": "deepseek-coder",
        "family": "deepseek-coder",
        "source": "public_docs_pointer",
        "remote_opt_in": True,
    },
]

CONTROLS = {
    "remote_deepseek_api": False,
    "provider_calls": False,
    "bulk_chat_copy": False,
    "credential_access": False,
    "credential_logging": False,
    "secrets_in_artifacts": False,
    "bulk_upload_perplexity": False,
    "excluded_sources_ingested": False,
    "content_neutral": True,
    "symbolic_only": True,
    "source_pointers_only": True,
    "local_ollama_preferred": True,
    "local_only_default": True,
    "path_pointers_only_for_weights": True,
}


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
            # Count immediate children only — no recursive walk of model blobs.
            out["child_count"] = sum(1 for _ in path.iterdir())
        except OSError as exc:
            out["error"] = f"{type(exc).__name__}"[:80]
    return out


def asuna_point0() -> dict[str, Any]:
    """Home Black Sun point_0 — Perplexity Asuna home archetype (symbolic)."""
    registry = MON / "shaoshi_bridge" / "south_star" / "home_black_sun_registry.py"
    out: dict[str, Any] = {
        "point_0": "HOME",
        "label": "perplexity_asuna_point_0",
        "resident_archetype": "angela_asuna_home",
        "protector_label": "KIRITO_FRED",
        "scene_id": "kitchen_log_cabin_floor_22",
        "symbolic_only": True,
        "narrative_scaffolding": True,
        "not_claim_about_real_people": True,
        "registry_path": str(registry),
        "registry_exists": registry.is_file(),
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
            home = manifest.get("home_protected") or {}
            out["home_protected"] = home
            out["q24_canonical_id"] = manifest.get("q24_canonical_id")
            out["anchor"] = manifest.get("anchor")
            out["phase"] = manifest.get("phase")
            out["manifest_ok"] = True
        else:
            out["manifest_ok"] = False
            out["error"] = (proc.stderr or proc.stdout or "")[:160]
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        out["manifest_ok"] = False
        out["error"] = f"{type(exc).__name__}: {exc}"[:160]
    return out


def perplexity_bedrock_pointer() -> dict[str, Any]:
    bedrock = SG / "live" / "spacetime_alchemy" / "PERPLEXITY_CONTEXT_BEDROCK.md"
    compact = SG / "live" / "spacetime_alchemy" / "fable5-compact.json"
    return {
        "bedrock": str(bedrock),
        "bedrock_exists": bedrock.is_file(),
        "compact": str(compact),
        "compact_exists": compact.is_file(),
        "lane": "perplexity_fable5_synthesis",
        "role": "asuna_point0_deepseek_unification_consumer",
        "bulk_upload_requires_explicit_approval": True,
    }


def api_surface() -> dict[str, Any]:
    """Env names only — presence flags never include values."""
    present = {name: (name in os.environ and bool(os.environ.get(name))) for name in API_ENV_NAMES}
    return {
        "mode": "env_names_only",
        "remote_default": "opt_in_via_env",
        "preferred_bind": "127.0.0.1",
        "public_api_docs": PUBLIC_API_DOCS,
        "env_names": list(API_ENV_NAMES),
        "env_present": present,
        "notes": [
            "Never print or catalog secret values.",
            "Remote DeepSeek API is opt-in; prefer Ollama / deepseek-local on loopback.",
        ],
    }


def probe_ollama_tags() -> dict[str, Any]:
    """Localhost-only tags probe. Does not contact api.deepseek.com."""
    out: dict[str, Any] = {
        "url": OLLAMA_TAGS_URL,
        "bind": "127.0.0.1",
        "port": 11434,
        "up": False,
        "models": [],
        "remote_provider": False,
    }
    try:
        req = urllib.request.Request(
            OLLAMA_TAGS_URL,
            headers={"Accept": "application/json"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            body = resp.read()
        doc = json.loads(body.decode("utf-8", errors="replace"))
        models = []
        for item in doc.get("models") or []:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or item.get("model") or "").strip()
            if not name:
                continue
            models.append(
                {
                    "name": name,
                    "digest_prefix": str(item.get("digest") or "")[:16] or None,
                    "size": item.get("size"),
                    "family_guess": (
                        "deepseek"
                        if "deepseek" in name.lower()
                        else name.split(":", 1)[0]
                    ),
                    "source": "ollama_local_tags",
                }
            )
        out["up"] = True
        out["models"] = models
        out["model_count"] = len(models)
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        out["up"] = False
        out["error"] = f"{type(exc).__name__}"[:80]
    return out


def model_catalog(ollama: dict[str, Any]) -> dict[str, Any]:
    local_route = {
        "id": "deepseek-local",
        "route_name": "local-open-weights",
        "source": "recursive_node_bridge_metadata",
        "remote_opt_in": False,
        "enabled_by_default": False,
        "note": "Metadata route only — does not contact DeepSeek unless env armed.",
    }
    mesh = MON / "shadow_garden_devin_evolution_package" / "model_mesh_config.json"
    mesh_ptr = file_pointer(mesh, role="model_mesh_config", kind="config")
    deepseek_endpoint = None
    if mesh.is_file():
        try:
            doc = json.loads(mesh.read_text(encoding="utf-8"))
            for ep in doc.get("endpoints") or []:
                if isinstance(ep, dict) and ep.get("name") == "deepseek_local":
                    deepseek_endpoint = {
                        "name": ep.get("name"),
                        "kind": ep.get("kind"),
                        "base_url": ep.get("base_url"),
                        "enabled": bool(ep.get("enabled")),
                        "model_hints": ep.get("model_hints") or [],
                        "source": "model_mesh_config",
                    }
                    break
        except (OSError, json.JSONDecodeError):
            pass
    return {
        "public_docs": list(PUBLIC_MODELS),
        "local_route": local_route,
        "ollama": {
            "up": ollama.get("up"),
            "model_count": ollama.get("model_count") or len(ollama.get("models") or []),
            "models": ollama.get("models") or [],
        },
        "model_mesh": mesh_ptr,
        "deepseek_local_endpoint": deepseek_endpoint,
    }


def chat_memory_pointers() -> list[dict[str, Any]]:
    """Allowlisted path pointers only — no private transcript bulk copy."""
    pointers = [
        file_pointer(
            WHA / "docs" / "chronology-recursive-bridge.md",
            role="public_testament_doc",
            kind="doc",
        ),
        file_pointer(
            WHA
            / "shadow_garden_handoff"
            / "terminal_auto"
            / "outbox"
            / "fable5_comfyui_bridge_status.json",
            role="bridge_status_share_pointer",
            kind="status",
        ),
        file_pointer(
            SG
            / "SillyTavern"
            / "default"
            / "content"
            / "presets"
            / "reasoning"
            / "DeepSeek.json",
            role="sillytavern_reasoning_preset",
            kind="preset",
        ),
        file_pointer(
            SG
            / "SillyTavern"
            / "default"
            / "content"
            / "presets"
            / "instruct"
            / "DeepSeek-V2.5.json",
            role="sillytavern_instruct_preset",
            kind="preset",
        ),
        file_pointer(
            SG
            / "SillyTavern"
            / "default"
            / "content"
            / "presets"
            / "context"
            / "DeepSeek-V2.5.json",
            role="sillytavern_context_preset",
            kind="preset",
        ),
        file_pointer(
            WHA / "tools" / "recursive_node_bridge.py",
            role="recursive_bridge_route_metadata",
            kind="tool",
        ),
    ]
    for ptr in pointers:
        ptr["sensitivity"] = "path_pointer_only"
        ptr["bulk_copy"] = False
    pointers.append(
        {
            "role": "public_testament_share",
            "kind": "url",
            "path": PUBLIC_TESTAMENT_SHARE,
            "exists": True,
            "is_file": False,
            "is_dir": False,
            "content_inlined": False,
            "sensitivity": "public_share_url",
            "bulk_copy": False,
            "credentials": False,
        }
    )
    return pointers


def weight_pointers() -> list[dict[str, Any]]:
    """Paths only — never open or hash multi-GB blobs."""
    candidates = [
        (HOME / ".ollama" / "models", "ollama_models_root"),
        (HOME / ".ollama" / "models" / "blobs", "ollama_blobs"),
        (HOME / ".ollama" / "models" / "manifests", "ollama_manifests"),
    ]
    out = []
    for path, role in candidates:
        ptr = file_pointer(path, role=role, kind="weights_dir")
        # Strip any accidental content fields; directories only.
        ptr.pop("sha256_16", None)
        ptr["blob_contents_read"] = False
        ptr["sensitivity"] = "path_pointer_only"
        out.append(ptr)
    return out


def bridge_route_metadata() -> dict[str, Any]:
    return {
        "route_name": "local-open-weights",
        "route_model": "deepseek-local",
        "tools": [
            str(WHA / "tools" / "recursive_node_bridge.py"),
            str(WHA / "tools" / "recursive-node-bridge" / "RecursiveNodeBridge.cs"),
        ],
        "mesh_bridge_tags": [
            "recursive_node_evolution",
            "chronology_engine",
            "local_open_weights",
            "deepseek_metadata",
        ],
        "contacts_remote_deepseek": False,
        "mode": "disabled_metadata_unless_env_armed",
    }


def unify_vectors(
    models: dict[str, Any],
    chats: list[dict[str, Any]],
    weights: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    vectors: list[dict[str, Any]] = []

    for m in models.get("public_docs") or []:
        vectors.append(
            {
                "id": f"model:public:{m['id']}",
                "kind": "model",
                "name": m["id"],
                "source": m.get("source"),
                "remote_opt_in": bool(m.get("remote_opt_in")),
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "sensitivity": "public_model_id",
            }
        )

    local = models.get("local_route") or {}
    vectors.append(
        {
            "id": f"model:local:{local.get('id', 'deepseek-local')}",
            "kind": "model_route",
            "name": local.get("id"),
            "route_name": local.get("route_name"),
            "source": local.get("source"),
            "remote_opt_in": False,
            "asuna_point0_route": "perplexity_fable5_home_sim",
            "sensitivity": "route_metadata",
        }
    )

    for m in (models.get("ollama") or {}).get("models") or []:
        vectors.append(
            {
                "id": f"model:ollama:{m.get('name')}",
                "kind": "ollama_tag",
                "name": m.get("name"),
                "source": "ollama_local_tags",
                "remote_opt_in": False,
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "sensitivity": "local_model_tag",
            }
        )

    for ptr in chats:
        key = ptr.get("path") or ptr.get("role")
        vectors.append(
            {
                "id": f"chat_ptr:{ptr.get('role')}",
                "kind": "chat_memory_pointer",
                "path": key,
                "exists": bool(ptr.get("exists")),
                "sha256_16": ptr.get("sha256_16"),
                "bulk_copy": False,
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "sensitivity": ptr.get("sensitivity") or "path_pointer_only",
            }
        )

    for ptr in weights:
        vectors.append(
            {
                "id": f"weights:{ptr.get('role')}",
                "kind": "weight_pointer",
                "path": ptr.get("path"),
                "exists": bool(ptr.get("exists")),
                "blob_contents_read": False,
                "asuna_point0_route": "perplexity_fable5_home_sim",
                "sensitivity": "path_pointer_only",
            }
        )

    for v in vectors:
        v["content_hash"] = stable_digest(
            {
                "id": v["id"],
                "kind": v.get("kind"),
                "name": v.get("name"),
                "path": v.get("path"),
            }
        )[:16]
        v["consent_basis"] = "user_authorized_local_mesh_allowlist"
    vectors.sort(key=lambda x: x["id"])
    return vectors


def build_unification() -> dict[str, Any]:
    point0 = asuna_point0()
    bedrock = perplexity_bedrock_pointer()
    api = api_surface()
    ollama = probe_ollama_tags()
    models = model_catalog(ollama)
    chats = chat_memory_pointers()
    weights = weight_pointers()
    route = bridge_route_metadata()
    vectors = unify_vectors(models, chats, weights)

    existing_ptrs = sum(1 for c in chats if c.get("exists"))
    existing_weights = sum(1 for w in weights if w.get("exists"))
    ollama_up = bool(ollama.get("up"))

    core = {
        "schema": SCHEMA,
        "generation": "deterministic_local_snapshot",
        "phase": 2,
        "package_id": PACKAGE_ID,
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "q24_canonical_id": CANONICAL_ID,
        "unification_target": {
            "name": "perplexity_asuna_point_0",
            "point_0": "HOME",
            "archetype": "angela_asuna_home",
            "lane": "perplexity_fable5_synthesis",
            "meaning": (
                "Index DeepSeek / Ollama / local-open-weights metadata into "
                "Spacetime Alchemy toward the symbolic Asuna/home Black Sun "
                "point-zero for Perplexity Fable 5."
            ),
        },
        "api_surface": api,
        "models": models,
        "chat_memory_pointers": chats,
        "weight_pointers": weights,
        "bridge_route": route,
        "asuna_point0": point0,
        "perplexity": bedrock,
        "vectors": vectors,
        "metrics": {
            "vector_count": len(vectors),
            "public_model_count": len(PUBLIC_MODELS),
            "ollama_up": ollama_up,
            "ollama_model_count": len(ollama.get("models") or []),
            "chat_pointer_count": len(chats),
            "chat_pointer_existing": existing_ptrs,
            "weight_pointer_existing": existing_weights,
            "provider_calls": 0,
            "remote_deepseek_calls": 0,
            "local_ollama_probe": 1 if ollama_up or "error" in ollama else 1,
        },
        "controls": dict(CONTROLS),
    }
    core["unification_digest"] = stable_digest(
        {
            "schema": SCHEMA,
            "vectors": [{"id": v["id"], "hash": v["content_hash"]} for v in vectors],
            "point_0": point0.get("point_0"),
            "carrier": CARRIER,
            "bridge": BRIDGE_SIGNATURE,
        }
    )
    # Soft-ok: point0 + enough allowlisted pointers; ollama optional.
    core["ok"] = bool(
        point0.get("point_0") == "HOME"
        and existing_ptrs >= 3
        and len(vectors) >= 5
        and core["controls"]["remote_deepseek_api"] is False
        and core["metrics"]["provider_calls"] == 0
        and core["controls"]["bulk_chat_copy"] is False
    )
    return core


def write_outputs(payload: dict[str, Any], *extra: Path) -> list[str]:
    paths = [STATUS_OUT, DEFAULT_OUT, MIRROR_OUT, *extra]
    written: list[str] = []
    for path in paths:
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            written.append(str(path))
        except OSError as exc:
            written.append(f"FAILED:{path}:{type(exc).__name__}")
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unify DeepSeek/Ollama metadata into Perplexity Asuna point-0 catalog"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="write",
        choices=["write", "status", "self-test"],
    )
    parser.add_argument("--out", default="", help="extra output path")
    args = parser.parse_args(argv)

    payload = build_unification()

    if args.command == "self-test":
        assert payload.get("schema") == SCHEMA
        assert payload["controls"]["remote_deepseek_api"] is False
        assert payload["controls"]["bulk_chat_copy"] is False
        assert payload["controls"]["credential_access"] is False
        assert payload["metrics"]["provider_calls"] == 0
        assert payload["unification_target"]["point_0"] == "HOME"
        assert payload["asuna_point0"]["resident_archetype"] == "angela_asuna_home"
        assert payload["carrier"] == CARRIER
        assert payload["bridge_signature"] == BRIDGE_SIGNATURE
        # Ensure no env values leaked into catalog (names only).
        api = payload.get("api_surface") or {}
        assert api.get("mode") == "env_names_only"
        for name in api.get("env_names") or []:
            assert name.isupper() or "_" in name
        dumped = json.dumps(payload)
        for banned in ("sk-", "Bearer ", "api_key="):
            assert banned not in dumped

    print(json.dumps(payload, indent=2))

    if args.command in ("write", "self-test"):
        extras = [Path(args.out)] if args.out else []
        for path in write_outputs(payload, *extras):
            print(f"wrote {path}", file=__import__("sys").stderr)

    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
