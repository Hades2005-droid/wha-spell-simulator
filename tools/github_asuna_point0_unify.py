#!/usr/bin/env python3
"""
GitHub profile → Perplexity Asuna Point-0 unification.

Indexes the authorized Hades2005-droid GitHub pointer and local mesh paths into
Spacetime Alchemy metadata/source-pointers only. Anchors to the
Home Black Sun point_0 / angela_asuna_home archetype for Perplexity Fable 5.

Never performs provider calls, reads credentials, clones repos, or scrapes content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.github_asuna_point0_unification.v1"
OWNER = "Hades2005-droid"
PROFILE_URL = f"https://github.com/{OWNER}"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CANONICAL_ID = "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1"
PACKAGE_ID = "shadow-garden-phase2-fable5-black-sun-home-sim"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
MESH = HOME / "shadow_garden_mesh"
MON = Path(
    os.environ.get("SHADOW_MONITOR_ROOT", HOME / "shadow_garden_may30_monitoring")
)

DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "bridges" / "github_asuna_point0_unification.json"
)
STATUS_OUT = Path("/tmp/shadow_garden_github_asuna_point0.json")

CONTROLS = {
    "external_fetch": False,
    "bulk_clone": False,
    "private_repo_harvest": False,
    "credential_access": False,
    "credential_logging": False,
    "provider_calls": False,
    "secrets_in_artifacts": False,
    "excluded_sources_ingested": False,
    "content_neutral": True,
    "symbolic_only": True,
    "github_pointer_only": True,
    "source_pointers_only": True,
    "local_only": True,
}


def stable_digest(payload: Any) -> str:
    canonical = json.dumps(
        payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def local_profile_pointer() -> dict[str, Any]:
    """Return a stable pointer without contacting GitHub."""
    return {
        "ok": True,
        "login": OWNER,
        "html_url": PROFILE_URL,
        "mode": "pointer_only",
        "fetched": False,
        "authority": "local_allowlisted_mesh_registry",
    }


def mesh_surfaces() -> dict[str, Any]:
    reg = MESH / "MESH_REGISTRY.json"
    if not reg.is_file():
        return {"ok": False, "error": "mesh_registry_missing", "surfaces": []}
    try:
        doc = json.loads(reg.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)[:160], "surfaces": []}

    surfaces: list[dict[str, Any]] = []
    live = doc.get("live_repos") or {}
    for key, meta in live.items():
        if not isinstance(meta, dict):
            continue
        path = Path(str(meta.get("path") or ""))
        surfaces.append(
            {
                "id": meta.get("id") or key,
                "role": meta.get("role"),
                "github": meta.get("github"),
                "path": str(path) if path else None,
                "exists": path.is_dir() if path else False,
                "head": meta.get("head"),
                "source": "mesh_registry_live_repos",
            }
        )
    for section in ("clones", "worktrees"):
        block = doc.get(section) or {}
        for key, meta in block.items():
            if not isinstance(meta, dict):
                continue
            path = Path(str(meta.get("path") or ""))
            surfaces.append(
                {
                    "id": key,
                    "role": section,
                    "github": None,
                    "path": str(path) if path else None,
                    "exists": path.is_dir() if path else False,
                    "head": meta.get("head"),
                    "source": f"mesh_registry_{section}",
                }
            )
    return {
        "ok": True,
        "path": str(reg),
        "perplexity_task": doc.get("perplexity_task"),
        "surface_count": len(surfaces),
        "surfaces": surfaces,
    }


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
        "role": "asuna_point0_unification_consumer",
    }


def unify_vectors(
    profile: dict[str, Any],
    mesh: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build deterministic vectors from the local allowlisted mesh."""
    by_name: dict[str, dict[str, Any]] = {}

    for surface in mesh.get("surfaces") or []:
        sid = str(surface.get("id") or "")
        gh = surface.get("github")
        name = sid
        if isinstance(gh, str) and "/" in gh:
            name = gh.split("/", 1)[1]
        entry = by_name.setdefault(
            name,
            {
                "id": name,
                "github": gh,
                "html_url": f"https://github.com/{gh}" if gh else None,
                "sources": [],
                "local_paths": [],
                "roles": [],
            },
        )
        src = surface.get("source")
        if src and src not in entry["sources"]:
            entry["sources"].append(src)
        if gh and not entry.get("github"):
            entry["github"] = gh
            entry["html_url"] = f"https://github.com/{gh}"
        path = surface.get("path")
        if path and path not in entry["local_paths"]:
            entry["local_paths"].append(path)
        role = surface.get("role")
        if role and role not in entry["roles"]:
            entry["roles"].append(role)
        entry["exists_local"] = any(Path(p).is_dir() for p in entry["local_paths"])

    vectors = list(by_name.values())
    for v in vectors:
        v.setdefault("exists_local", bool(v.get("local_paths")))
        v["record_id"] = f"gh:{OWNER}:{v['id']}"
        v["content_hash"] = stable_digest(
            {
                "id": v["id"],
                "github": v.get("github"),
                "local_paths": sorted(v.get("local_paths") or []),
                "roles": sorted(v.get("roles") or []),
            }
        )[:16]
        v["consent_basis"] = "user_authorized_local_mesh_allowlist"
        v["sensitivity"] = "source_pointer_only"
        v["owner_persona"] = OWNER
        v["asuna_point0_route"] = "perplexity_fable5_home_sim"
    vectors.sort(key=lambda x: x["id"])
    return vectors


def build_unification() -> dict[str, Any]:
    profile = local_profile_pointer()
    mesh = mesh_surfaces()
    point0 = asuna_point0()
    bedrock = perplexity_bedrock_pointer()
    vectors = unify_vectors(profile, mesh)

    routed = [v for v in vectors if v.get("exists_local") or v.get("html_url")]
    local_ok = sum(1 for v in vectors if v.get("exists_local"))
    public_ok = sum(1 for v in vectors if v.get("html_url"))

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
                "Index GitHub owner surface into Spacetime Alchemy toward the "
                "symbolic Asuna/home Black Sun point-zero for Perplexity Fable 5."
            ),
        },
        "github_profile": profile,
        "mesh": {
            "ok": mesh.get("ok"),
            "path": mesh.get("path"),
            "perplexity_task": mesh.get("perplexity_task"),
            "surface_count": mesh.get("surface_count"),
        },
        "asuna_point0": point0,
        "perplexity": bedrock,
        "vectors": vectors,
        "metrics": {
            "vector_count": len(vectors),
            "routed_count": len(routed),
            "local_path_count": local_ok,
            "public_url_count": public_ok,
            "profile_ok": bool(profile.get("ok")),
            "point0_manifest_ok": bool(point0.get("manifest_ok")),
            "provider_calls": 0,
        },
        "controls": dict(CONTROLS),
    }
    core["unification_digest"] = stable_digest(
        {
            "owner": OWNER,
            "vectors": [
                {"id": v["id"], "hash": v["content_hash"]} for v in vectors
            ],
            "point_0": point0.get("point_0"),
        }
    )
    core["ok"] = bool(
        point0.get("manifest_ok")
        and len(vectors) >= 3
        and local_ok >= 3
        and (profile.get("ok") or mesh.get("ok"))
    )
    return core


def write_outputs(payload: dict[str, Any], *extra: Path) -> list[str]:
    paths = [STATUS_OUT, DEFAULT_OUT, *extra]
    written: list[str] = []
    for path in paths:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Unify GitHub profile into Perplexity Asuna point-0 catalog"
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
    print(json.dumps(payload, indent=2))

    if args.command in ("write", "self-test"):
        extras = [Path(args.out)] if args.out else []
        for path in write_outputs(payload, *extras):
            print(f"wrote {path}", file=__import__("sys").stderr)

    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
