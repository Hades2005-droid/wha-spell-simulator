"""Test suite for Eden Shadow game logic."""
import copy
import json
import tempfile
from pathlib import Path

import pytest

from eden_shadow.game import (
    Character, Enemy, Skill,
    make_player, make_enemy,
    save_game, load_game,
    run_combat, STARTER_SKILLS,
)


# ---------------------------------------------------------------------------
# Character tests
# ---------------------------------------------------------------------------

def test_take_damage_reduces_hp():
    p = make_player()
    p.take_damage(20)
    assert p.hp < p.max_hp


def test_damage_never_zero():
    p = make_player()
    p.defense = 9999
    dealt = p.take_damage(1)
    assert dealt == 1
    assert p.hp == p.max_hp - 1


def test_heal_caps_at_max():
    p = make_player()
    p.hp = 10
    p.heal(9999)
    assert p.hp == p.max_hp


def test_gain_xp_level_up():
    p = make_player()
    old_level = p.level
    levelled = p.gain_xp(200)
    assert levelled
    assert p.level == old_level + 1
    assert p.hp == p.max_hp  # HP restored on level-up


def test_no_level_up_below_threshold():
    p = make_player()
    levelled = p.gain_xp(10)
    assert not levelled
    assert p.level == 1


# ---------------------------------------------------------------------------
# Skill tests
# ---------------------------------------------------------------------------

def test_skill_cooldown():
    skill = copy.deepcopy(STARTER_SKILLS[0])  # Slash, cooldown_max=1
    assert skill.is_ready()
    skill.use()
    assert not skill.is_ready()
    skill.tick()
    assert skill.is_ready()


def test_skill_mp_cost():
    p = make_player()
    slash = next(s for s in p.skills if s.name == "Slash")
    cost = slash.mp_cost
    p.mp = cost - 1
    result = p.use_skill(slash)
    assert result is None  # not enough MP


def test_skill_use_deducts_mp():
    p = make_player()
    slash = next(s for s in p.skills if s.name == "Slash")
    before = p.mp
    p.use_skill(slash)
    assert p.mp == before - slash.mp_cost


def test_fireball_damage_range():
    results = set()
    skill = copy.deepcopy(STARTER_SKILLS[1])  # Fireball
    for _ in range(50):
        skill.cooldown = 0
        dmg = skill.use()
        results.add(dmg)
    assert len(results) > 1  # randomness present
    assert all(40 <= d <= 60 for d in results)


# ---------------------------------------------------------------------------
# Enemy tests
# ---------------------------------------------------------------------------

def test_enemy_scales_with_floor():
    e1 = make_enemy(1)
    e5 = make_enemy(5)
    assert e5.hp > e1.hp
    assert e5.xp_reward > e1.xp_reward


def test_boss_on_floor_5():
    boss = make_enemy(5)
    assert boss.name == "Floor Boss"


def test_enemy_take_damage():
    e = make_enemy(1)
    old_hp = e.hp
    dealt = e.take_damage(10)
    assert e.hp == old_hp - dealt
    assert e.hp >= 0


# ---------------------------------------------------------------------------
# Combat tests
# ---------------------------------------------------------------------------

def _make_io(actions):
    """Build a headless IO dict that feeds a sequence of actions."""
    log = []
    queue = list(actions)

    def _print(msg):
        log.append(msg)

    def _choose(player, enemy):
        return queue.pop(0) if queue else "attack"

    return {"print": _print, "choose_action": _choose}, log


def test_combat_player_wins_weak_enemy():
    player = make_player()
    enemy = Enemy(name="Dummy", hp=1, max_hp=1, attack=0, defense=0, xp_reward=10, floor=1)
    io, _ = _make_io(["attack"])
    survived = run_combat(player, enemy, io)
    assert survived
    assert player.xp > 0


def test_combat_player_dies():
    player = make_player()
    player.hp = 1
    enemy = Enemy(name="Crusher", hp=9999, max_hp=9999, attack=9999, defense=0, xp_reward=0, floor=1)
    io, _ = _make_io(["attack"] * 100)
    survived = run_combat(player, enemy, io)
    assert not survived
    assert not player.is_alive()


def test_combat_flee():
    player = make_player()
    enemy = make_enemy(1)
    io, log = _make_io(["flee"])
    survived = run_combat(player, enemy, io)
    assert survived
    assert any("fled" in m for m in log)


def test_combat_skill_use():
    player = make_player()
    enemy = Enemy(name="Target", hp=200, max_hp=200, attack=1, defense=0, xp_reward=10, floor=1)
    # Use Slash then keep attacking
    io, _ = _make_io(["Slash"] + ["attack"] * 50)
    survived = run_combat(player, enemy, io)
    assert survived


def test_combat_healing_wind():
    player = make_player()
    player.hp = 10
    enemy = Enemy(name="Poke", hp=5, max_hp=5, attack=1, defense=0, xp_reward=5, floor=1)
    io, log = _make_io(["Healing Wind", "attack"])
    run_combat(player, enemy, io)
    assert any("HP" in m or "restore" in m.lower() for m in log)


# ---------------------------------------------------------------------------
# Save / Load tests
# ---------------------------------------------------------------------------

def test_save_and_load_roundtrip():
    player = make_player("TestHero")
    player.floor = 3
    player.xp = 55
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    try:
        save_game(player, path)
        loaded = load_game(path)
        assert loaded is not None
        assert loaded.name == "TestHero"
        assert loaded.floor == 3
        assert loaded.xp == 55
        assert len(loaded.skills) == len(player.skills)
    finally:
        path.unlink(missing_ok=True)


def test_load_missing_returns_none():
    result = load_game(Path("/nonexistent/path/save.json"))
    assert result is None


def test_save_json_structure():
    player = make_player("Aria")
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = Path(f.name)
    try:
        save_game(player, path)
        data = json.loads(path.read_text())
        assert "name" in data
        assert "hp" in data
        assert "skills" in data
        assert isinstance(data["skills"], list)
    finally:
        path.unlink(missing_ok=True)
