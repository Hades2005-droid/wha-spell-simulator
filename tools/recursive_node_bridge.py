#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from .chronology_engine import analyze_now
except ImportError:
    from chronology_engine import analyze_now

DEFAULT_STATUS_FILE = "/tmp/shadow_garden_recursive_node_status.json"
DEFAULT_NODE_COUNT = 9
MAX_NODE_COUNT = 9
MAX_GAIN = 8.0
MAX_FEED_ENTRIES = 256
MAX_CYCLE_POWER = 8.0


@dataclass
class SovereignNode:
    dexterity: float = 1.0
    cycle_power: float = 0.0
    feed_rate: float = 1.0
    sensory_depth: float = 1.0
    cycles: int = 0


@dataclass
class MatriarchNode:
    node_id: int
    activation: float = 0.0
    signal_feed: list[str] = field(default_factory=list)
    signal_ripple_factor: float = 1.0
    cycles: int = 0


@dataclass(frozen=True)
class LoopConfig:
    node_count: int = DEFAULT_NODE_COUNT
    gain: float = 1.0
    max_feed_entries: int = MAX_FEED_ENTRIES
    minimum_interval: float = 0.02
    route_name: str = "local-open-weights"
    route_model: str = "deepseek-local"
    route_endpoint: str = "http://127.0.0.1:11434/v1"

    def __post_init__(self) -> None:
        if not 1 <= self.node_count <= MAX_NODE_COUNT:
            raise ValueError(f"node_count must be between 1 and {MAX_NODE_COUNT}")
        if not 0 < self.gain <= MAX_GAIN:
            raise ValueError(f"gain must be greater than 0 and at most {MAX_GAIN}")
        if not 1 <= self.max_feed_entries <= MAX_FEED_ENTRIES:
            raise ValueError(f"max_feed_entries must be between 1 and {MAX_FEED_ENTRIES}")
        if self.minimum_interval <= 0:
            raise ValueError("minimum_interval must be positive")


class RecursiveLoop:
    def __init__(self, config: LoopConfig | None = None):
        self.config = config or LoopConfig()
        self.sovereign = SovereignNode()
        self.matriarchs = [MatriarchNode(i) for i in range(self.config.node_count)]
        self.content_pool: list[str] = []
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._worker: threading.Thread | None = None
        self._started_at: str | None = None
        self._last_cycle_at: str | None = None
        self._last_error: str | None = None

    @property
    def running(self) -> bool:
        return self._worker is not None and self._worker.is_alive()

    def _append_feed(self, item: str) -> None:
        self.content_pool.append(item)
        if len(self.content_pool) > self.config.max_feed_entries:
            del self.content_pool[:-self.config.max_feed_entries]

    def node_resonance(self, node: MatriarchNode) -> None:
        with self._lock:
            node.activation = min(
                1.0,
                node.activation + 0.03 * self.sovereign.dexterity * self.config.gain,
            )
            node.signal_ripple_factor = min(
                2.0,
                node.signal_ripple_factor + 0.02 * self.config.gain,
            )
            node.cycles += 1
            self._append_feed(f"node_{node.node_id}_resonance_feed_v2")
            self.sovereign.cycle_power = min(
                MAX_CYCLE_POWER,
                self.sovereign.cycle_power + 0.01 * self.config.gain,
            )
            self.sovereign.feed_rate = 1.0 + self.sovereign.cycle_power
            self.sovereign.sensory_depth = min(
                4.0,
                1.0 + self.sovereign.cycle_power * 0.5,
            )

    def sovereign_cycle(self) -> dict[str, Any]:
        with self._lock:
            for node in self.matriarchs:
                self.node_resonance(node)
            average_activation = sum(node.activation for node in self.matriarchs) / len(self.matriarchs)
            self.sovereign.dexterity = min(2.0, 1.0 + average_activation)
            self.sovereign.sensory_depth = max(1.0, self.sovereign.sensory_depth)
            self.sovereign.cycles += 1
            self._last_cycle_at = datetime.now(timezone.utc).isoformat()
            return self.snapshot()

    def _interval(self) -> float:
        return max(
            self.config.minimum_interval,
            0.08 / max(1.0, self.sovereign.feed_rate),
        )

    def run_loop(
        self,
        *,
        max_cycles: int | None = None,
        max_seconds: float | None = None,
    ) -> dict[str, Any]:
        if max_cycles is not None and max_cycles < 1:
            raise ValueError("max_cycles must be at least 1")
        if max_seconds is not None and max_seconds <= 0:
            raise ValueError("max_seconds must be positive")
        started = time.monotonic()
        with self._lock:
            self._started_at = datetime.now(timezone.utc).isoformat()
            self._stop_event.clear()
            self._last_error = None
        completed = 0
        while not self._stop_event.is_set():
            if max_cycles is not None and completed >= max_cycles:
                break
            if max_seconds is not None and time.monotonic() - started >= max_seconds:
                break
            self.sovereign_cycle()
            completed += 1
            if self._stop_event.wait(self._interval()):
                break
        return self.snapshot()

    def _run_worker(self, max_cycles: int | None, max_seconds: float | None) -> None:
        try:
            self.run_loop(max_cycles=max_cycles, max_seconds=max_seconds)
        except Exception as exc:  # pragma: no cover - surfaced through status
            with self._lock:
                self._last_error = f"{type(exc).__name__}: {exc}"
        finally:
            self._stop_event.set()

    def start(self, *, max_cycles: int | None = None, max_seconds: float | None = None) -> None:
        with self._lock:
            if self.running:
                raise RuntimeError("recursive loop is already running")
            self._worker = threading.Thread(
                target=self._run_worker,
                args=(max_cycles, max_seconds),
                name="shadow-garden-recursive-loop",
                daemon=True,
            )
            self._worker.start()

    def stop(self, timeout: float = 2.0) -> None:
        self._stop_event.set()
        worker = self._worker
        if worker is not None and worker.is_alive():
            worker.join(timeout=timeout)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "kind": "shadow_garden_recursive_node_status",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "status": "running" if self.running else "ready",
                "local_only": True,
                "symbolic_only": True,
                "guardrails": [
                    "bounded_gain",
                    "bounded_node_count",
                    "bounded_feed_pool",
                    "cooperative_cancellation",
                    "no_external_network_calls",
                    "no_provider_credentials",
                    "neutral_signal_metadata_only",
                ],
                "config": asdict(self.config),
                "route": {
                    "name": self.config.route_name,
                    "model": self.config.route_model,
                    "endpoint": self.config.route_endpoint,
                    "enabled": False,
                    "reason": "metadata-only local route; no model call is made",
                },
                "chronology": analyze_now(),
                "started_at": self._started_at,
                "last_cycle_at": self._last_cycle_at,
                "last_error": self._last_error,
                "sovereign": asdict(self.sovereign),
                "matriarchs": [asdict(node) for node in self.matriarchs],
                "content_pool": list(self.content_pool),
            }


def write_status(path: str, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f"{target.suffix}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(target)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Bounded local recursive node-evolution bridge")
    parser.add_argument("--nodes", type=int, default=DEFAULT_NODE_COUNT)
    parser.add_argument("--gain", type=float, default=1.0)
    parser.add_argument("--cycles", type=int, default=1)
    parser.add_argument("--continuous", action="store_true")
    parser.add_argument("--duration", type=float, default=0.0)
    parser.add_argument("--status-file", default=DEFAULT_STATUS_FILE)
    parser.add_argument("--route-name", default="local-open-weights")
    parser.add_argument("--route-model", default="deepseek-local")
    parser.add_argument(
        "--route-endpoint",
        default=os.environ.get("SG_LOCAL_MODEL_ENDPOINT", "http://127.0.0.1:11434/v1"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.continuous and args.duration <= 0:
            raise ValueError("--continuous requires a positive --duration safety limit")
        loop = RecursiveLoop(
            LoopConfig(
                node_count=args.nodes,
                gain=args.gain,
                route_name=args.route_name,
                route_model=args.route_model,
                route_endpoint=args.route_endpoint,
            )
        )
        payload = loop.run_loop(
            max_cycles=None if args.continuous else args.cycles,
            max_seconds=args.duration if args.continuous else None,
        )
        write_status(args.status_file, payload)
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except (ValueError, OSError) as exc:
        print(json.dumps({"error": str(exc)}))
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
