#!/usr/bin/env python3
"""Local status lane for the Comet browser-extension workspace."""

from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
from pathlib import Path
from typing import Any

REPO_URL = "https://github.com/webLiang/Pornhub-Video-Downloader-Plugin-v3.git"
DEFAULT_WORKSPACE = "/Users/fredwashere/browser-extension-workspaces/pornhub-video-downloader-plugin-v3"
DEFAULT_STATUS_FILE = "/tmp/shadow_garden_extension_workspace_status.json"
DEFAULT_REVIEW_PROMPT_FILE = "/tmp/shadow_garden_extension_perplexity_review_prompt.md"
LAWFUL_ENV = "SG_LAWFUL_DOWNLOADS_CONFIRMED"
COMET_VERIFIED_ENV = "SG_COMET_EXTENSION_VERIFIED"
EXPECTED_PACKAGE_NAME = "pornhub-video-downloader-plugin-v3"


def _utc_now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).isoformat()


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {"_raw": data}
    except (OSError, json.JSONDecodeError) as exc:
        return {"_error": f"{type(exc).__name__}: could not parse {path.name}"}


def _atomic_write(path: str, content: str) -> None:
    if not path:
        return
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        temporary.replace(target)
    finally:
        if temporary.exists():
            temporary.unlink()


def _write_text(path: str, content: str) -> None:
    _atomic_write(path, content)


def _write_json(path: str, payload: dict[str, Any]) -> None:
    _atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _detect_package_manager(package_json: dict[str, Any], workspace: Path) -> str | None:
    manager = package_json.get("packageManager")
    if isinstance(manager, str) and manager:
        return manager
    if (workspace / "pnpm-lock.yaml").exists():
        return "pnpm"
    if (workspace / "yarn.lock").exists():
        return "yarn"
    if (workspace / "package-lock.json").exists():
        return "npm"
    return None


def _bundled_artifacts(workspace: Path) -> list[str]:
    if not workspace.is_dir():
        return []
    matches = [*workspace.glob("*.crx"), *workspace.glob("*.pem")]
    return sorted(str(path.relative_to(workspace)) for path in matches if path.is_file())


def _risk_flags(
    package_json: dict[str, Any],
    dist_manifest: dict[str, Any],
    bundled_artifacts: list[str],
) -> list[str]:
    flags = [
        "lawful_personal_use_only",
        "no_drm_paywall_or_auth_bypass",
        "manual_browser_extension_install_only",
    ]
    permissions = dist_manifest.get("permissions") if dist_manifest else None
    host_permissions = dist_manifest.get("host_permissions") if dist_manifest else None
    if isinstance(host_permissions, list) and any(str(item) == "<all_urls>" for item in host_permissions):
        flags.append("broad_host_permissions")
    if isinstance(permissions, list) and "downloads" in permissions:
        flags.append("downloads_permission")
    if isinstance(permissions, list) and "declarativeNetRequest" in permissions:
        flags.append("declarative_net_request_permission")
    scripts = package_json.get("scripts") if isinstance(package_json, dict) else {}
    if isinstance(scripts, dict) and "build:crx" in scripts:
        flags.append("crx_packaging_available_manual_review_required")
    if bundled_artifacts:
        flags.append("bundled_crx_or_pem_quarantine_required")
    if dist_manifest and dist_manifest.get("manifest_version") != 3:
        flags.append("manifest_version_3_required")
    if package_json and package_json.get("name") not in {None, EXPECTED_PACKAGE_NAME}:
        flags.append("unexpected_package_name_manual_review_required")
    return flags


def _build_review_prompt(status: dict[str, Any]) -> str:
    return "\n".join([
        "Perplexity review brief for the Comet browser-extension workspace.",
        f"Repository: {status['repo']['url']}",
        f"Workspace: {status['workspace']['path']}",
        f"Lane status: {status['status']}",
        f"Package manager: {status['package'].get('manager') or 'unknown'}",
        f"Version: {status['package'].get('version') or 'unknown'}",
        f"Comet verification: {status['cometCompatibility']['verifiedInComet']}",
        f"Bundled CRX/PEM artifacts: {status['artifacts']['bundledCrxOrPem'] or 'none detected'}",
        "Review goals:",
        "1. Summarize the Manifest V3/Vite/Preact architecture.",
        "2. Check Comet/Chromium unpacked-extension compatibility risks.",
        "3. Review extension permissions, injected scripts, downloads behavior, and offscreen usage.",
        "4. Produce lawful-use, copyright, terms-of-service, and no-circumvention risk notes.",
        "5. Return a short build/test checklist and task backlog.",
        "Boundary: docs-only review; do not generate downloader logic, bypass steps, or automated download instructions.",
    ]) + "\n"


def build_status(args: argparse.Namespace) -> dict[str, Any]:
    workspace = Path(args.workspace).expanduser()
    package_path = workspace / "package.json"
    dist_manifest_path = workspace / "dist" / "manifest.json"
    source_manifest_path = workspace / "manifest.js"
    package_json = _read_json(package_path)
    dist_manifest = _read_json(dist_manifest_path)
    lawful_confirmed = args.lawful_confirmed or os.environ.get(LAWFUL_ENV) == "1"
    comet_verified = getattr(args, "comet_verified", False) or os.environ.get(COMET_VERIFIED_ENV) == "1"
    workspace_exists = workspace.is_dir()
    package_present = bool(package_json) and "_error" not in package_json
    dist_manifest_present = bool(dist_manifest) and "_error" not in dist_manifest
    manifest_v3 = dist_manifest_present and dist_manifest.get("manifest_version") == 3
    bundled_artifacts = _bundled_artifacts(workspace)

    if not lawful_confirmed:
        lane_status = "blocked_lawful_confirmation_required"
    elif not workspace_exists:
        lane_status = "not_ready_workspace_missing"
    elif not package_present:
        lane_status = "not_ready_package_json_missing"
    elif not dist_manifest_present:
        lane_status = "not_ready_build_missing"
    elif not manifest_v3:
        lane_status = "not_ready_manifest_v3_required"
    else:
        lane_status = "ready"

    manager = _detect_package_manager(package_json, workspace)
    commands = {
        "clone": ["git", "clone", REPO_URL, str(workspace)],
        "update": ["git", "-C", str(workspace), "pull", "--ff-only"],
        "submodules": ["git", "-C", str(workspace), "submodule", "update", "--init", "--recursive"],
        "install": ["pnpm", "--dir", str(workspace), "install", "--frozen-lockfile"],
        "test": ["pnpm", "--dir", str(workspace), "test"],
        "lint": ["pnpm", "--dir", str(workspace), "lint"],
        "build": ["pnpm", "--dir", str(workspace), "build"],
        "status": ["python3", "tools/extension_workspace_status.py", "--workspace", str(workspace)],
    }

    status = {
        "kind": "shadow_garden_comet_extension_workspace_status",
        "generatedAt": _utc_now(),
        "status": lane_status,
        "repo": {
            "url": REPO_URL,
            "expectedPackageName": EXPECTED_PACKAGE_NAME,
        },
        "workspace": {
            "path": str(workspace),
            "parent": str(workspace.parent),
            "exists": workspace_exists,
        },
        "package": {
            "present": package_present,
            "name": package_json.get("name") if package_present else None,
            "version": package_json.get("version") if package_present else None,
            "manager": manager,
            "scripts": sorted(package_json.get("scripts", {}).keys()) if isinstance(package_json.get("scripts"), dict) else [],
            "error": package_json.get("_error"),
        },
        "dist": {
            "path": str(workspace / "dist"),
            "manifestPath": str(dist_manifest_path),
            "manifestPresent": dist_manifest_present,
            "manifestVersion": dist_manifest.get("manifest_version") if dist_manifest_present else None,
            "permissions": dist_manifest.get("permissions") if dist_manifest_present else [],
            "hostPermissions": dist_manifest.get("host_permissions") if dist_manifest_present else [],
            "error": dist_manifest.get("_error"),
        },
        "source": {
            "manifestJsPath": str(source_manifest_path),
            "manifestJsPresent": source_manifest_path.exists(),
            "pnpmLockPresent": (workspace / "pnpm-lock.yaml").exists(),
        },
        "legalGate": {
            "env": LAWFUL_ENV,
            "confirmed": lawful_confirmed,
            "boundary": "User-confirmed lawful personal-use downloads only; no DRM, paywall, auth bypass, or hidden scraping support.",
        },
        "capabilities": [
            "browser_extension",
            "comet",
            "chromium",
            "manifest_v3",
            "local_workspace",
            "perplexity_review",
        ],
        "riskFlags": _risk_flags(package_json, dist_manifest, bundled_artifacts),
        "artifacts": {
            "bundledCrxOrPem": bundled_artifacts,
            "quarantineRequired": bool(bundled_artifacts),
        },
        "cometCompatibility": {
            "manifestV3": manifest_v3,
            "unpackedDistPresent": dist_manifest_present,
            "downloadsPermissionDeclared": "downloads" in (dist_manifest.get("permissions") or []),
            "broadHostPermissionsDeclared": "<all_urls>" in (dist_manifest.get("host_permissions") or []),
            "manualLoadRequired": True,
            "verificationEnv": COMET_VERIFIED_ENV,
            "verifiedInComet": comet_verified,
        },
        "commands": commands,
        "cometInstructions": [
            "Build the extension from source with pnpm build after reviewing dependencies.",
            "Open Comet or another Chromium browser extension settings page manually.",
            "Enable developer mode manually.",
            "Load the workspace dist directory as an unpacked extension manually.",
        ],
        "routeHints": [
            {"lane": "claude", "reason": "review TypeScript, Vite, Manifest V3, and workspace build failures"},
            {"lane": "perplexity", "reason": "produce docs-only architecture, risk, compatibility, and task notes"},
            {"lane": "bridge_feedback", "reason": "surface workspace readiness and lawful-use gate in diagnostics"},
        ],
        "reviewPromptPath": args.review_prompt_file,
    }
    status["perplexityReviewPrompt"] = _build_review_prompt(status)
    return status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Emit local Comet browser-extension workspace status JSON.")
    parser.add_argument("--workspace", default=os.environ.get("SG_EXTENSION_WORKSPACE", DEFAULT_WORKSPACE))
    parser.add_argument("--status-file", default=os.environ.get("SG_EXTENSION_STATUS_FILE", DEFAULT_STATUS_FILE))
    parser.add_argument("--review-prompt-file", default=os.environ.get("SG_EXTENSION_REVIEW_PROMPT_FILE", DEFAULT_REVIEW_PROMPT_FILE))
    parser.add_argument("--lawful-confirmed", action="store_true")
    parser.add_argument("--comet-verified", action="store_true")
    parser.add_argument("--no-write", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    status = build_status(args)
    if not args.no_write:
        _write_json(args.status_file, status)
        _write_text(args.review_prompt_file, status["perplexityReviewPrompt"])
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
