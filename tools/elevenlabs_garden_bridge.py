#!/usr/bin/env python3
"""Expose ComfyUI's native ElevenLabs nodes to Shadow Garden safely.

This bridge indexes an explicitly configured ComfyUI installation and an
optional local workflow. It emits API-node and workflow metadata only. It does
not import ComfyUI, submit ``/prompt`` jobs, call ElevenLabs, or print secret
values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import socket
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


SCHEMA = "shadow_garden.comfyui_elevenlabs_bridge.v1"
HOME = Path.home()
DEFAULT_COMFYUI_ROOT = HOME / "ComfyUI"
DEFAULT_WORKFLOW = (
    DEFAULT_COMFYUI_ROOT
    / "workflows"
    / "shadow_garden_persona_prompt_pack_v15_1_safe.json"
)
MAX_WORKFLOW_BYTES = 2 * 1024 * 1024
MAX_WORKFLOW_NODES = 5_000
LOCAL_HOSTS = {"127.0.0.1", "localhost", "::1"}

NATIVE_NODE_IDS = (
    "ElevenLabsSpeechToText",
    "ElevenLabsVoiceSelector",
    "ElevenLabsTextToSpeech",
    "ElevenLabsAudioIsolation",
    "ElevenLabsTextToSoundEffects",
    "ElevenLabsInstantVoiceClone",
    "ElevenLabsSpeechToSpeech",
    "ElevenLabsTextToDialogue",
)

API_ENDPOINTS = (
    {"method": "POST", "path": "/proxy/elevenlabs/v1/speech-to-text"},
    {"method": "POST", "path": "/proxy/elevenlabs/v1/text-to-speech/{voice}"},
    {"method": "POST", "path": "/proxy/elevenlabs/v1/audio-isolation"},
    {"method": "POST", "path": "/proxy/elevenlabs/v1/sound-generation"},
    {"method": "POST", "path": "/proxy/elevenlabs/v1/voices/add"},
    {"method": "POST", "path": "/proxy/elevenlabs/v1/speech-to-speech/{voice}"},
    {"method": "POST", "path": "/proxy/elevenlabs/v1/text-to-dialogue"},
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _workflow_node_classes(value: Any, output: list[str], depth: int = 0) -> None:
    if len(output) >= MAX_WORKFLOW_NODES or depth > 4:
        return
    if isinstance(value, dict):
        node_type = value.get("class_type") or value.get("type")
        if isinstance(node_type, str) and node_type:
            output.append(node_type)
        for key in ("nodes", "prompt", "workflow"):
            if key in value:
                _workflow_node_classes(value[key], output, depth + 1)
    elif isinstance(value, list):
        for item in value:
            _workflow_node_classes(item, output, depth + 1)
            if len(output) >= MAX_WORKFLOW_NODES:
                return


def workflow_metadata(path: Path) -> dict[str, Any]:
    """Read bounded workflow structure without retaining prompt content."""

    result: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "payloads_stored": False,
    }
    if not path.is_file():
        return result
    try:
        size = path.stat().st_size
        result["bytes"] = size
        if size > MAX_WORKFLOW_BYTES:
            result["error"] = "workflow_byte_limit_exceeded"
            return result
        raw = path.read_bytes()
    except OSError as exc:
        result["error"] = f"{type(exc).__name__}"
        return result
    result["bytes"] = len(raw)
    result["sha256"] = _sha256(raw)
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        result["error"] = f"workflow_parse_failed:{type(exc).__name__}"
        return result

    classes: list[str] = []
    _workflow_node_classes(document, classes)
    counts = Counter(classes)
    elevenlabs = sorted(
        node_type for node_type in counts if "elevenlabs" in node_type.lower()
    )
    result.update(
        {
            "parse_ok": True,
            "node_count": len(classes),
            "node_counts": dict(sorted(counts.items())),
            "elevenlabs_nodes": elevenlabs,
            "node_scan_truncated": len(classes) >= MAX_WORKFLOW_NODES,
        }
    )
    return result


def _comfyui_probe(url: str, enabled: bool) -> dict[str, Any]:
    parsed = urlparse(url)
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    result: dict[str, Any] = {
        "enabled": enabled,
        "host": host,
        "port": port,
        "local_only": host in LOCAL_HOSTS,
        "port_open": None,
    }
    if enabled and host in LOCAL_HOSTS:
        try:
            with socket.create_connection((host, port), timeout=0.8):
                result["port_open"] = True
        except OSError:
            result["port_open"] = False
    return result


def build_manifest(
    *,
    comfyui_root: Path | None = None,
    workflow: Path | None = None,
    probe: bool = False,
) -> dict[str, Any]:
    configured_root = os.environ.get("COMFYUI_ROOT") or str(DEFAULT_COMFYUI_ROOT)
    root = (comfyui_root or Path(configured_root)).expanduser()
    configured_workflow = os.environ.get("COMFYUI_GARDEN_WORKFLOW") or str(
        DEFAULT_WORKFLOW
    )
    workflow_path = (
        workflow or Path(configured_workflow)
    ).expanduser()
    comfyui_url = os.environ.get("COMFYUI_URL", "http://127.0.0.1:8189").rstrip("/")
    extension_path = root / "comfy_api_nodes" / "nodes_elevenlabs.py"
    api_path = root / "comfy_api_nodes" / "apis" / "elevenlabs.py"
    garden_root = Path(
        os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden")
    ).expanduser()

    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "provider": "ElevenLabs",
        "interpretation": "Elvenio request mapped to the local ComfyUI ElevenLabs API nodes",
        "mode": "manifest_only",
        "comfyui": {
            "root": str(root),
            "url": comfyui_url,
            "native_extension": {
                "path": str(extension_path),
                "exists": extension_path.is_file(),
                "node_ids": list(NATIVE_NODE_IDS),
            },
            "api_contract": {
                "path": str(api_path),
                "exists": api_path.is_file(),
                "endpoints": list(API_ENDPOINTS),
            },
            "probe": _comfyui_probe(comfyui_url, probe),
        },
        "garden": {
            "root": str(garden_root),
            "fable5_compact": {
                "path": str(
                    garden_root
                    / "live"
                    / "spacetime_alchemy"
                    / "fable5-compact.json"
                ),
                "exists": (
                    garden_root
                    / "live"
                    / "spacetime_alchemy"
                    / "fable5-compact.json"
                ).is_file(),
            },
            "bedrock": {
                "path": str(
                    garden_root
                    / "live"
                    / "spacetime_alchemy"
                    / "PERPLEXITY_CONTEXT_BEDROCK.md"
                ),
                "exists": (
                    garden_root
                    / "live"
                    / "spacetime_alchemy"
                    / "PERPLEXITY_CONTEXT_BEDROCK.md"
                ).is_file(),
            },
        },
        "workflow": workflow_metadata(workflow_path),
        "credentials": {
            "env_name": "ELEVENLABS_API_KEY",
            "present": bool(os.environ.get("ELEVENLABS_API_KEY")),
            "value_emitted": False,
        },
        "controls": {
            "local_only": True,
            "external_fetch": False,
            "provider_calls": False,
            "comfy_prompt_submission": False,
            "browser_automation": False,
            "credentials_allowed": False,
            "payloads_stored": False,
            "approval_required_for_live_audio": True,
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Index ComfyUI ElevenLabs nodes into a Shadow Garden manifest"
    )
    parser.add_argument("command", choices=("status", "write"))
    parser.add_argument("--root", help="explicit ComfyUI installation root")
    parser.add_argument("--workflow", help="explicit local workflow JSON path")
    parser.add_argument("--probe", action="store_true", help="probe local port only")
    parser.add_argument("--out", help="manifest output path for write")
    args = parser.parse_args(argv)

    manifest = build_manifest(
        comfyui_root=Path(args.root).expanduser() if args.root else None,
        workflow=Path(args.workflow).expanduser() if args.workflow else None,
        probe=args.probe,
    )
    rendered = json.dumps(manifest, indent=2)
    if args.command == "status":
        print(rendered)
        return 0

    output = (
        Path(args.out).expanduser()
        if args.out
        else Path(__file__).resolve().parents[1]
        / "shadow_garden_handoff"
        / "terminal_auto"
        / "outbox"
        / "comfyui_elevenlabs_garden_bridge.json"
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered + "\n", encoding="utf-8")
    print(f"wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
