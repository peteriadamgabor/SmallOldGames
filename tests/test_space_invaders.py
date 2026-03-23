from __future__ import annotations

import unittest

from smalloldgames.engine import SceneContext
from smalloldgames.engine.input import InputState
from smalloldgames.games.space_invaders import SpaceInvadersScene


def _make_scene(seed: int = 42) -> SpaceInvadersScene:
    return SpaceInvadersScene(lambda: None, seed=seed)


class SpaceInvadersTests(unittest.TestCase):
    def test_initial_state(self) -> None:
        scene = _make_scene()
        self.assertEqual(scene.lives, 3)
        self.assertEqual(scene.score, 0)
        self.assertEqual(scene.wave, 1)
        self.assertFalse(scene.game_over)
        alive = sum(1 for a in scene.aliens if a.alive)
        self.assertEqual(alive, 55)

    def test_player_bullet_kills_alien(self) -> None:
        scene = _make_scene()
        alien = scene.aliens[0]
        ax = scene.grid_x + alien.col * 40.0
        ay = scene.grid_y + alien.row * 34.0
        from smalloldgames.games.space_invaders_game.scene import Bullet

        scene.bullets.append(Bullet(x=ax, y=ay))
        scene._update_bullets(1.0 / 120.0)
        self.assertFalse(alien.alive)
        self.assertGreater(scene.score, 0)

    def test_bomb_kills_player(self) -> None:
        scene = _make_scene()
        from smalloldgames.games.space_invaders_game.scene import PLAYER_H, PLAYER_Y, Bomb

        scene.bombs.append(Bomb(x=scene.player_x, y=PLAYER_Y + PLAYER_H * 0.5))
        scene._update_bombs(1.0 / 120.0)
        self.assertEqual(scene.lives, 2)
        self.assertGreater(scene.player_hit_timer, 0.0)

    def test_all_aliens_dead_advances_wave(self) -> None:
        scene = _make_scene()
        for alien in scene.aliens:
            alien.alive = False
        scene._check_wave_clear()
        self.assertEqual(scene.wave, 2)
        alive = sum(1 for a in scene.aliens if a.alive)
        self.assertEqual(alive, 55)

    def test_player_cannot_move_past_edges(self) -> None:
        scene = _make_scene()
        from smalloldgames.games.space_invaders_game.scene import PLAY_LEFT, PLAYER_W

        scene.player_x = 0.0
        inputs = InputState()
        scene._update_player(1.0, inputs)
        self.assertGreaterEqual(scene.player_x, PLAY_LEFT + PLAYER_W * 0.5)

    def test_bullet_vs_shield_removes_block(self) -> None:
        scene = _make_scene()
        shield = scene.shields[0]
        initial_count = len(shield)
        from smalloldgames.games.space_invaders_game.scene import (
            SHIELD_BLOCK,
            SHIELD_POSITIONS,
            SHIELD_Y,
            Bullet,
        )

        block = next(iter(shield))
        bx = SHIELD_POSITIONS[0] + block[0] * SHIELD_BLOCK + SHIELD_BLOCK * 0.5
        by = SHIELD_Y + block[1] * SHIELD_BLOCK + SHIELD_BLOCK * 0.5
        scene.bullets.append(Bullet(x=bx, y=by))
        scene._update_bullets(1.0 / 120.0)
        self.assertEqual(len(shield), initial_count - 1)

    def test_game_over_on_zero_lives(self) -> None:
        scene = _make_scene()
        scene.lives = 1
        scene._player_killed()
        self.assertTrue(scene.game_over)
        self.assertEqual(scene.lives, 0)

    def test_aliens_step_and_reverse(self) -> None:
        scene = _make_scene()
        initial_dir = scene.grid_dir
        # Force aliens near the right edge
        from smalloldgames.games.space_invaders_game.scene import ALIEN_SPACING_X, ALIEN_W, PLAY_RIGHT

        max_col = max(a.col for a in scene.aliens if a.alive)
        scene.grid_x = PLAY_RIGHT - max_col * ALIEN_SPACING_X - ALIEN_W * 0.5
        scene._step_aliens()
        # After stepping past the edge, direction should reverse
        self.assertEqual(scene.grid_dir, -initial_dir)

    def test_score_persists_on_game_over(self) -> None:
        import os
        import tempfile

        from smalloldgames.data.storage import ScoreRepository

        db_path = os.path.join(tempfile.mkdtemp(), "test.sqlite3")
        repo = ScoreRepository(database_path=db_path)
        try:
            scene = SpaceInvadersScene(lambda: None, ctx=SceneContext(score_repository=repo), seed=42)
            scene.score = 500
            scene.lives = 1
            scene._player_killed()
            self.assertTrue(scene.game_over)
            self.assertEqual(repo.best_score("space_invaders"), 500)
        finally:
            repo.close()

    def test_ufo_awards_points_when_shot(self) -> None:
        scene = _make_scene()
        scene.ufo_active = True
        scene.ufo_x = 270.0
        from smalloldgames.games.space_invaders_game.scene import UFO_Y, Bullet

        scene.bullets.append(Bullet(x=270.0, y=UFO_Y))
        scene._update_ufo(1.0 / 120.0)
        self.assertGreater(scene.score, 0)
        self.assertFalse(scene.ufo_active)


if __name__ == "__main__":
    unittest.main()
