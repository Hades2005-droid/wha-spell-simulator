"""Deterministic tests for the Eden Shadow floor-climbing RPG."""

import json
import tempfile
import unittest
from pathlib import Path

from eden_shadow.game import (
    BOSS_EVERY,
    SKILLS,
    TARGET_FLOOR,
    Enemy,
    Game,
    Player,
    roll_damage,
)


def quiet_game(seed=7, save_path=None):
    return Game(seed=seed, save_path=save_path, quiet=True)


class EnemyScalingTest(unittest.TestCase):
    def test_every_fifth_floor_is_boss(self):
        for floor in range(1, TARGET_FLOOR + 1):
            enemy = Enemy.for_floor(floor)
            self.assertEqual(enemy.is_boss, floor % BOSS_EVERY == 0, f"floor {floor}")

    def test_stats_scale_with_floor(self):
        low, high = Enemy.for_floor(1), Enemy.for_floor(9)
        self.assertLess(low.max_hp, high.max_hp)
        self.assertLess(low.attack, high.attack)
        self.assertLess(low.xp_reward, high.xp_reward)

    def test_boss_outclasses_neighbor_grunt(self):
        grunt, boss = Enemy.for_floor(4), Enemy.for_floor(5)
        self.assertGreater(boss.max_hp, grunt.max_hp)
        self.assertGreater(boss.xp_reward, grunt.xp_reward)


class CombatMathTest(unittest.TestCase):
    def test_damage_has_floor_of_one(self):
        import random
        rng = random.Random(1)
        for _ in range(50):
            self.assertGreaterEqual(roll_damage(1, 999, rng), 1)

    def test_guard_absorbs_limited_hits(self):
        player = Player()
        player.guard_bonus = 4
        player.guard_hits_left = 2
        self.assertEqual(player.effective_defense(), player.defense + 4)
        player.absorb_hit()
        self.assertEqual(player.effective_defense(), player.defense + 4)
        player.absorb_hit()
        self.assertEqual(player.effective_defense(), player.defense)
        self.assertEqual(player.guard_bonus, 0)


class ProgressionTest(unittest.TestCase):
    def test_level_up_grows_stats_and_restores(self):
        player = Player()
        player.hp = 5
        lines = player.gain_xp(player.xp_to_next())
        self.assertEqual(player.level, 2)
        self.assertEqual(player.hp, player.max_hp)
        self.assertEqual(player.mp, player.max_mp)
        self.assertTrue(any("Level up" in line for line in lines))

    def test_chained_level_ups(self):
        player = Player()
        player.gain_xp(25 + 50 + 3)  # levels 1->2->3 with 3 spare XP
        self.assertEqual(player.level, 3)
        self.assertEqual(player.xp, 3)

    def test_skills_unlock_at_levels_3_and_5(self):
        player = Player()
        names_at = lambda: {s.name for s in player.known_skills()}
        self.assertNotIn("Gale Slash", names_at())
        player.level = 3
        self.assertIn("Gale Slash", names_at())
        self.assertNotIn("Stone Ward", names_at())
        player.level = 5
        self.assertIn("Stone Ward", names_at())


class CooldownTest(unittest.TestCase):
    def test_cast_skill_locks_for_cooldown_turns(self):
        game = quiet_game()
        enemy = Enemy.for_floor(1)
        skill = SKILLS[0]  # Ember Strike, cooldown 1
        game.player_action(enemy, skill)
        game.player.tick_round()  # end of casting round
        self.assertNotIn(skill, game.player.ready_skills())
        game.player.tick_round()  # one full locked round elapses
        self.assertIn(skill, game.player.ready_skills())

    def test_mp_regenerates_each_round(self):
        player = Player()
        player.mp = 0
        player.tick_round()
        self.assertEqual(player.mp, 1)


class SaveLoadTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.save = Path(self.tmp.name) / "save.json"
        self.addCleanup(self.tmp.cleanup)

    def test_round_trip(self):
        game = quiet_game(save_path=self.save)
        game.floor = 4
        game.player.level = 3
        game.player.xp = 11
        game.save()

        loaded = quiet_game(save_path=self.save)
        self.assertTrue(loaded.load())
        self.assertEqual(loaded.floor, 4)
        self.assertEqual(loaded.player.level, 3)
        self.assertEqual(loaded.player.xp, 11)

    def test_save_written_after_cleared_floor(self):
        game = quiet_game(save_path=self.save)
        game.clear_floor()
        self.assertTrue(self.save.exists())
        data = json.loads(self.save.read_text())
        self.assertEqual(data["floor"], 2)

    def test_corrupt_save_is_rejected(self):
        self.save.write_text("{not json")
        game = quiet_game(save_path=self.save)
        self.assertFalse(game.load())

    def test_new_run_resets_state_and_save(self):
        game = quiet_game(save_path=self.save)
        game.floor = 6
        game.save()
        game.new_run()
        self.assertEqual(game.floor, 1)
        self.assertEqual(game.status, "climbing")
        self.assertFalse(self.save.exists())


class AutoRunTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def run_seeded(self, seed, name):
        game = quiet_game(seed=seed, save_path=Path(self.tmp.name) / name)
        status = game.run_auto()
        return game, status

    def test_full_run_terminates_cleanly(self):
        game, status = self.run_seeded(7, "a.json")
        self.assertIn(status, ("victory", "defeat"))
        self.assertGreaterEqual(game.player.level, 1)
        self.assertTrue(game.log)

    def test_same_seed_replays_identically(self):
        game_a, status_a = self.run_seeded(42, "a.json")
        game_b, status_b = self.run_seeded(42, "b.json")
        self.assertEqual(status_a, status_b)
        self.assertEqual(game_a.log, game_b.log)

    def test_defeat_path_is_reachable(self):
        game = quiet_game(seed=3, save_path=Path(self.tmp.name) / "d.json")
        game.player.max_hp = game.player.hp = 1
        game.player.attack = 1
        status = game.run_auto()
        self.assertEqual(status, "defeat")
        self.assertEqual(game.status, "defeat")

    def test_victory_sets_end_state(self):
        # Overpowered player guarantees victory regardless of rolls.
        game = quiet_game(seed=1, save_path=Path(self.tmp.name) / "v.json")
        game.player.attack = 500
        game.player.max_hp = game.player.hp = 500
        status = game.run_auto()
        self.assertEqual(status, "victory")
        self.assertGreater(game.floor, TARGET_FLOOR)


if __name__ == "__main__":
    unittest.main()
