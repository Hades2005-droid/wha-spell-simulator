#!/usr/bin/env python3
"""
Shadow Garden Local Prompt + Perplexity/Cursor Bridge v4.3 (safe)

- Reads API/model settings from the environment (never hardcode secrets).
- Dry-runs Cursor bridge by default.
- Supports plain-text prompt routing for voice/image/video/audio activities.
- Enforces consent-safe, non-explicit boundary framing.
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

KEYWORDS_IMAGE = ("image", "illustration", "poster", "render", "portrait", "visual")
KEYWORDS_VIDEO = ("video", "cinematic", "clip", "animation", "scene", "movie", "trailer")
KEYWORDS_AUDIO = ("audio", "music", "soundtrack", "sfx", "sound effect", "sound design")
KEYWORDS_VOICE = ("voice", "dialogue", "narration", "spoken", "tts")


@dataclass(frozen=True)
class BridgeConfig:
    xai_api_key: str | None
    grok_voice_model: str
    grok_image_model: str
    grok_video_model: str
    grok_audio_model: str
    grok_text_model: str
    dry_run: bool
    cursor_binary: str | None


@dataclass(frozen=True)
class VoicePassResult:
    activity: str
    voice: str
    input_prompt: str
    prompt: str
    selected_model: str
    cursor_invoked: bool
    cursor_exit_code: int | None
    cursor_error: str | None


def normalize_prompt(value: str) -> str:
    return " ".join((value or "").strip().split())


def infer_activity(prompt: str, explicit_activity: str | None = None) -> str:
    if explicit_activity and explicit_activity != "auto":
        return explicit_activity

    lower = normalize_prompt(prompt).lower()
    scores = {
        "video": sum(word in lower for word in KEYWORDS_VIDEO),
        "audio": sum(word in lower for word in KEYWORDS_AUDIO),
        "image": sum(word in lower for word in KEYWORDS_IMAGE),
        "voice": sum(word in lower for word in KEYWORDS_VOICE),
    }
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    top_activity, top_score = ranked[0]
    return top_activity if top_score > 0 else "text"


def selected_model(config: BridgeConfig, activity: str) -> str:
    return {
        "voice": config.grok_voice_model,
        "image": config.grok_image_model,
        "video": config.grok_video_model,
        "audio": config.grok_audio_model,
        "text": config.grok_text_model,
    }.get(activity, config.grok_text_model)


def build_voice_prompt(voice: str) -> str:
    return (
        f"Shadow Garden cinematic voice pass for {voice}. "
        f"{SOVEREIGN_BOUNDARY}"
    )


def build_activity_prompt(activity: str, raw_prompt: str) -> str:
    cleaned = normalize_prompt(raw_prompt)
    if not cleaned:
        cleaned = "Shadow Garden sovereign activity prompt."

    instruction = {
        "image": "Create an image-generation brief with subject, composition, lens/style, lighting, palette, and quality constraints.",
        "video": "Create a video-generation brief with shot list, camera motion, pacing, transitions, continuity, and quality constraints.",
        "audio": "Create an audio-generation brief with sonic palette, tempo/mood, scene timing, layering, and mastering constraints.",
        "voice": "Create a voice-generation brief with persona, delivery, pacing, pronunciation cues, and recording constraints.",
        "text": "Create a structured Shadow Garden production brief with clear downstream generation-ready instructions.",
    }[activity]
    return (
        f"Shadow Garden {activity} activity. "
        f"{instruction} "
        f"User plain-text prompt: {cleaned}. "
        f"{SOVEREIGN_BOUNDARY}"
    )


def load_config(*, dry_run: bool) -> BridgeConfig:
    cursor_binary = shutil.which("cursor")
    return BridgeConfig(
        xai_api_key=os.getenv("XAI_API_KEY"),
        grok_voice_model=os.getenv("GROK_VOICE_MODEL", "grok-voice-latest"),
        grok_image_model=os.getenv("GROK_IMAGE_MODEL", "grok-image-latest"),
        grok_video_model=os.getenv("GROK_VIDEO_MODEL", "grok-video-latest"),
        grok_audio_model=os.getenv("GROK_AUDIO_MODEL", "grok-audio-latest"),
        grok_text_model=os.getenv("GROK_TEXT_MODEL", "grok-3"),
        dry_run=dry_run,
        cursor_binary=cursor_binary,
    )


def invoke_cursor(config: BridgeConfig, prompt: str, *, activity: str, input_prompt: str, voice: str = "", model: str = "") -> VoicePassResult:
    if config.dry_run:
        print(f"DRY RUN Cursor command: {prompt}")
        return VoicePassResult(
            activity=activity,
            voice="",
            input_prompt=input_prompt,
            prompt=prompt,
            selected_model=model,
            cursor_invoked=False,
            cursor_exit_code=None,
            cursor_error=None,
        )

    if not config.cursor_binary:
        return VoicePassResult(
            activity=activity,
            voice="",
            input_prompt=input_prompt,
            prompt=prompt,
            selected_model=model,
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
            activity=activity,
            voice="",
            input_prompt=input_prompt,
            prompt=prompt,
            selected_model=model,
            cursor_invoked=True,
            cursor_exit_code=completed.returncode,
            cursor_error=error,
        )
    except subprocess.TimeoutExpired:
        return VoicePassResult(
            activity=activity,
            voice="",
            input_prompt=input_prompt,
            prompt=prompt,
            selected_model=model,
            cursor_invoked=True,
            cursor_exit_code=None,
            cursor_error="cursor command timed out after 30s",
        )
    except OSError as exc:
        return VoicePassResult(
            activity=activity,
            voice="",
            input_prompt=input_prompt,
            prompt=prompt,
            selected_model=model,
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
        prompt = build_voice_prompt(voice)
        model = selected_model(config, "voice")
        print(f"Voice: {voice}")
        print(f"Activity: voice | Model: {model}")
        print(f"Prompt: {prompt}")
        print(f"Perplexity bridge (manual): {prompt}")

        cursor_result = invoke_cursor(
            config,
            prompt,
            activity="voice",
            input_prompt=f"voice pass for {voice}",
            voice=voice,
            model=model,
        )
        results.append(
            VoicePassResult(
                activity="voice",
                voice=voice,
                input_prompt=f"voice pass for {voice}",
                prompt=prompt,
                selected_model=model,
                cursor_invoked=cursor_result.cursor_invoked,
                cursor_exit_code=cursor_result.cursor_exit_code,
                cursor_error=cursor_result.cursor_error,
            )
        )

        if cursor_result.cursor_error:
            print(f"Cursor bridge error: {cursor_result.cursor_error}", file=sys.stderr)

    return results


def cast_plaintext_prompts(
    prompts: Sequence[str],
    *,
    activity: str = "auto",
    dry_run: bool = True,
) -> list[VoicePassResult]:
    config = load_config(dry_run=dry_run)
    results: list[VoicePassResult] = []

    if not config.xai_api_key:
        print("Warning: XAI_API_KEY is not set; provider checks will be skipped.", file=sys.stderr)

    for raw_prompt in prompts:
        inferred_activity = infer_activity(raw_prompt, activity)
        prompt = build_activity_prompt(inferred_activity, raw_prompt)
        model = selected_model(config, inferred_activity)
        cursor_command = f"[SHADOW_GARDEN:{inferred_activity}:{model}] {prompt}"

        print(f"Activity: {inferred_activity} | Model: {model}")
        print(f"Input: {normalize_prompt(raw_prompt)}")
        print(f"Prompt: {prompt}")
        print(f"Perplexity bridge (manual): {prompt}")

        cursor_result = invoke_cursor(
            config,
            cursor_command,
            activity=inferred_activity,
            input_prompt=raw_prompt,
            model=model,
        )
        results.append(
            VoicePassResult(
                activity=inferred_activity,
                voice="",
                input_prompt=raw_prompt,
                prompt=prompt,
                selected_model=model,
                cursor_invoked=cursor_result.cursor_invoked,
                cursor_exit_code=cursor_result.cursor_exit_code,
                cursor_error=cursor_result.cursor_error,
            )
        )
        if cursor_result.cursor_error:
            print(f"Cursor bridge error: {cursor_result.cursor_error}", file=sys.stderr)

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Shadow Garden safe prompt bridge dry-run")
    parser.add_argument(
        "--invoke-cursor",
        action="store_true",
        help="Actually run `cursor --command` (default is dry-run only)",
    )
    parser.add_argument(
        "--prompt",
        action="append",
        default=[],
        help="Plain-text prompt to route (repeat for multiple prompts)",
    )
    parser.add_argument(
        "--activity",
        choices=["auto", "voice", "image", "video", "audio", "text"],
        default="auto",
        help="Route plain-text prompts to a specific activity (default: auto)",
    )
    parser.add_argument(
        "--voice",
        action="append",
        default=[],
        help="Voice preset for voice-pass mode (repeat for multiple voices)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.prompt:
        results = cast_plaintext_prompts(
            args.prompt,
            activity=args.activity,
            dry_run=not args.invoke_cursor,
        )
    else:
        voices = tuple(args.voice) if args.voice else DEFAULT_VOICES
        results = cast_safe_scene(voices=voices, dry_run=not args.invoke_cursor)

    failures = [r for r in results if r.cursor_error]
    print("Safe Shadow Garden bridge complete.")
    return 1 if failures and args.invoke_cursor else 0


if __name__ == "__main__":
    raise SystemExit(main())
