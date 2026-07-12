# Shadow Garden Phase 2 — Black Sun Home Simulation Open

Status: **Phase 2 development opened** on branch `cursor/hooks-secret-scanners`.

## Gate meaning

Phase 2 is the **Fable 5 Black Sun home simulation** checkpoint after Phase 1 closure (Magician sovereign prime, Q24 alpha, final three catalysts 4→5→6→7).

It unifies:

- **Spacetime Alchemy** — compact + bedrock index, chronology ledger (metadata only)
- **Home Black Sun registry** — render profiles, justice toggle 14, protected home node
- **Q24 deterministic engine** — subprocess adapter contract for Godot `Q24StateAdapter`

Carrier: `love_and_harmony_6`  
Bridge signature: `f2e596cd043d6819`  
Q24 anchor: 14 (unreduced)  
Sequence: [19, 10, 1]

## Safety conversion

- Symbolic / content-neutral base build only.
- No credentials, provider calls, browser automation, or external fetch.
- Secret-scan hooks remain enforced (`.cursor/hooks/`).
- Adult content stays in separate DLC depot pattern — not in base build.

## Phase 2 engine entry points

```bash
# Self-test (moon_18 gate + 6 deterministic vectors + spacetime import)
python3 tools/black_sun_phase2_engine.py self-test

# Phase 2 manifest (spacetime + home black sun + engine sample)
python3 tools/black_sun_phase2_engine.py manifest

# Q24StateAdapter subprocess contract (single action)
python3 tools/black_sun_phase2_engine.py apply --action launch --seed 42 --mastery 10

# JSON stdin mode for Godot subprocess bridge
echo '{"command":"apply_action","action":"launch","seed":42,"mastery":10}' \
  | python3 tools/black_sun_phase2_engine.py json

# Unified packet (includes phase2 check)
python3 tools/shadow_garden_packet.py write
```

## Catalyst objectives (from coaching packet)

| Catalyst | Scope | Holder |
|----------|-------|--------|
| A | Q24 registry hardening review | Claude front |
| B | Two-track architecture (Godot 4 + Ren'Py) | Claude front |
| C | JSON return to monitoring inbox | Claude front |
| **Engine** | Spacetime + home sim bridge | Local terminal |

## Connector posture

- Atlassian: no write unless explicitly approved.
- GitHub: no commit/push/PR unless explicitly approved.
- X: no social interactions.
- Qdrant: no mutation.

## Next return command

```bash
python3 tools/black_sun_phase2_engine.py self-test
python3 -m unittest tests.test_black_sun_phase2_engine -v
python3 tools/shadow_garden_packet.py write
```
