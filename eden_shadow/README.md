# Eden Shadow

A self-contained turn-based floor-climbing RPG. No external dependencies — stdlib only.

## Play

```bash
python -m eden_shadow.game
```

Or from the repo root:

```bash
python eden_shadow/game.py
```

## Features

- **Floor progression** — each floor spawns a scaled enemy; every 5th floor is a boss
- **Turn-based combat** — basic attack or pick from your ready skills each turn
- **Skill system** — MP costs, cooldowns, unlock new skills at level 3 and 5
- **XP / leveling** — stats grow on level-up; HP and MP restored
- **JSON save state** — progress saved after every cleared floor
- **Test suite** — `pytest eden_shadow/tests/`

## Skills

| Skill | MP | Base DMG | Cooldown | Notes |
|---|---|---|---|---|
| Slash | 5 | 20 | 1 | Quick strike |
| Fireball | 15 | 40 | 3 | Burst damage |
| Healing Wind | 10 | — | 4 | Restore 30 HP |
| Thunder Clap | 20 | 60 | 4 | Unlocked Lv 3 |
| Shadow Step | 8 | 35 | 2 | Unlocked Lv 5 |

## Tests

```bash
pip install pytest
pytest eden_shadow/tests/ -v
```
