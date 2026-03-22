from __future__ import annotations

import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import glfw

from smalloldgames.games.sketch_hopper import BlackHole, SketchHopperScene, Monster, Pickup, Projectile
from smalloldgames.data.storage import ScoreRepository
from smalloldgames.engine.input import InputState


class SketchHopperTests(unittest.TestCase):
    def make_scene(self) -> SketchHopperScene:
        return SketchHopperScene(lambda: None, seed=7)

    def test_horizontal_wraparound(self) -> None:
        scene = self.make_scene()
        scene.player.x = scene.world_width - 6.0
        scene._tick_player(0.1, 1.0)
        self.assertLess(scene.player.x, 40.0)

    def test_platform_generation_stays_ahead_of_camera(self) -> None:
        scene = self.make_scene()
        scene.camera_y = 1800.0
        previous_top = scene.highest_platform_y
        scene._spawn_platforms()
        self.assertGreaterEqual(scene.highest_platform_y, scene.camera_y + scene.world_height + 200.0)
        anchors = [platform for platform in scene.platforms if platform.anchor and platform.y > previous_top]
        self.assertTrue(anchors)
        self.assertTrue(all(platform.kind != "broken" for platform in anchors))
        self.assertTrue(
            all(
                abs(current.x - previous.x) <= scene.path_max_shift + 0.001
                for previous, current in zip(anchors, anchors[1:])
            )
        )

    def test_special_platforms_obey_min_height_thresholds(self) -> None:
        scene = self.make_scene()
        self.assertEqual(scene._choose_anchor_kind(scene.spring_min_height - 1.0, 0.6), "stable")
        self.assertNotEqual(scene._choose_anchor_kind(scene.moving_platform_min_height + 20.0, 1.0), "broken")
        low_extra_results = {scene._choose_extra_kind(scene.spring_min_height - 1.0, 1.0) for _ in range(20)}
        self.assertEqual(low_extra_results, {"stable"})

    def test_monsters_continue_spawning_ahead_of_camera(self) -> None:
        scene = self.make_scene()
        scene.camera_y = 4200.0
        scene.monsters = []
        scene.highest_monster_y = 0.0
        scene._spawn_platforms()
        scene._spawn_monsters()
        visible_monsters = [
            monster
            for monster in scene.monsters
            if scene.camera_y + 120.0 <= monster.y <= scene.camera_y + scene.world_height + 220.0
        ]
        self.assertGreaterEqual(len(visible_monsters), scene.min_visible_monsters)

    def test_monster_top_up_does_not_force_early_spawn(self) -> None:
        scene = self.make_scene()
        scene.camera_y = 600.0
        scene.monsters = []
        scene.highest_monster_y = 0.0
        scene._spawn_platforms()
        scene._spawn_monsters()
        self.assertTrue(all(monster.y >= scene.monster_min_height for monster in scene.monsters))

    def test_pickups_continue_spawning_ahead_of_camera(self) -> None:
        scene = self.make_scene()
        scene.camera_y = 4200.0
        scene.pickups = []
        scene.highest_pickup_y = -2000.0
        scene._spawn_platforms()
        scene._spawn_pickups()
        visible_pickups = [
            pickup
            for pickup in scene.pickups
            if scene.camera_y + 80.0 <= pickup.y <= scene.camera_y + scene.world_height + 160.0
        ]
        self.assertGreaterEqual(len(visible_pickups), scene.min_visible_pickups)

    def test_pickups_can_show_up_before_late_game(self) -> None:
        scene = self.make_scene()
        scene.camera_y = scene.pickup_top_up_min_camera_y + 40.0
        scene.pickups = []
        scene.highest_pickup_y = -2000.0
        scene._spawn_platforms()
        scene._spawn_pickups()
        self.assertTrue(any(pickup.y >= max(scene.pickup_min_height, scene.player.y + 160.0) for pickup in scene.pickups))

    def test_pickups_do_not_spawn_too_early(self) -> None:
        scene = self.make_scene()
        scene.camera_y = scene.pickup_top_up_min_camera_y - 10.0
        scene.pickups = []
        scene._spawn_platforms()
        scene._spawn_pickups()
        self.assertEqual(scene.pickups, [])

    def test_pickups_obey_min_vertical_gap(self) -> None:
        scene = self.make_scene()
        scene.pickups = []
        scene.highest_pickup_y = 1200.0
        platform = scene.platforms[0]
        platform.kind = "stable"
        platform.y = 1500.0
        scene._maybe_add_pickup(platform, 1.0)
        self.assertEqual(scene.pickups, [])

    def test_decorative_clouds_spawn_ahead_of_camera(self) -> None:
        scene = self.make_scene()
        previous_top = scene.highest_cloud_y
        scene.camera_y = 2200.0
        scene._spawn_clouds()
        self.assertGreater(scene.highest_cloud_y, previous_top)
        self.assertTrue(any(cloud.y > previous_top for cloud in scene.clouds))

    def test_spawned_platforms_do_not_stack_on_top_of_each_other(self) -> None:
        scene = self.make_scene()
        scene.camera_y = 1800.0
        previous_top = scene.highest_platform_y
        scene._spawn_platforms()
        spawned = [platform for platform in scene.platforms if platform.y > previous_top]
        for index, first in enumerate(spawned):
            for second in spawned[index + 1 :]:
                overlaps_x = first.x < second.x + second.width + scene.overlap_x_padding and first.x + first.width + scene.overlap_x_padding > second.x
                overlaps_y = first.y < second.y + second.height + scene.overlap_y_padding and first.y + first.height + scene.overlap_y_padding > second.y
                self.assertFalse(overlaps_x and overlaps_y)

    def test_landing_on_platform_restores_jump_velocity(self) -> None:
        scene = self.make_scene()
        platform = scene.platforms[0]
        scene.player.x = platform.x + 10.0
        scene.player.y = platform.y + 30.0
        scene.player.velocity_y = -260.0
        scene._tick_player(0.1, 0.0)
        self.assertGreater(scene.player.velocity_y, 0.0)
        self.assertAlmostEqual(scene.player.y, platform.y + platform.height)

    def test_spring_platform_launches_higher(self) -> None:
        scene = self.make_scene()
        platform = scene.platforms[0]
        platform.kind = "spring"
        scene.player.x = platform.x + 10.0
        scene.player.y = platform.y + 30.0
        scene.player.velocity_y = -260.0
        scene._tick_player(0.1, 0.0)
        self.assertEqual(scene.player.velocity_y, scene.spring_jump_velocity)
        self.assertGreater(platform.spring_timer, 0.0)

    def test_spring_feedback_timer_expires(self) -> None:
        scene = self.make_scene()
        platform = scene.platforms[0]
        platform.kind = "spring"
        platform.spring_timer = scene.spring_feedback_duration
        scene._tick_platforms(scene.spring_feedback_duration)
        self.assertEqual(platform.spring_timer, 0.0)

    def test_fake_platform_breaks_without_jump(self) -> None:
        scene = self.make_scene()
        platform = scene.platforms[0]
        platform.kind = "fake"
        scene.player.x = platform.x + 10.0
        scene.player.y = platform.y + 30.0
        scene.player.velocity_y = -260.0
        scene._tick_player(0.1, 0.0)
        self.assertTrue(platform.broken)
        self.assertLess(scene.player.velocity_y, 0.0)

    def test_vanish_platform_gives_jump_then_disappears(self) -> None:
        scene = self.make_scene()
        platform = scene.platforms[0]
        platform.kind = "vanish"
        scene.player.x = platform.x + 10.0
        scene.player.y = platform.y + 30.0
        scene.player.velocity_y = -260.0
        scene._tick_player(0.1, 0.0)
        self.assertEqual(scene.player.velocity_y, scene.jump_velocity)
        self.assertGreater(platform.state_timer, 0.0)
        scene._tick_platforms(platform.state_timer)
        self.assertTrue(platform.broken)

    def test_hover_monster_bobs_around_base_height(self) -> None:
        scene = self.make_scene()
        monster = Monster(
            x=140.0,
            y=300.0,
            width=scene.monster_width,
            height=scene.monster_height,
            velocity_x=0.0,
            base_y=300.0,
            bob_phase=0.0,
            bob_speed=math.pi,
            bob_amplitude=18.0,
        )
        scene.monsters.append(monster)
        scene._tick_monsters(0.5)
        self.assertAlmostEqual(monster.y, 318.0, places=3)

    def test_jetpack_pickup_starts_boost(self) -> None:
        scene = self.make_scene()
        scene.pickups = []
        scene.pickups.append(Pickup(x=scene.player.x, y=scene.player.y, width=30.0, height=32.0, kind="jetpack"))
        scene._handle_pickups()
        self.assertGreater(scene.jetpack_timer, 0.0)
        self.assertEqual(len(scene.pickups), 0)

    def test_propeller_pickup_starts_boost(self) -> None:
        scene = self.make_scene()
        scene.pickups = []
        scene.pickups.append(Pickup(x=scene.player.x, y=scene.player.y, width=30.0, height=34.0, kind="propeller"))
        scene._handle_pickups()
        self.assertGreater(scene.propeller_timer, 0.0)
        self.assertEqual(scene.player.velocity_y, scene.propeller_velocity)

    def test_rocket_pickup_starts_stronger_boost(self) -> None:
        scene = self.make_scene()
        scene.pickups = []
        scene.pickups.append(Pickup(x=scene.player.x, y=scene.player.y, width=26.0, height=42.0, kind="rocket"))
        scene._handle_pickups()
        self.assertGreater(scene.rocket_timer, 0.0)
        self.assertEqual(scene.player.velocity_y, scene.rocket_velocity)

    def test_boots_boost_next_landing(self) -> None:
        scene = self.make_scene()
        scene.boots_charges_left = scene.boots_charges
        platform = scene.platforms[0]
        scene.player.x = platform.x + 10.0
        scene.player.y = platform.y + 30.0
        scene.player.velocity_y = -260.0
        scene._tick_player(0.1, 0.0)
        self.assertEqual(scene.player.velocity_y, scene.boots_jump_velocity)
        self.assertEqual(scene.boots_charges_left, scene.boots_charges - 1)

    def test_shield_blocks_one_monster_collision(self) -> None:
        scene = self.make_scene()
        scene.shield_timer = scene.shield_duration
        scene.monsters.append(
            Monster(
                x=scene.player.x + 8.0,
                y=scene.player.y + 6.0,
                width=scene.monster_width,
                height=scene.monster_height,
                velocity_x=0.0,
            )
        )
        scene._handle_monster_collisions()
        self.assertFalse(scene.game_over)
        self.assertEqual(scene.shield_timer, 0.0)
        self.assertEqual(len(scene.monsters), 0)

    def test_hostile_projectile_can_end_run(self) -> None:
        scene = self.make_scene()
        scene.projectiles.append(
            Projectile(
                x=scene.player.x,
                y=scene.player.y,
                width=10.0,
                height=14.0,
                velocity_y=0.0,
                hostile=True,
            )
        )
        scene._tick_projectiles(0.0)
        self.assertTrue(scene.game_over)

    def test_black_hole_can_end_run(self) -> None:
        scene = self.make_scene()
        scene.black_holes.append(
            BlackHole(
                x=scene.player.x,
                y=scene.player.y,
                width=scene.black_hole_size,
                height=scene.black_hole_size,
                pulse_phase=0.0,
                pulse_speed=1.0,
            )
        )
        scene._apply_black_holes(0.016)
        self.assertTrue(scene.game_over)

    def test_touch_controls_move_player(self) -> None:
        scene = self.make_scene()
        scene.touch_controls_enabled = True
        inputs = InputState()
        inputs.on_cursor_pos(40.0, 40.0)
        inputs.on_pointer(glfw.PRESS)
        original_x = scene.player.x
        scene.update(0.1, inputs)
        self.assertLess(scene.player.x, original_x)

    def test_pause_button_toggles_pause(self) -> None:
        scene = self.make_scene()
        scene.touch_controls_enabled = True
        inputs = InputState()
        inputs.on_cursor_pos(480.0, 910.0)
        inputs.on_pointer(glfw.PRESS)
        scene.update(0.0, inputs)
        self.assertTrue(scene.paused)

    def test_pause_menu_can_toggle_sound_setting(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = ScoreRepository(Path(temp_dir) / "scores.sqlite3")
            scene = SketchHopperScene(lambda: None, score_repository=repository, seed=7)
            scene.paused = True
            scene.sound_enabled = True
            inputs = InputState()
            inputs.on_cursor_pos(180.0, 460.0)
            inputs.on_pointer(glfw.PRESS)
            scene.update(0.0, inputs)
            self.assertFalse(scene.sound_enabled)
            self.assertFalse(repository.get_sound_enabled())

    def test_pause_menu_can_switch_to_balance_page(self) -> None:
        scene = self.make_scene()
        scene.paused = True
        inputs = InputState()
        inputs.on_key(glfw.KEY_B, glfw.PRESS)
        scene.update(0.0, inputs)
        self.assertEqual(scene.pause_page, "balance")

    def test_balance_reset_requires_confirmation(self) -> None:
        scene = self.make_scene()
        scene.pause_page = "balance"
        scene.config = scene.config.__class__(spring_min_height=999.0)
        scene._apply_config()
        scene._trigger_or_apply_balance_reset()
        self.assertTrue(scene.confirm_reset_defaults)
        self.assertEqual(scene.spring_min_height, 999.0)

    def test_balance_adjustment_updates_runtime_config(self) -> None:
        scene = self.make_scene()
        original = scene.spring_min_height
        scene.balance_index = 0
        scene._adjust_balance(1)
        self.assertGreater(scene.spring_min_height, original)
        self.assertEqual(scene.spring_min_height, scene.config.spring_min_height)

    def test_theme_transition_starts_when_camera_crosses_threshold(self) -> None:
        scene = self.make_scene()
        scene.camera_y = scene.theme_height_1 + 10.0
        scene._update_theme_progression()
        self.assertEqual(scene.theme_index, 1)
        self.assertGreater(scene.theme_transition_timer, 0.0)

    def test_projectile_removes_monster(self) -> None:
        scene = self.make_scene()
        scene.monsters.append(
            Monster(
                x=120.0,
                y=420.0,
                width=scene.monster_width,
                height=scene.monster_height,
                velocity_x=0.0,
            )
        )
        scene.projectiles.append(
            Projectile(
                x=138.0,
                y=422.0,
                width=8.0,
                height=18.0,
                velocity_y=0.0,
            )
        )
        scene._tick_projectiles(0.0)
        self.assertEqual(len(scene.monsters), 0)
        self.assertEqual(len(scene.projectiles), 0)

    def test_player_shot_stays_faster_than_upward_player_motion(self) -> None:
        scene = self.make_scene()
        scene.player.velocity_y = scene.jetpack_velocity
        scene._shoot()

        projectile = scene.projectiles[0]
        self.assertGreater(projectile.velocity_y, scene.player.velocity_y)

    def test_monster_collision_ends_run(self) -> None:
        scene = self.make_scene()
        scene.monsters.append(
            Monster(
                x=scene.player.x + 8.0,
                y=scene.player.y + 6.0,
                width=scene.monster_width,
                height=scene.monster_height,
                velocity_x=0.0,
            )
        )
        scene._handle_monster_collisions()
        self.assertTrue(scene.game_over)

    def test_game_over_persists_score_to_repository(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = ScoreRepository(Path(temp_dir) / "scores.sqlite3")
            repository.set_player_name("rocket")
            scene = SketchHopperScene(lambda: None, score_repository=repository, seed=7)
            scene.score = 321
            scene.player.y = scene.camera_y - scene.player.height - 200.0
            scene.player.velocity_y = -200.0
            scene.update(0.0, InputState())
            self.assertTrue(scene.game_over)
            self.assertEqual(repository.best_score("sketch_hopper"), 321)
            self.assertEqual(scene.best_score, 321)
            self.assertIsNotNone(scene.latest_rank)
            self.assertEqual(repository.top_scores("sketch_hopper", limit=1)[0].player_name, "ROCKET")


if __name__ == "__main__":
    unittest.main()
