#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

try:
    from .perplexity_mesh_adapter import (
        DEFAULT_API_URL,
        DEFAULT_MODEL,
        build_payload,
        build_prompt,
        read_json,
        request_perplexity,
        write_json,
    )
    from .recursive_node_bridge import LoopConfig, RecursiveLoop, write_status
except ImportError:
    from perplexity_mesh_adapter import (
        DEFAULT_API_URL,
        DEFAULT_MODEL,
        build_payload,
        build_prompt,
        read_json,
        request_perplexity,
        write_json,
    )
    from recursive_node_bridge import LoopConfig, RecursiveLoop, write_status

DEFAULT_STATUS_FILE = "/tmp/shadow_garden_mesh_review_loop_status.json"
DEFAULT_OUTPUT_FILE = "/tmp/shadow_garden_mesh_review_loop_results.json"
DEFAULT_RECURSIVE_STATUS_FILE = "/tmp/shadow_garden_recursive_node_status.json"
DEFAULT_EXTENSION_STATUS_FILE = "/tmp/shadow_garden_extension_workspace_status.json"
CONFIRM_SEND_TOKEN = "PERPLEXITY_LOOP_OK"
MAX_LOCAL_CYCLES = 12
MAX_EXTERNAL_CYCLES = 3
MAX_DURATION_SECONDS = 900.0
MIN_LOCAL_INTERVAL_SECONDS = 0.1
MIN_EXTERNAL_INTERVAL_SECONDS = 30.0
SECRET_PATTERNS = (
    re.compile(r"\bpplx-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE),
    re.compile(r"\bxai-[A-Za-z0-9_-]{12,}\b", re.IGNORECASE),
    re.compile(r"\bsk[-_][A-Za-z0-9_-]{12,}\b", re.IGNORECASE),
    re.compile(r"\bBearer\s+\S+", re.IGNORECASE),
    re.compile(
        r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*['\"]?[a-zA-Z0-9_\-]{8,}"
    ),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def contains_secret(value: str) -> bool:
    return any(pattern.search(value or "") for pattern in SECRET_PATTERNS)


def _redact_string(text: str, secrets: tuple[str, ...]) -> str:
    redacted = text
    for secret in secrets:
        if secret:
            redacted = redacted.replace(secret, "[REDACTED]")
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def redact_secrets(value: Any, secrets: tuple[str, ...]) -> Any:
    """Deep-redact credential-like substrings before writing artifacts to disk."""
    if isinstance(value, str):
        return _redact_string(value, secrets)
    if isinstance(value, dict):
        return {key: redact_secrets(item, secrets) for key, item in value.items()}
    if isinstance(value, list):
        return [redact_secrets(item, secrets) for item in value]
    return value


@dataclass(frozen=True)
class MeshReviewLoopConfig:
    cycles: int = 1
    interval_seconds: float = 1.0
    max_seconds: float = 60.0
    node_count: int = 9
    gain: float = 1.0
    send_perplexity: bool = False
    confirm_send: str = ""
    request: str = "Review local recursive and Comet workspace status for integration risks."
    model: str = DEFAULT_MODEL
    api_url: str = DEFAULT_API_URL
    max_tokens: int = 800
    request_timeout: float = 30.0

    def __post_init__(self) -> None:
        maximum_cycles = MAX_EXTERNAL_CYCLES if self.send_perplexity else MAX_LOCAL_CYCLES
        minimum_interval = (
            MIN_EXTERNAL_INTERVAL_SECONDS
            if self.send_perplexity
            else MIN_LOCAL_INTERVAL_SECONDS
        )
        if not 1 <= self.cycles <= maximum_cycles:
            raise ValueError(f"cycles must be between 1 and {maximum_cycles}")
        if not minimum_interval <= self.interval_seconds:
            raise ValueError(f"interval must be at least {minimum_interval} seconds")
        if not 0 < self.max_seconds <= MAX_DURATION_SECONDS:
            raise ValueError(
                f"max_seconds must be greater than 0 and at most {MAX_DURATION_SECONDS}"
            )
        if self.send_perplexity and self.confirm_send != CONFIRM_SEND_TOKEN:
            raise ValueError(
                f"external review requires --confirm-send {CONFIRM_SEND_TOKEN}"
            )
        if self.max_tokens < 1 or self.request_timeout <= 0:
            raise ValueError("max_tokens and request_timeout must be positive")
        if contains_secret(self.request):
            raise ValueError("request contains a credential-like value")


class MeshReviewLoop:
    def __init__(
        self,
        config: MeshReviewLoopConfig,
        *,
        status_file: str = DEFAULT_STATUS_FILE,
        output_file: str = DEFAULT_OUTPUT_FILE,
        recursive_status_file: str = DEFAULT_RECURSIVE_STATUS_FILE,
        extension_status_file: str = DEFAULT_EXTENSION_STATUS_FILE,
        request_fn: Callable[[str, str, dict[str, Any], float], dict[str, Any]] = request_perplexity,
    ) -> None:
        self.config = config
        self.status_file = status_file
        self.output_file = output_file
        self.recursive_status_file = recursive_status_file
        self.extension_status_file = extension_status_file
        self.request_fn = request_fn
        self.stop_event = threading.Event()
        self.recursive_loop = RecursiveLoop(
            LoopConfig(node_count=config.node_count, gain=config.gain)
        )

    def stop(self) -> None:
        self.stop_event.set()

    def _write_results(self, results: list[dict[str, Any]]) -> None:
        write_json(
            self.output_file,
            {
                "kind": "shadow_garden_mesh_review_loop_results",
                "generated_at": utc_now(),
                "results": results,
            },
        )

    def _context(self, recursive_snapshot: dict[str, Any]) -> dict[str, Any]:
        context = {"recursive": recursive_snapshot}
        extension_status = read_json(self.extension_status_file)
        if extension_status is not None:
            context["comet_extension"] = extension_status
        return context

    def _status(
        self,
        state: str,
        completed_cycles: int,
        external_requests: int,
        started_at: str,
        error: str | None = None,
    ) -> dict[str, Any]:
        return {
            "kind": "shadow_garden_mesh_review_loop_status",
            "generated_at": utc_now(),
            "status": state,
            "started_at": started_at,
            "completed_cycles": completed_cycles,
            "external_requests": external_requests,
            "perplexity_api_key_present": bool(os.environ.get("PERPLEXITY_API_KEY")),
            "dry_run": not self.config.send_perplexity,
            "bounded": True,
            "cascade_chat_connected": False,
            "browser_automation": False,
            "command_execution_from_model_output": False,
            "error": error,
            "config": {
                **asdict(self.config),
                "confirm_send": bool(self.config.confirm_send),
            },
            "guardrails": [
                "bounded_cycles",
                "bounded_duration",
                "cooperative_cancellation",
                "dry_run_by_default",
                "explicit_external_send_confirmation",
                "environment_only_credentials",
                "credential_pattern_rejection",
                "no_browser_profile_control",
                "no_agent_broadcast",
                "no_model_output_command_execution",
                "symbolic_chronology_metadata_only",
            ],
        }

    def run(self) -> dict[str, Any]:
        api_key = os.environ.get("PERPLEXITY_API_KEY", "")
        if self.config.send_perplexity and not api_key:
            raise ValueError("PERPLEXITY_API_KEY is required for external review")

        started_at = utc_now()
        started_monotonic = time.monotonic()
        completed_cycles = 0
        external_requests = 0
        results: list[dict[str, Any]] = []
        write_json(
            self.status_file,
            self._status("running", completed_cycles, external_requests, started_at),
        )

        try:
            for cycle_number in range(1, self.config.cycles + 1):
                if self.stop_event.is_set():
                    break
                elapsed = time.monotonic() - started_monotonic
                if elapsed >= self.config.max_seconds:
                    break

                recursive_snapshot = self.recursive_loop.sovereign_cycle()
                write_status(self.recursive_status_file, recursive_snapshot)
                prompt = build_prompt(self.config.request, self._context(recursive_snapshot))
                event: dict[str, Any] = {
                    "cycle": cycle_number,
                    "generated_at": utc_now(),
                    "mode": "external_review" if self.config.send_perplexity else "dry_run",
                    "recursive_cycles": recursive_snapshot["sovereign"]["cycles"],
                }

                if self.config.send_perplexity:
                    response = self.request_fn(
                        self.config.api_url,
                        api_key,
                        build_payload(self.config.model, prompt, self.config.max_tokens),
                        self.config.request_timeout,
                    )
                    external_requests += 1
                    event["response"] = redact_secrets(response, (api_key,))
                else:
                    event["prompt_preview"] = redact_secrets(prompt, (api_key,))

                results.append(redact_secrets(event, (api_key,)))
                completed_cycles += 1
                self._write_results(results)
                write_json(
                    self.status_file,
                    self._status(
                        "running",
                        completed_cycles,
                        external_requests,
                        started_at,
                    ),
                )

                if cycle_number < self.config.cycles:
                    remaining = self.config.max_seconds - (
                        time.monotonic() - started_monotonic
                    )
                    if remaining <= 0:
                        break
                    self.stop_event.wait(min(self.config.interval_seconds, remaining))
        except KeyboardInterrupt:
            self.stop_event.set()
        except RuntimeError as exc:
            status = self._status(
                "api_error",
                completed_cycles,
                external_requests,
                started_at,
                str(exc),
            )
            write_json(self.status_file, status)
            return status

        state = "stopped" if self.stop_event.is_set() else "completed"
        status = self._status(
            state,
            completed_cycles,
            external_requests,
            started_at,
        )
        write_json(self.status_file, status)
        if completed_cycles == 0:
            self._write_results([])
        return status


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Bounded local recursive telemetry and Perplexity review loop"
    )
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--interval", type=float, default=1.0)
    parser.add_argument("--max-seconds", type=float, default=60.0)
    parser.add_argument("--nodes", type=int, default=9)
    parser.add_argument("--gain", type=float, default=1.0)
    parser.add_argument("--request", default=MeshReviewLoopConfig.request)
    parser.add_argument("--model", default=os.environ.get("PERPLEXITY_MODEL", DEFAULT_MODEL))
    parser.add_argument("--api-url", default=os.environ.get("PERPLEXITY_API_URL", DEFAULT_API_URL))
    parser.add_argument("--max-tokens", type=int, default=800)
    parser.add_argument("--request-timeout", type=float, default=30.0)
    parser.add_argument("--send-perplexity", action="store_true")
    parser.add_argument("--confirm-send", default="")
    parser.add_argument("--status-file", default=DEFAULT_STATUS_FILE)
    parser.add_argument("--output-file", default=DEFAULT_OUTPUT_FILE)
    parser.add_argument("--recursive-status-file", default=DEFAULT_RECURSIVE_STATUS_FILE)
    parser.add_argument("--extension-status-file", default=DEFAULT_EXTENSION_STATUS_FILE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        config = MeshReviewLoopConfig(
            cycles=args.cycles,
            interval_seconds=args.interval,
            max_seconds=args.max_seconds,
            node_count=args.nodes,
            gain=args.gain,
            send_perplexity=args.send_perplexity,
            confirm_send=args.confirm_send,
            request=args.request,
            model=args.model,
            api_url=args.api_url,
            max_tokens=args.max_tokens,
            request_timeout=args.request_timeout,
        )
        loop = MeshReviewLoop(
            config,
            status_file=args.status_file,
            output_file=args.output_file,
            recursive_status_file=args.recursive_status_file,
            extension_status_file=args.extension_status_file,
        )
        status = loop.run()
    except (OSError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 0 if status["status"] in {"completed", "stopped"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
