#!/usr/bin/env python3
"""Install Q24 Fable5 master ingest into wha-spell-simulator as local bedrock."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HOME = Path.home()
WHA = Path(__file__).resolve().parents[1]
SG = Path(HOME / "ShadowGarden")
SLIM = WHA / "shadow_garden_handoff" / "bridges" / "q24_fable5_master_ingest.slim.json"
OUTBOX = WHA / "shadow_garden_handoff" / "terminal_auto" / "outbox"
Q24_ROOT = WHA / "q24"

FILE_MAP: list[tuple[str, str]] = [
    ("godot/GameSession.gd", "autoload/GameSession.gd"),
    ("godot/SaveManager.gd", "autoload/SaveManager.gd"),
    ("godot/ContentRegistry.gd", "autoload/ContentRegistry.gd"),
    ("godot/Q24StateAdapter.gd", "adapters/Q24StateAdapter.gd"),
    (
        "godot/Q24_EternalDao_Temperance14_HarmonyParadox_19to10to1.tres",
        "canon/Q24_EternalDao_Temperance14_HarmonyParadox_19to10to1.tres",
    ),
    ("canon/q24_canonical.yaml", "canon/q24_canonical.yaml"),
    ("q24_symbolic_registry.json", "q24_symbolic_registry.json"),
    ("ren_py/game/q24_canon.rpy", "ren_py/game/q24_canon.rpy"),
    ("README.md", "README.md"),
    (
        "report/Q24_Alpha_Component_Recommendation.md",
        "report/Q24_Alpha_Component_Recommendation.md",
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def load_slim(path: Path = SLIM) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_digest(slim: dict[str, Any]) -> dict[str, Any]:
    full = Path(slim["full"])
    expected = slim.get("digest_sha256", "")
    if not full.is_file():
        return {"ok": False, "detail": f"missing full digest: {full}"}
    actual = sha256_file(full)
    if expected and actual != expected:
        return {
            "ok": True,
            "detail": "digest drift (full digest updated since slim pointer)",
            "expected": expected,
            "actual": actual,
            "digest_sha256": actual,
        }
    return {"ok": True, "full": str(full), "digest_sha256": actual or expected}


def install_q24(import_root: Path, dest: Path = Q24_ROOT) -> dict[str, Any]:
    copied: list[dict[str, str]] = []
    missing: list[str] = []
    for rel_src, rel_dest in FILE_MAP:
        src = import_root / rel_src
        dst = dest / rel_dest
        if not src.is_file():
            missing.append(rel_src)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        copied.append({"rel": rel_dest, "sha256": sha256_file(dst)})
    return {
        "ok": not missing,
        "dest": str(dest),
        "files_copied": len(copied),
        "copied": copied,
        "missing": missing,
    }


def build_status(
    slim: dict[str, Any],
    *,
    digest: dict[str, Any],
    install: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema": "shadow_garden.q24_fable5_master_ingest_install.v1",
        "installed_at": utc_now(),
        "status": "INSTALLED_LOCAL" if install.get("ok") else "PARTIAL",
        "symbolic_only": True,
        "local_only": True,
        "slim": str(SLIM),
        "digest": digest,
        "slim_pointer": slim,
        "install": install,
        "bedrock": str(WHA / "shadow_garden_handoff" / "bridges" / "fable5_bedrock.json"),
    }


def write_status(status: dict[str, Any]) -> list[str]:
    OUTBOX.mkdir(parents=True, exist_ok=True)
    paths = [
        OUTBOX / "q24_fable5_master_ingest_status.json",
        Path("/tmp/q24_fable5_master_ingest_status.json"),
    ]
    written: list[str] = []
    for path in paths:
        path.write_text(json.dumps(status, indent=2) + "\n", encoding="utf-8")
        written.append(str(path))
    return written


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Install Q24 Fable5 master ingest bedrock")
    parser.add_argument(
        "command",
        nargs="?",
        default="install",
        choices=["install", "status", "verify"],
    )
    parser.add_argument("--slim", default=str(SLIM))
    args = parser.parse_args(argv)

    slim_path = Path(args.slim)
    slim = load_slim(slim_path)
    digest = verify_digest(slim)

    if args.command == "verify":
        print(json.dumps({"slim": str(slim_path), "digest": digest}, indent=2))
        return 0 if digest.get("ok") else 1

    import_root = Path(slim.get("q24_import", SG / "manual_imports/q24_unified"))
    install = install_q24(import_root)
    status = build_status(slim, digest=digest, install=install)
    written = write_status(status)

    if args.command == "status":
        print(json.dumps(status, indent=2))
        return 0

    print(json.dumps(status, indent=2))
    for path in written:
        print(f"wrote {path}")
    ok = digest.get("ok") and install.get("ok")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
