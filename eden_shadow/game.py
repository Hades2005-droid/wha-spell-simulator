#!/usr/bin/env python3
"""Eden Shadow — a self-contained turn-based floor-climbing RPG.

Standard library only. Deterministic when seeded (same seed => same run).
The only file it touches is its JSON save. No network, no external writes.

Play:
    python3 -m eden_shadow.game            # interactive
    python3 -m eden_shadow.game --demo     # headless auto-play (smoke test)
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

TARGET_FLOOR = 10
BOSS_EVERY = 5
XP_PER_LEVEL = 25
MP_REGEN_PER_ROUND = 1
REST_HP_FRACTION = 0.4  # recovered after clearing a floor
REST_MP_FRACTION = 0.6
DEFAULT_SAVE_NAME = "eden_shadow_save.json"

GRUNT_NAMES = ("Gloom Sprite", "Ash Wisp", "Thorn Shade", "Mire Crawler", "Hollow Husk")
BOSS_NAMES = ("Warden of the Black Sun", "Eden Gatekeeper")


@dataclass(frozen=True)
class Skill:
    name: str
    kind: str  # "damage" | "heal" | "guard"
    mp_cost: int
    cooldown: int  # locked turns after casting
    power: float  # damage multiplier, heal fraction of max HP, or defense bonus
    duration: int = 0  # guard only: enemy hits it absorbs
    unlock_level: int = 1


SKILLS = (
    Skill("Ember Strike", "damage", mp_cost=3, cooldown=1, power=1.6),
    Skill("Mend", "heal", mp_cost=4, cooldown=2, power=0.4),
    Skill("Gale Slash", "damage", mp_cost=5, cooldown=2, power=2.2, unlock_level=3),
    Skill("Stone Ward", "guard", mp_cost=6, cooldown=3, power=4, duration=2, unlock_level=5),
)


def roll_damage(attack: int, defense: int, rng: random.Random, mult: float = 1.0) -> int:
    variance = rng.uniform(0.85, 1.15)
    return max(1, round(attack * mult * variance) - max(0, defense))


@dataclass
class Enemy:
    name: str
    max_hp: int
    hp: int
    attack: int
    defense: int
    xp_reward: int
    is_boss: bool

    @classmethod
    def for_floor(cls, floor: int) -> "Enemy":
        is_boss = floor % BOSS_EVERY == 0
        hp = 16 + 6 * floor
        attack = 4 + floor
        defense = 1 + floor // 3
        xp = 10 + 5 * floor
        if is_boss:
            name = BOSS_NAMES[(floor // BOSS_EVERY - 1) % len(BOSS_NAMES)]
            hp = round(hp * 1.7)
            attack = round(attack * 1.3)
            xp *= 2
        else:
            name = GRUNT_NAMES[(floor - 1) % len(GRUNT_NAMES)]
        return cls(
            name=name, max_hp=hp, hp=hp, attack=attack, defense=defense,
            xp_reward=xp, is_boss=is_boss,
        )


@dataclass
class Player:
    max_hp: int = 40
    hp: int = 40
    max_mp: int = 12
    mp: int = 12
    attack: int = 7
    defense: int = 2
    level: int = 1
    xp: int = 0
    cooldowns: dict = field(default_factory=dict)
    guard_bonus: int = 0
    guard_hits_left: int = 0

    # -- skills ------------------------------------------------------------
    def known_skills(self) -> list[Skill]:
        return [s for s in SKILLS if s.unlock_level <= self.level]

    def ready_skills(self) -> list[Skill]:
        return [
            s for s in self.known_skills()
            if self.cooldowns.get(s.name, 0) == 0 and s.mp_cost <= self.mp
        ]

    def can_cast(self, skill: Skill) -> bool:
        return skill in self.ready_skills()

    def start_cooldown(self, skill: Skill) -> None:
        # +1 so the end-of-round tick on the casting turn still leaves
        # `cooldown` full locked turns.
        self.cooldowns[skill.name] = skill.cooldown + 1

    def tick_round(self) -> None:
        for name, turns in list(self.cooldowns.items()):
            if turns > 0:
                self.cooldowns[name] = turns - 1
        self.mp = min(self.max_mp, self.mp + MP_REGEN_PER_ROUND)

    # -- damage intake -----------------------------------------------------
    def effective_defense(self) -> int:
        return self.defense + (self.guard_bonus if self.guard_hits_left > 0 else 0)

    def absorb_hit(self) -> None:
        if self.guard_hits_left > 0:
            self.guard_hits_left -= 1
            if self.guard_hits_left == 0:
                self.guard_bonus = 0

    # -- progression ---------------------------------------------------------
    def xp_to_next(self) -> int:
        return self.level * XP_PER_LEVEL

    def gain_xp(self, amount: int) -> list[str]:
        """Apply XP, handle (possibly chained) level-ups. Returns log lines."""
        lines = [f"You gain {amount} XP."]
        self.xp += amount
        while self.xp >= self.xp_to_next():
            self.xp -= self.xp_to_next()
            self.level += 1
            self.max_hp += 10
            self.max_mp += 3
            self.attack += 3
            self.defense += 1
            self.hp = self.max_hp
            self.mp = self.max_mp
            lines.append(
                f"Level up! You are now level {self.level} "
                f"(HP {self.max_hp}, MP {self.max_mp}, ATK {self.attack}, DEF {self.defense})."
            )
            for skill in SKILLS:
                if skill.unlock_level == self.level:
                    lines.append(f"New skill unlocked: {skill.name}!")
        return lines

    # -- persistence ---------------------------------------------------------
    def to_dict(self) -> dict:
        return {
            "max_hp": self.max_hp, "hp": self.hp,
            "max_mp": self.max_mp, "mp": self.mp,
            "attack": self.attack, "defense": self.defense,
            "level": self.level, "xp": self.xp,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(**{k: data[k] for k in (
            "max_hp", "hp", "max_mp", "mp", "attack", "defense", "level", "xp",
        )})


class Game:
    """One run of Eden Shadow: climb floors, fight, level, save."""

    def __init__(self, seed: int | None = None, save_path: Path | str | None = None,
                 quiet: bool = False):
        self.rng = random.Random(seed)
        self.save_path = Path(save_path) if save_path else Path.cwd() / DEFAULT_SAVE_NAME
        self.quiet = quiet
        self.log: list[str] = []
        self.player = Player()
        self.floor = 1
        self.status = "climbing"  # climbing | victory | defeat

    # -- output --------------------------------------------------------------
    def say(self, line: str) -> None:
        self.log.append(line)
        if not self.quiet:
            print(line)

    # -- persistence ----------------------------------------------------------
    def save(self) -> None:
        payload = {
            "version": 1,
            "floor": self.floor,
            "status": self.status,
            "player": self.player.to_dict(),
        }
        self.save_path.write_text(json.dumps(payload, indent=2))

    def load(self) -> bool:
        if not self.save_path.exists():
            return False
        try:
            data = json.loads(self.save_path.read_text())
            self.player = Player.from_dict(data["player"])
            self.floor = int(data["floor"])
            self.status = data.get("status", "climbing")
            return True
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            return False

    def new_run(self) -> None:
        self.player = Player()
        self.floor = 1
        self.status = "climbing"
        if self.save_path.exists():
            self.save_path.unlink()
        self.say("A fresh run begins at floor 1.")

    # -- combat ----------------------------------------------------------------
    def player_action(self, enemy: Enemy, action: Skill | None) -> None:
        """Resolve the player's turn. action=None means basic attack."""
        if action is None:
            dmg = roll_damage(self.player.attack, enemy.defense, self.rng)
            enemy.hp -= dmg
            self.say(f"You strike {enemy.name} for {dmg}.")
            return

        skill = action
        self.player.mp -= skill.mp_cost
        self.player.start_cooldown(skill)
        if skill.kind == "damage":
            dmg = roll_damage(self.player.attack, enemy.defense, self.rng, mult=skill.power)
            enemy.hp -= dmg
            self.say(f"{skill.name}! {enemy.name} takes {dmg}.")
        elif skill.kind == "heal":
            healed = min(round(self.player.max_hp * skill.power),
                         self.player.max_hp - self.player.hp)
            self.player.hp += healed
            self.say(f"{skill.name} restores {healed} HP ({self.player.hp}/{self.player.max_hp}).")
        elif skill.kind == "guard":
            self.player.guard_bonus = int(skill.power)
            self.player.guard_hits_left = skill.duration
            self.say(f"{skill.name} raises your defense by {int(skill.power)} "
                     f"for the next {skill.duration} hits.")

    def enemy_action(self, enemy: Enemy) -> None:
        dmg = roll_damage(enemy.attack, self.player.effective_defense(), self.rng)
        self.player.absorb_hit()
        self.player.hp -= dmg
        self.say(f"{enemy.name} hits you for {dmg} ({max(0, self.player.hp)}/{self.player.max_hp} HP).")

    def battle(self, enemy: Enemy, choose_action) -> str:
        """Fight one enemy. choose_action(game, enemy) -> Skill | None.

        Returns "win" or "lose".
        """
        label = "BOSS" if enemy.is_boss else "enemy"
        self.say(f"-- Floor {self.floor}: {label} {enemy.name} "
                 f"(HP {enemy.hp}, ATK {enemy.attack}, DEF {enemy.defense}) --")
        while True:
            self.player_action(enemy, choose_action(self, enemy))
            if enemy.hp <= 0:
                self.say(f"{enemy.name} falls!")
                for line in self.player.gain_xp(enemy.xp_reward):
                    self.say(line)
                self.player.tick_round()
                return "win"
            self.enemy_action(enemy)
            self.player.tick_round()
            if self.player.hp <= 0:
                self.say("You collapse. The shadow claims this run.")
                return "lose"

    def rest(self) -> None:
        """Catch your breath between floors: partial HP/MP recovery."""
        healed = min(round(self.player.max_hp * REST_HP_FRACTION),
                     self.player.max_hp - self.player.hp)
        restored = min(round(self.player.max_mp * REST_MP_FRACTION),
                       self.player.max_mp - self.player.mp)
        self.player.hp += healed
        self.player.mp += restored
        if healed or restored:
            self.say(f"You catch your breath (+{healed} HP, +{restored} MP).")

    def clear_floor(self) -> None:
        self.floor += 1
        if self.floor > TARGET_FLOOR:
            self.status = "victory"
            self.say(f"Floor {TARGET_FLOOR} cleared — the Eden gate opens. VICTORY.")
        else:
            self.rest()
            self.say(f"You climb to floor {self.floor}. Progress saved.")
        self.save()

    # -- auto-play (demo / tests) ----------------------------------------------
    @staticmethod
    def auto_policy(game: "Game", enemy: Enemy) -> Skill | None:
        ready = game.player.ready_skills()
        heal = next((s for s in ready if s.kind == "heal"), None)
        if heal and game.player.hp < game.player.max_hp * 0.45:
            return heal
        guard = next((s for s in ready if s.kind == "guard"), None)
        if guard and enemy.is_boss and game.player.guard_hits_left == 0:
            return guard
        damage_skills = sorted(
            (s for s in ready if s.kind == "damage"),
            key=lambda s: s.power, reverse=True,
        )
        if damage_skills and enemy.hp > game.player.attack:
            return damage_skills[0]
        return None

    def run_auto(self, max_floors: int = TARGET_FLOOR) -> str:
        """Headless run using the built-in policy. Returns final status."""
        while self.status == "climbing" and self.floor <= min(max_floors, TARGET_FLOOR):
            enemy = Enemy.for_floor(self.floor)
            if self.battle(enemy, self.auto_policy) == "lose":
                self.status = "defeat"
                self.save()
                break
            self.clear_floor()
        if self.status == "climbing":
            self.say(f"Auto-climb paused at floor {self.floor}.")
        return self.status

    # -- interactive -------------------------------------------------------------
    def prompt_action(self, game: "Game", enemy: Enemy) -> Skill | None:
        ready = self.player.ready_skills()
        self.say(f"HP {self.player.hp}/{self.player.max_hp}  MP {self.player.mp}/{self.player.max_mp}"
                 f"  |  {enemy.name} HP {enemy.hp}")
        options = ["[a] attack"] + [
            f"[{i + 1}] {s.name} (MP {s.mp_cost}, CD {s.cooldown})"
            for i, s in enumerate(ready)
        ]
        while True:
            try:
                raw = input(f"{'  '.join(options)} > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                self.say("\nSaving and leaving the tower.")
                self.save()
                sys.exit(0)
            if raw in ("a", ""):
                return None
            if raw.isdigit() and 1 <= int(raw) <= len(ready):
                return ready[int(raw) - 1]
            self.say("Pick 'a' or a listed skill number.")

    def run_interactive(self) -> None:
        self.say("=== EDEN SHADOW ===")
        self.say(f"Climb to floor {TARGET_FLOOR}. Bosses guard every {BOSS_EVERY}th floor.")
        while True:
            while self.status == "climbing":
                enemy = Enemy.for_floor(self.floor)
                if self.battle(enemy, self.prompt_action) == "lose":
                    self.status = "defeat"
                    self.save()
                else:
                    self.clear_floor()
            self.say(f"Run over: {self.status.upper()} on floor {self.floor}.")
            try:
                again = input("Play again? [y/N] > ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                again = "n"
            if again == "y":
                self.new_run()
            else:
                self.say("The Garden rests. Goodbye.")
                return


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Eden Shadow — turn-based floor climber")
    parser.add_argument("--demo", action="store_true", help="headless auto-play run")
    parser.add_argument("--seed", type=int, default=None, help="RNG seed (deterministic runs)")
    parser.add_argument("--floors", type=int, default=TARGET_FLOOR,
                        help="max floors for --demo (default %(default)s)")
    parser.add_argument("--save", type=Path, default=None, help="save file path")
    parser.add_argument("--new", action="store_true", help="ignore any existing save")
    args = parser.parse_args(argv)

    game = Game(seed=args.seed, save_path=args.save)
    if not args.new and game.load():
        game.say(f"Loaded save: floor {game.floor}, level {game.player.level}.")
        if game.status != "climbing":
            game.new_run()

    if args.demo:
        status = game.run_auto(max_floors=args.floors)
        game.say(f"Demo finished: {status} (floor {game.floor}, level {game.player.level}).")
        return 0 if status != "defeat" else 1

    game.run_interactive()
    return 0


if __name__ == "__main__":
    sys.exit(main())
