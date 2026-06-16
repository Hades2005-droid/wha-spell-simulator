#!/usr/bin/env python3
"""
Shadow Garden Local Voice + Perplexity/Cursor Bridge v4.2 (safe)

- Reads XAI_API_KEY from the environment (never hardcode secrets).
- Dry-runs Cursor bridge by default.
- Consent-safe, non-explicit voice pass prompts only.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from typing import Sequence

DEFAULT_VOICES: tuple[str, ...] = (
    "Mature Chinese Professional",
    "Addie",
    "Angela's Mom",
    "Sue",
    "Angela",
)

SOVEREIGN_BOUNDARY = (
    "Consent-safe, non-explicit, high emotional intensity, "
    "ritual/technical language, improved image/video quality direction, "
    "sovereign boundary active."
)


@dataclass(frozen=True)
class BridgeConfig:
    xai_api_key: str | None
    grok_voice_model: str
    dry_run: bool
    cursor_binary: str | None


@dataclass(frozen=True)
class VoicePassResult:
    voice: str
    prompt: str
    cursor_invoked: bool
    cursor_exit_code: int | None
    cursor_error: str | None


def build_prompt(voice: str) -> str:
    return (
        f"Shadow Garden cinematic voice pass for {voice}. "
        f"{SOVEREIGN_BOUNDARY}"
    )


def load_config(*, dry_run: bool) -> BridgeConfig:
    cursor_binary = shutil.which("cursor")
    return BridgeConfig(
        xai_api_key=os.getenv("XAI_API_KEY"),
        grok_voice_model=os.getenv("GROK_VOICE_MODEL", "grok-voice-latest"),
        dry_run=dry_run,
        cursor_binary=cursor_binary,
    )


def invoke_cursor(config: BridgeConfig, prompt: str) -> VoicePassResult:
    if config.dry_run:
        print(f"DRY RUN Cursor command: {prompt}")
        return VoicePassResult(
            voice="",
            prompt=prompt,
            cursor_invoked=False,
            cursor_exit_code=None,
            cursor_error=None,
        )

    if not config.cursor_binary:
        return VoicePassResult(
            voice="",
            prompt=prompt,
            cursor_invoked=False,
            cursor_exit_code=None,
            cursor_error="cursor CLI not found on PATH",
        )

    try:
        completed = subprocess.run(
            [config.cursor_binary, "--command", prompt],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        error = None
        if completed.returncode != 0:
            stderr = (completed.stderr or "").strip()
            error = stderr or f"cursor exited with code {completed.returncode}"
        return VoicePassResult(
            voice="",
            prompt=prompt,
            cursor_invoked=True,
            cursor_exit_code=completed.returncode,
            cursor_error=error,
        )
    except subprocess.TimeoutExpired:
        return VoicePassResult(
            voice="",
            prompt=prompt,
            cursor_invoked=True,
            cursor_exit_code=None,
            cursor_error="cursor command timed out after 30s",
        )
    except OSError as exc:
        return VoicePassResult(
            voice="",
            prompt=prompt,
            cursor_invoked=False,
            cursor_exit_code=None,
            cursor_error=str(exc),
        )


def cast_safe_scene(
    voices: Sequence[str] = DEFAULT_VOICES,
    *,
    dry_run: bool = True,
) -> list[VoicePassResult]:
    config = load_config(dry_run=dry_run)
    results: list[VoicePassResult] = []

    if not config.xai_api_key:
        print("Warning: XAI_API_KEY is not set; voice API checks will be skipped.", file=sys.stderr)
    else:
        print(f"Grok voice model: {config.grok_voice_model}")

    for voice in voices:
        prompt = build_prompt(voice)
        print(f"Voice: {voice}")
        print(f"Prompt: {prompt}")
        print(f"Perplexity bridge (manual): {prompt}")

        cursor_result = invoke_cursor(config, prompt)
        results.append(
            VoicePassResult(
                voice=voice,
                prompt=prompt,
                cursor_invoked=cursor_result.cursor_invoked,
                cursor_exit_code=cursor_result.cursor_exit_code,
                cursor_error=cursor_result.cursor_error,
            )
        )

        if cursor_result.cursor_error:
            print(f"Cursor bridge error: {cursor_result.cursor_error}", file=sys.stderr)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shadow Garden safe voice + bridge dry-run")
    parser.add_argument(
        "--invoke-cursor",
        action="store_true",
        help="Actually run `cursor --command` (default is dry-run only)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    results = cast_safe_scene(dry_run=not args.invoke_cursor)

    failures = [r for r in results if r.cursor_error]
    print("Safe Shadow Garden bridge complete.")
    return 1 if failures and args.invoke_cursor else 0


if __name__ == "__main__":
    raise SystemExit(main())
