#!/usr/bin/env python3
"""
Black Sun Phase 2 engine — Spacetime Alchemy + home simulation bridge.

Unifies:
  * Spacetime Alchemy compact/bedrock index (metadata only)
  * Home Black Sun registry (render profiles, justice toggle 14)
  * Deterministic Fable5 observer game (subprocess adapter contract)

Credential-free. Content-neutral. Local-only. Symbolic Phase 2 checkpoint.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.black_sun_phase2_engine.v1"
PACKAGE_ID = "shadow-garden-phase2-fable5-black-sun-home-sim"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CANONICAL_ID = "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1"

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
MON = Path(os.environ.get("SHADOW_MONITOR_ROOT", HOME / "shadow_garden_may30_monitoring"))
SOUTH_STAR = MON / "shaoshi_bridge" / "south_star"

CONTROLS = {
    "external_fetch": False,
    "browser_automation": False,
    "agent_broadcast": False,
    "credentials_allowed": False,
    "generated_code_execution": False,
    "provider_calls": False,
    "explicit_adult_rendering": False,
    "content_neutral_base_build": True,
    "symbolic_only": True,
    "safe_abort": True,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def _load_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_fable5_engine() -> Any:
    path = SOUTH_STAR / "fable5_shadow_garden_unified.py"
    if not path.is_file():
        raise FileNotFoundError(f"missing engine at {path}")
    return _load_module("fable5_shadow_garden_unified", path)


def load_home_black_sun() -> Any:
    path = SOUTH_STAR / "home_black_sun_registry.py"
    if not path.is_file():
        raise FileNotFoundError(f"missing registry at {path}")
    return _load_module("home_black_sun_registry", path)


def spacetime_snapshot() -> dict[str, Any]:
    compact_path = SG / "live" / "spacetime_alchemy" / "fable5-compact.json"
    bedrock_path = SG / "live" / "spacetime_alchemy" / "PERPLEXITY_CONTEXT_BEDROCK.md"
    out: dict[str, Any] = {
        "compact_path": str(compact_path),
        "bedrock_path": str(bedrock_path),
        "compact_exists": compact_path.is_file(),
        "bedrock_exists": bedrock_path.is_file(),
    }
    if compact_path.is_file():
        try:
            compact = json.loads(compact_path.read_text(encoding="utf-8"))
            out["compact_version"] = compact.get("version") or compact.get("export_version")
            out["compact_keys"] = sorted(compact.keys())[:12]
        except (json.JSONDecodeError, OSError):
            out["compact_parse_ok"] = False
        else:
            out["compact_parse_ok"] = True
    root = str(SG)
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        from spacetime_alchemy import SpacetimeAlchemy  # type: ignore

        ledger = SpacetimeAlchemy().compute("2026-07-12")
        out["chronology"] = {
            "date": ledger.get("date"),
            "micro": ledger.get("micro"),
            "macro": ledger.get("macro"),
        }
        out["spacetime_import_ok"] = True
    except Exception as exc:  # noqa: BLE001 — snapshot must not crash
        out["spacetime_import_ok"] = False
        out["spacetime_error"] = f"{type(exc).__name__}: {exc}"[:160]
    return out


def apply_action(
    *,
    action: str,
    seed: int = 42,
    mastery: int = 10,
    history: list[str] | None = None,
    max_turns: int = 24,
) -> dict[str, Any]:
    """Q24StateAdapter subprocess contract — one action, deterministic replay."""
    engine = load_fable5_engine()
    GameConfig = engine.GameConfig
    Phase = engine.Phase

    prior = list(history or [])
    game = engine.Fable5Universe(
        GameConfig(seed=seed, mastery=mastery, max_turns=max_turns)
    )
    if prior:
        game.play(prior)

    from_state = game.phase.value
    try:
        game.choose(action)
        ok = True
        reason = ""
    except (RuntimeError, ValueError) as exc:
        ok = False
        reason = str(exc)[:200]

    snap = game.snapshot()
    aborted = game.phase is Phase.ABORTED or not ok
    return {
        "schema": "shadow_garden.q24_state_adapter_response.v1",
        "ok": ok and game.phase not in {Phase.ABORTED},
        "from_state": from_state,
        "next_state": snap["phase"],
        "resonance": snap["resonance"],
        "turn": snap["turn"],
        "aborted": aborted,
        "reason": reason,
        "moon_18": snap["moon_18"],
        "available_actions": list(game.available_actions()),
        "history_len": len(game.history),
    }


def replay_actions(
    actions: list[str],
    *,
    seed: int = 42,
    mastery: int = 10,
    max_turns: int = 24,
) -> dict[str, Any]:
    engine = load_fable5_engine()
    game = engine.Fable5Universe(
        engine.GameConfig(seed=seed, mastery=mastery, max_turns=max_turns)
    )
    return game.play(actions)


def build_manifest() -> dict[str, Any]:
    home_mod = load_home_black_sun()
    session = home_mod.HomeBlackSunSession()
    toggle = session.justice_toggle_14()
    spacetime = spacetime_snapshot()
    engine = load_fable5_engine()
    sample = engine.Fable5Universe().play(engine.default_actions())
    return {
        "schema": "shadow_garden.black_sun_phase2_manifest.v1",
        "generated_at": utc_now(),
        "phase": 2,
        "package_id": PACKAGE_ID,
        "q24_canonical_id": CANONICAL_ID,
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "symbolic_only": True,
        "spacetime_alchemy": spacetime,
        "home_black_sun": {
            "render_profile": session.render_profile.value,
            "justice_toggle": toggle,
            "home_protected": session.home.snapshot(),
        },
        "engine_sample": {
            "phase": sample["state"]["phase"],
            "moon_18": sample["state"]["moon_18"],
            "universe_ready": sample["state"]["universe_ready"],
        },
        "adapter": {
            "backend_mode": "subprocess",
            "cli": "python3 tools/black_sun_phase2_engine.py json",
            "max_turns": engine.MAX_TURNS,
        },
        "controls": dict(CONTROLS),
    }


def run_self_test() -> dict[str, Any]:
    checks: list[dict[str, Any]] = []

    def record(name: str, ok: bool, **extra: Any) -> None:
        checks.append({"check": name, "ok": ok, **extra})

    spacetime = spacetime_snapshot()
    record(
        "spacetime_compact",
        spacetime.get("compact_exists") is True,
        compact_exists=spacetime.get("compact_exists"),
    )
    record(
        "spacetime_bedrock",
        spacetime.get("bedrock_exists") is True,
        bedrock_exists=spacetime.get("bedrock_exists"),
    )
    record(
        "spacetime_import",
        spacetime.get("spacetime_import_ok") is True,
        chronology=spacetime.get("chronology"),
    )

    home_mod = load_home_black_sun()
    session = home_mod.HomeBlackSunSession()
    report = session.report()
    record(
        "home_black_sun",
        report.get("phase") == 2 and report.get("symbolic_only") is True,
        package_id=report.get("package_id"),
    )

    engine = load_fable5_engine()
    actions = engine.default_actions()
    first = replay_actions(actions)
    second = replay_actions(actions)
    record(
        "determinism_default_arc",
        first == second,
        digest=first.get("report_digest", "")[:16],
    )

    moon = first["state"]["moon_18"]
    record(
        "moon_18_gate",
        moon["target"] == 18 and moon["gate_open"] is True,
        charge=moon["charge"],
    )

    vectors = [
        (42, 10, actions),
        (7, 5, actions),
        (99, 0, actions),
        (1, 10, actions),
        (2026, 7, actions),
        (18, 3, actions),
    ]
    vector_ok = True
    for seed, mastery, vec in vectors:
        report = replay_actions(vec, seed=seed, mastery=mastery)
        if report["state"]["moon_18"]["gate_open"] is not True:
            vector_ok = False
            break
        if report["state"]["phase"] != "complete":
            vector_ok = False
            break
    record("deterministic_vectors_x6", vector_ok, count=len(vectors))

    adapter = apply_action(action="launch", seed=42, mastery=10)
    record(
        "q24_adapter_contract",
        adapter.get("schema") == "shadow_garden.q24_state_adapter_response.v1"
        and adapter.get("next_state") == "glide",
        next_state=adapter.get("next_state"),
    )

    passed = sum(1 for c in checks if c.get("ok"))
    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "phase": 2,
        "package_id": PACKAGE_ID,
        "total": len(checks),
        "passed": passed,
        "failed": len(checks) - passed,
        "ok": passed == len(checks),
        "results": checks,
        "controls": dict(CONTROLS),
    }


def handle_json(payload: dict[str, Any]) -> dict[str, Any]:
    cmd = payload.get("command", "apply_action")
    if cmd == "apply_action":
        return apply_action(
            action=str(payload.get("action", "")),
            seed=int(payload.get("seed", 42)),
            mastery=int(payload.get("mastery", 10)),
            history=payload.get("history"),
            max_turns=int(payload.get("max_turns", 24)),
        )
    if cmd == "replay":
        return replay_actions(
            list(payload.get("actions") or []),
            seed=int(payload.get("seed", 42)),
            mastery=int(payload.get("mastery", 10)),
            max_turns=int(payload.get("max_turns", 24)),
        )
    if cmd == "manifest":
        return build_manifest()
    if cmd == "self_test":
        return run_self_test()
    return {"ok": False, "error": f"unknown command: {cmd}"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Black Sun Phase 2 — Spacetime Alchemy + home simulation bridge"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="self-test",
        choices=["self-test", "manifest", "apply", "replay", "json"],
    )
    parser.add_argument("--action", default="launch")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--mastery", type=int, default=10)
    parser.add_argument("--max-turns", type=int, default=24)
    parser.add_argument(
        "--actions",
        default="launch,fable,harmony,chariot,land",
        help="comma-separated replay actions",
    )
    args = parser.parse_args(argv)

    if args.command == "self-test":
        result = run_self_test()
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.command == "manifest":
        print(json.dumps(build_manifest(), indent=2))
        return 0

    if args.command == "apply":
        result = apply_action(
            action=args.action,
            seed=args.seed,
            mastery=args.mastery,
            max_turns=args.max_turns,
        )
        print(json.dumps(result, indent=2))
        return 0 if result.get("ok") else 1

    if args.command == "replay":
        actions = [a.strip() for a in args.actions.split(",") if a.strip()]
        result = replay_actions(
            actions,
            seed=args.seed,
            mastery=args.mastery,
            max_turns=args.max_turns,
        )
        print(json.dumps(result, indent=2))
        return 0

    if args.command == "json":
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError as exc:
            print(json.dumps({"ok": False, "error": str(exc)}))
            return 1
        print(json.dumps(handle_json(payload), indent=2))
        return 0

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
