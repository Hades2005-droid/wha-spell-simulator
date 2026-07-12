#!/usr/bin/env python3
"""
Phase 2 recursive spell creation — bounded, content-neutral.

One evolve cycle max by default (Fable 5 contract). Couples:
  * black_sun_phase2_engine (spacetime + moon_18 + Q24 adapter)
  * recursive_node_bridge (bounded 9-node resonance)
  * local spell candidate synthesis (metadata / prompt fuel only)

Never starts an infinite loop. Never calls providers. Never prints secrets.
AGI task ref is metadata-only (URL may 404 until Cursor/GitHub surfaces it).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "shadow_garden.phase2_recursive_spell.v1"
PACKAGE_ID = "shadow-garden-phase2-fable5-black-sun-home-sim"
CARRIER = "love_and_harmony_6"
BRIDGE_SIGNATURE = "f2e596cd043d6819"
CANONICAL_ID = "q24_eternal_dao_temperance_14_harmony_paradox_ignite_19_10_1"
AGI_TASK_REF = (
    "https://github.com/Hades2005-droid/wha-spell-simulator"
    "/tasks/65421066-bc27-4336-a4a6-5f5e7b79d090"
)
MAX_CYCLES = 3
DEFAULT_CYCLES = 1
QUALITY_FLOOR = 0.55
PHASE2_BOOST = 0.06

HOME = Path.home()
WHA = Path(os.environ.get("WHA_SPELL_ROOT", HOME / "wha-spell-simulator"))
SG = Path(os.environ.get("SHADOW_GARDEN_ROOT", HOME / "ShadowGarden"))
DEFAULT_OUT = (
    WHA / "shadow_garden_handoff" / "terminal_auto" / "outbox" / "phase2_recursive_spells.json"
)
STATUS_OUT = Path("/tmp/shadow_garden_phase2_recursive_spells.json")

CONTROLS = {
    "external_fetch": False,
    "provider_calls": False,
    "credentials_allowed": False,
    "generated_code_execution": False,
    "explicit_adult_rendering": False,
    "content_neutral_base_build": True,
    "symbolic_only": True,
    "bounded_cycles_max": MAX_CYCLES,
    "infinite_loop": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def stable_id(*parts: str) -> str:
    blob = "|".join(parts).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()[:16]


def run_json(argv: list[str], timeout: float = 45) -> dict[str, Any]:
    proc = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
        cwd=str(WHA),
    )
    if proc.returncode != 0:
        return {
            "ok": False,
            "exit": proc.returncode,
            "error": (proc.stderr or proc.stdout or "")[:240],
        }
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError as exc:
        return {"ok": False, "error": f"json: {exc}", "raw_head": (proc.stdout or "")[:200]}


def phase2_snapshot() -> dict[str, Any]:
    engine = WHA / "tools" / "black_sun_phase2_engine.py"
    if not engine.is_file():
        return {"ok": False, "error": "missing black_sun_phase2_engine.py"}
    result = run_json([sys.executable, str(engine), "self-test"])
    result.setdefault("ok", False)
    return result


def recursive_snapshot(cycles: int = 1, gain: float = 1.0) -> dict[str, Any]:
    bridge = WHA / "tools" / "recursive_node_bridge.py"
    if not bridge.is_file():
        return {"ok": False, "error": "missing recursive_node_bridge.py"}
    return run_json(
        [
            sys.executable,
            str(bridge),
            "--cycles",
            str(max(1, min(cycles, MAX_CYCLES))),
            "--gain",
            str(gain),
        ]
    )


def spell_fuel() -> dict[str, Any]:
    path = SG / "live" / "spacetime_alchemy" / "spell_generator_latest.json"
    if not path.is_file():
        return {"ok": False, "path": str(path)}
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": str(exc)[:160]}
    return {
        "ok": True,
        "path": str(path),
        "jing_power": doc.get("jing_power"),
        "authority": doc.get("authority"),
        "policy": doc.get("policy"),
        "sampled_at": doc.get("sampled_at"),
    }


# Content-neutral Phase 2 spell templates (technical mechanics, not supernatural claims)
TEMPLATES: list[dict[str, Any]] = [
    {
        "id": "phase2-black-sun-home",
        "displayName": "Black Sun Home Anchor",
        "element": "light",
        "intent": (
            "Content-neutral home-simulation anchor: Temperance 14 unreduced, "
            "justice toggle solar/lunar, kitchen cabin Floor-22 protected node."
        ),
        "mechanic": "scene_registry_gate",
        "base_quality": 0.72,
    },
    {
        "id": "phase2-moon-18-gate",
        "displayName": "Moon-18 Catalyst Gate",
        "element": "water",
        "intent": (
            "Deterministic moon_18 gate before land: charge catalysts 5+6+7 = 18, "
            "then complete landing. Party-game turn prompt only."
        ),
        "mechanic": "turn_gate_checklist",
        "base_quality": 0.78,
    },
    {
        "id": "phase2-temperance-14-toggle",
        "displayName": "Temperance 14 Justice Toggle",
        "element": "wind",
        "intent": (
            "Dual render profile switch (MODE_SOLAR ↔ MODE_LUNAR) keyed to Q24 "
            "anchor 14. Accessibility / atmosphere choice, not authority override."
        ),
        "mechanic": "accessibility_mode_toggle",
        "base_quality": 0.74,
    },
    {
        "id": "phase2-ignition-19-10-1",
        "displayName": "Ignition Path 19→10→1",
        "element": "fire",
        "intent": (
            "Ordered ignition path Sun-19 → gap-10 → loop-1 for Black Sun home sim. "
            "Explainable state machine step, MAX_TURNS=24 hard cap."
        ),
        "mechanic": "state_machine_arc",
        "base_quality": 0.76,
    },
    {
        "id": "phase2-recursive-resonance",
        "displayName": "Bounded Resonance Evolve",
        "element": "earth",
        "intent": (
            "One-cycle recursive node resonance feeding spell quality — gain≤8, "
            "nodes≤9, local-only metadata. Never infinite."
        ),
        "mechanic": "bounded_recursive_improve",
        "base_quality": 0.70,
    },
]


def score_candidate(
    template: dict[str, Any],
    *,
    cycle: int,
    phase2_ok: bool,
    moon_open: bool,
    resonance: float,
    jing: float | None,
) -> dict[str, Any]:
    quality = float(template["base_quality"])
    if phase2_ok:
        quality += PHASE2_BOOST
    if moon_open:
        quality += 0.04
    # Bounded resonance contribution from recursive node cycle power
    quality += min(0.08, max(0.0, resonance) * 0.01)
    if jing is not None and jing > 0:
        quality += min(0.03, jing / 500.0)
    # Slight improvement per allowed evolve cycle (capped)
    quality += min(0.05, (cycle - 1) * 0.02)
    quality = round(min(1.0, quality), 4)
    ready = quality >= QUALITY_FLOOR and phase2_ok
    return {
        "id": template["id"],
        "displayName": template["displayName"],
        "element": template["element"],
        "intent": template["intent"],
        "mechanic": template["mechanic"],
        "quality": quality,
        "status": "ready_for_user_approval" if ready else "needs_spell_refinement",
        "fingerprint": stable_id(
            template["id"], str(quality), str(cycle), BRIDGE_SIGNATURE
        ),
        "phase2": {
            "package_id": PACKAGE_ID,
            "carrier": CARRIER,
            "q24_canonical_id": CANONICAL_ID,
            "anchor": 14,
            "reduce_anchor": False,
            "sequence": [19, 10, 1],
            "moon_18_open": moon_open,
        },
        "controls": {
            "executionMode": "manifest_only",
            "localOnly": True,
            "approved": False,
            "contentNeutral": True,
        },
    }


def evolve(*, cycles: int = DEFAULT_CYCLES, gain: float = 1.0) -> dict[str, Any]:
    cycles = max(1, min(int(cycles), MAX_CYCLES))
    phase2 = phase2_snapshot()
    recursive = recursive_snapshot(cycles=1, gain=gain)
    fuel = spell_fuel()

    phase2_ok = bool(phase2.get("ok"))
    moon_open = False
    if phase2_ok:
        for row in phase2.get("results") or []:
            if row.get("check") == "moon_18_gate" and row.get("ok"):
                moon_open = True
                break

    resonance = 0.0
    if isinstance(recursive, dict) and recursive.get("sovereign"):
        resonance = float(recursive["sovereign"].get("cycle_power") or 0.0)
    elif isinstance(recursive, dict) and recursive.get("ok") is False:
        resonance = 0.0

    jing = fuel.get("jing_power") if fuel.get("ok") else None
    if isinstance(jing, (int, float)):
        jing_f = float(jing)
    else:
        jing_f = None

    history: list[dict[str, Any]] = []
    best: list[dict[str, Any]] = []
    for cycle in range(1, cycles + 1):
        candidates = [
            score_candidate(
                t,
                cycle=cycle,
                phase2_ok=phase2_ok,
                moon_open=moon_open,
                resonance=resonance + (cycle - 1) * 0.5,
                jing=jing_f,
            )
            for t in TEMPLATES
        ]
        candidates.sort(key=lambda c: c["quality"], reverse=True)
        mean_q = round(sum(c["quality"] for c in candidates) / len(candidates), 4)
        history.append(
            {
                "cycle": cycle,
                "mean_quality": mean_q,
                "ready_count": sum(
                    1 for c in candidates if c["status"] == "ready_for_user_approval"
                ),
                "top_id": candidates[0]["id"],
                "top_quality": candidates[0]["quality"],
            }
        )
        best = candidates

    improved = (
        len(history) >= 2 and history[-1]["mean_quality"] > history[0]["mean_quality"]
    ) or (len(history) == 1 and history[0]["ready_count"] >= 4)

    return {
        "schema": SCHEMA,
        "generated_at": utc_now(),
        "phase": 2,
        "package_id": PACKAGE_ID,
        "carrier": CARRIER,
        "bridge_signature": BRIDGE_SIGNATURE,
        "agi_task_ref": AGI_TASK_REF,
        "agi_task_note": "metadata pointer only; GitHub task URL may 404 until surfaced",
        "cycles_requested": cycles,
        "cycles_ran": len(history),
        "improved": improved,
        "phase2_engine": {
            "ok": phase2_ok,
            "passed": phase2.get("passed"),
            "total": phase2.get("total"),
            "moon_18_open": moon_open,
        },
        "recursive_node": {
            "ok": recursive.get("status") == "ready" or recursive.get("ok") is not False,
            "cycle_power": resonance,
            "status": recursive.get("status"),
        },
        "spell_fuel": fuel,
        "history": history,
        "spells": best,
        "metric": {
            "name": "mean_spell_quality",
            "before": history[0]["mean_quality"] if history else 0,
            "after": history[-1]["mean_quality"] if history else 0,
            "ready_count": history[-1]["ready_count"] if history else 0,
            "acceptance": "ready_count>=4 and phase2_ok",
        },
        "controls": dict(CONTROLS),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 2 bounded recursive spell creation (content-neutral)"
    )
    parser.add_argument(
        "command",
        nargs="?",
        default="evolve",
        choices=["evolve", "write", "status"],
    )
    parser.add_argument(
        "--cycles",
        type=int,
        default=DEFAULT_CYCLES,
        help=f"evolve cycles (1–{MAX_CYCLES}, default {DEFAULT_CYCLES})",
    )
    parser.add_argument("--gain", type=float, default=1.0)
    parser.add_argument("--out", default="", help="extra output path")
    args = parser.parse_args(argv)

    if args.cycles > MAX_CYCLES:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": f"cycles cannot exceed {MAX_CYCLES} (Fable5 contract)",
                }
            ),
            file=sys.stderr,
        )
        return 2

    payload = evolve(cycles=args.cycles, gain=args.gain)
    print(json.dumps(payload, indent=2))

    if args.command in ("write", "evolve"):
        outs = [STATUS_OUT, DEFAULT_OUT]
        if args.out:
            outs.append(Path(args.out))
        for path in outs:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
            print(f"wrote {path}", file=sys.stderr)

    ok = bool(payload.get("phase2_engine", {}).get("ok")) and bool(
        payload.get("improved")
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
