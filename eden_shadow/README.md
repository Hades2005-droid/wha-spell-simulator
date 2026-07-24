# Eden Shadow

A self-contained turn-based floor-climbing RPG. No external dependencies — stdlib only.

## Play

```bash
python3 -m eden_shadow.game
```

Or headless (auto-play smoke test):

```bash
python3 -m eden_shadow.game --demo --seed 7
```

## Features

- **Floor progression** — each floor spawns a scaled enemy; every 5th floor is a boss
- **Turn-based combat** — basic attack or pick from your ready skills each turn
- **Skill system** — MP costs, cooldowns, unlock new skills at level 3 and 5
- **XP / leveling** — stats grow on level-up; HP and MP restored
- **JSON save state** — progress saved after every cleared floor (`eden_shadow_save.json`)
- **Deterministic** — pass `--seed N` and the same run replays exactly
- **Test suite** — `python3 -m unittest tests.test_eden_shadow -v`

## Rules

Climb to floor 10. Each turn choose a basic attack (`a`) or a ready skill
(number). Skills cost MP and go on cooldown; MP regenerates 1 per round.
Defeat ends the run; victory opens the Eden gate. `Ctrl-C` saves and exits.

## Scope

Local game slice only: no network calls, no external writes, the only file it
touches is its own JSON save.
