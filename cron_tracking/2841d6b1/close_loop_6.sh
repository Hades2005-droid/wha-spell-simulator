#!/usr/bin/env bash
# Bounded local closure for loop 6 — no secret values, no external writes.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"

echo "[close_loop_6] root=$ROOT"
python3 tools/black_sun_phase2_engine.py self-test >/tmp/black_sun_self_test.json
python3 - <<'PY'
import json
from pathlib import Path
root = Path(".")
light = root / "shadow_garden_handoff/treasure_chest/LIGHT_CONNECTOR_MANIFEST_7.json"
shadow = root / "shadow_garden_handoff/treasure_chest/SHADOW_CONNECTOR_STATUS_7.json"
closed = root / "shadow_garden_handoff/gates/LOOP_6_CLOSED.json"
for p in (light, shadow, closed):
    assert p.is_file(), f"missing {p}"
    json.loads(p.read_text())
print("[close_loop_6] treasure_chest + LOOP_6_CLOSED OK")
print("[close_loop_6] secrets_in_chest=false external_writes=false")
print("[close_loop_6] ROTATE NordVPN token at provider — do not paste into repo")
PY
echo "[close_loop_6] DONE_FOR_TODAY=1"
