"""Eden Shadow — standalone turn-based floor-climbing RPG."""
from __future__ import annotations
import json
import random
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class Skill:
    name: str
    mp_cost: int
    base_damage: int
    cooldown_max: int
    cooldown: int = 0
    description: str = ""

    def is_ready(self) -> bool:
        return self.cooldown == 0

    def tick(self):
        if self.cooldown > 0:
            self.cooldown -= 1

    def use(self) -> int:
        """Returns base damage; caller pays the MP and applies cooldown."""
        dmg = self.base_damage + random.randint(0, self.base_damage // 2)
        self.cooldown = self.cooldown_max
        return dmg


@dataclass
class Character:
    name: str
    hp: int
    max_hp: int
    mp: int
    max_mp: int
    attack: int
    defense: int
    level: int = 1
    xp: int = 0
    xp_to_next: int = 100
    floor: int = 1
    skills: list[Skill] = field(default_factory=list)

    # ---------- combat helpers ----------

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.defense)
        self.hp = max(0, self.hp - dmg)
        return dmg

    def basic_attack(self) -> int:
        return self.attack + random.randint(0, self.attack // 2)

    def heal(self, amount: int):
        self.hp = min(self.max_hp, self.hp + amount)

    def restore_mp(self, amount: int):
        self.mp = min(self.max_mp, self.mp + amount)

    # ---------- progression ----------

    def gain_xp(self, amount: int) -> bool:
        """Returns True if levelled up."""
        self.xp += amount
        if self.xp >= self.xp_to_next:
            self._level_up()
            return True
        return False

    def _level_up(self):
        self.xp -= self.xp_to_next
        self.level += 1
        self.xp_to_next = int(self.xp_to_next * 1.5)
        self.max_hp += 20
        self.hp = self.max_hp
        self.max_mp += 10
        self.mp = self.max_mp
        self.attack += 3
        self.defense += 2

    # ---------- skill access ----------

    def ready_skills(self) -> list[Skill]:
        return [s for s in self.skills if s.is_ready()]

    def tick_cooldowns(self):
        for s in self.skills:
            s.tick()

    def use_skill(self, skill: Skill) -> Optional[int]:
        """Returns damage dealt or None if insufficient MP."""
        if self.mp < skill.mp_cost:
            return None
        self.mp -= skill.mp_cost
        return skill.use()


@dataclass
class Enemy:
    name: str
    hp: int
    max_hp: int
    attack: int
    defense: int
    xp_reward: int
    floor: int

    def is_alive(self) -> bool:
        return self.hp > 0

    def take_damage(self, raw: int) -> int:
        dmg = max(1, raw - self.defense)
        self.hp = max(0, self.hp - dmg)
        return dmg

    def basic_attack(self) -> int:
        return self.attack + random.randint(0, self.attack // 3)


# ---------------------------------------------------------------------------
# Factory helpers
# ---------------------------------------------------------------------------

STARTER_SKILLS: list[Skill] = [
    Skill("Slash",       mp_cost=5,  base_damage=20, cooldown_max=1, description="Quick blade strike."),
    Skill("Fireball",    mp_cost=15, base_damage=40, cooldown_max=3, description="Explosive mana burst."),
    Skill("Healing Wind",mp_cost=10, base_damage=0,  cooldown_max=4, description="Restore 30 HP."),
]

ADVANCED_SKILLS: list[Skill] = [
    Skill("Thunder Clap", mp_cost=20, base_damage=60, cooldown_max=4, description="AoE lightning."),
    Skill("Shadow Step",  mp_cost=8,  base_damage=35, cooldown_max=2, description="Fast shadow attack."),
]


def make_player(name: str = "Wanderer") -> Character:
    import copy
    skills = [copy.deepcopy(s) for s in STARTER_SKILLS]
    return Character(
        name=name, hp=120, max_hp=120, mp=60, max_mp=60,
        attack=18, defense=5, skills=skills
    )


def make_enemy(floor: int) -> Enemy:
    scale = 1 + (floor - 1) * 0.15
    templates = [
        ("Shade Wisp",    30, 8,  2,  20),
        ("Stone Golem",   60, 14, 6,  40),
        ("Void Serpent",  80, 18, 4,  60),
        ("Iron Knight",  100, 22, 10, 80),
        ("Floor Boss",   150, 30, 8, 120),
    ]
    idx = min(floor - 1, len(templates) - 1)
    if floor % 5 == 0:
        idx = len(templates) - 1  # boss every 5 floors
    nm, base_hp, base_atk, base_def, base_xp = templates[idx]
    hp = int(base_hp * scale)
    return Enemy(
        name=nm, hp=hp, max_hp=hp,
        attack=int(base_atk * scale),
        defense=int(base_def * scale),
        xp_reward=int(base_xp * scale),
        floor=floor,
    )


# ---------------------------------------------------------------------------
# Save / Load
# ---------------------------------------------------------------------------

SAVE_PATH = Path("eden_shadow_save.json")


def save_game(player: Character, path: Path = SAVE_PATH):
    data = asdict(player)
    path.write_text(json.dumps(data, indent=2))


def load_game(path: Path = SAVE_PATH) -> Optional[Character]:
    if not path.exists():
        return None
    raw = json.loads(path.read_text())
    skills = [Skill(**s) for s in raw.pop("skills", [])]
    char = Character(**raw, skills=skills)
    return char


# ---------------------------------------------------------------------------
# Combat engine (returns True if player survived)
# ---------------------------------------------------------------------------

def run_combat(player: Character, enemy: Enemy, io=None) -> bool:
    """Headless-friendly combat loop. `io` is a dict with callables:
       print(msg), choose_action(player, enemy) -> 'attack'|skill_name|'heal'|'flee'
    """
    _print = (io or {}).get("print", print)
    _choose = (io or {}).get("choose_action", _default_choose)

    _print(f"\n--- Encounter: {enemy.name} (Floor {enemy.floor}) ---")
    _print(f"  Enemy HP: {enemy.hp} | ATK: {enemy.attack} | DEF: {enemy.defense}")

    while player.is_alive() and enemy.is_alive():
        _print(f"\n[{player.name}] HP:{player.hp}/{player.max_hp}  MP:{player.mp}/{player.max_mp}")
        action = _choose(player, enemy)

        if action == "flee":
            _print("You fled the battle!")
            return True

        elif action == "attack":
            dmg = player.basic_attack()
            dealt = enemy.take_damage(dmg)
            _print(f"You attack for {dealt} damage.")

        elif action == "heal":
            heal_skill = next((s for s in player.skills if s.name == "Healing Wind" and s.is_ready()), None)
            if heal_skill and player.mp >= heal_skill.mp_cost:
                player.mp -= heal_skill.mp_cost
                heal_skill.cooldown = heal_skill.cooldown_max
                player.heal(30)
                _print(f"Healing Wind restores HP. HP now {player.hp}.")
            else:
                _print("Can't heal right now — using basic attack instead.")
                dealt = enemy.take_damage(player.basic_attack())
                _print(f"You attack for {dealt} damage.")

        else:
            skill = next((s for s in player.skills if s.name == action and s.is_ready()), None)
            if skill:
                if skill.name == "Healing Wind":
                    result = player.use_skill(skill)
                    if result is not None:
                        player.heal(30)
                        _print(f"{skill.name}: restore 30 HP. HP now {player.hp}.")
                    else:
                        _print("Not enough MP!")
                else:
                    result = player.use_skill(skill)
                    if result is not None:
                        dealt = enemy.take_damage(result)
                        _print(f"{skill.name}: {dealt} damage dealt!")
                    else:
                        _print("Not enough MP! Basic attack instead.")
                        dealt = enemy.take_damage(player.basic_attack())
                        _print(f"You attack for {dealt} damage.")
            else:
                _print("Invalid action, basic attack.")
                dealt = enemy.take_damage(player.basic_attack())
                _print(f"You attack for {dealt} damage.")

        if enemy.is_alive():
            edamage = enemy.basic_attack()
            taken = player.take_damage(edamage)
            _print(f"{enemy.name} hits you for {taken} damage.")

        player.tick_cooldowns()

    if player.is_alive():
        levelled = player.gain_xp(enemy.xp_reward)
        _print(f"\nVictory! +{enemy.xp_reward} XP.")
        if levelled:
            _print(f"LEVEL UP! Now level {player.level}.")
            if player.level == 3 and not any(s.name == "Thunder Clap" for s in player.skills):
                import copy
                player.skills.append(copy.deepcopy(ADVANCED_SKILLS[0]))
                _print("New skill unlocked: Thunder Clap!")
            if player.level == 5 and not any(s.name == "Shadow Step" for s in player.skills):
                import copy
                player.skills.append(copy.deepcopy(ADVANCED_SKILLS[1]))
                _print("New skill unlocked: Shadow Step!")
        player.restore_mp(15)
        return True
    else:
        _print("\nYou have fallen...")
        return False


def _default_choose(player: Character, enemy: Enemy) -> str:
    ready = player.ready_skills()
    print("\nActions: [1] attack", end="")
    for i, s in enumerate(ready, 2):
        print(f"  [{i}] {s.name} (MP:{s.mp_cost})", end="")
    print("  [f] flee")
    choice = input("Choice: ").strip().lower()
    if choice == "1" or choice == "attack":
        return "attack"
    if choice == "f" or choice == "flee":
        return "flee"
    try:
        idx = int(choice) - 2
        if 0 <= idx < len(ready):
            return ready[idx].name
    except ValueError:
        pass
    return "attack"


# ---------------------------------------------------------------------------
# Main game loop
# ---------------------------------------------------------------------------

def main():
    print("=== EDEN SHADOW ===")
    print("A lone wanderer climbs the endless tower.\n")

    save = load_game()
    if save:
        choice = input(f"Save found: {save.name} Lv{save.level} Floor {save.floor}. Load? [y/n]: ").strip().lower()
        player = save if choice == "y" else None
    else:
        player = None

    if player is None:
        name = input("Enter your name: ").strip() or "Wanderer"
        player = make_player(name)

    while True:
        print(f"\n--- Floor {player.floor} ---")
        enemy = make_enemy(player.floor)
        survived = run_combat(player, enemy)

        if not survived:
            print("Game over. Your journey ends here.")
            SAVE_PATH.unlink(missing_ok=True)
            break

        save_game(player)
        print(f"Progress saved. Floor {player.floor} cleared.")
        player.floor += 1

        cont = input("Continue to next floor? [y/n]: ").strip().lower()
        if cont != "y":
            print("Rest well, wanderer.")
            break


if __name__ == "__main__":
    main()
