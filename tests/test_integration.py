from __future__ import annotations

import tempfile
import unittest

import glfw

from smalloldgames.data.storage import ScoreRepository
from smalloldgames.engine import GameRegistry, InputState, SceneContext
from smalloldgames.engine.scene import Transition
from smalloldgames.games import DEFAULT_GAME_MODULES
from smalloldgames.games.snake import SnakeScene
from smalloldgames.menus.home import LauncherScene
from smalloldgames.menus.leaderboard import LeaderboardScene
from smalloldgames.menus.settings import SettingsScene


class _FakeAudio:
    def __init__(self) -> None:
        self.enabled = True
        self.set_enabled_calls: list[bool] = []
        self.play_calls: list[str] = []
        self.music_calls: list[str | None] = []

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        self.set_enabled_calls.append(enabled)

    def play(self, effect_name: str) -> None:
        self.play_calls.append(effect_name)

    def play_music(self, track_name: str | None) -> None:
        self.music_calls.append(track_name)


class IntegrationFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.repository = ScoreRepository(f"{self.tempdir.name}/scores.sqlite3")
        self.addCleanup(self.repository.close)
        self.audio = _FakeAudio()
        self.ctx = SceneContext(score_repository=self.repository, audio=self.audio)

        def make_launcher() -> LauncherScene:
            return LauncherScene(self.games.all(), make_leaderboard, make_settings, ctx=self.ctx)

        def make_leaderboard(game=None) -> LeaderboardScene:
            return LeaderboardScene(make_launcher, self.games.all(), game or self.games.primary(), ctx=self.ctx)

        def make_settings() -> SettingsScene:
            return SettingsScene(make_launcher, ctx=self.ctx, on_sound_changed=self.audio.set_enabled)

        self.games = GameRegistry.from_modules(DEFAULT_GAME_MODULES, ctx=self.ctx, on_exit=make_launcher)
        self.make_launcher = make_launcher
        self.make_leaderboard = make_leaderboard
        self.make_settings = make_settings

    def _pointer_click(self, rect: tuple[float, float, float, float]) -> InputState:
        inputs = InputState()
        x, y, width, height = rect
        inputs.on_cursor_pos(x + width * 0.5, y + height * 0.5)
        inputs.pointer_pressed = True
        return inputs

    def test_launcher_settings_flow_persists_sound_toggle(self) -> None:
        launcher = self.make_launcher()
        result = launcher.update(0.0, self._pointer_click(launcher._settings_card_rect()))

        self.assertIsInstance(result, Transition)
        settings = result.scene
        self.assertIsInstance(settings, SettingsScene)

        toggle = InputState()
        toggle.actions_pressed.add(glfw.KEY_S)  # intentionally ignored at action layer
        toggle.actions_pressed.add(32)  # ignored noise
        toggle.actions_pressed.clear()
        toggle.actions_pressed.add(32)  # no-op noise
        toggle.actions_pressed.clear()
        toggle.actions_pressed.add(33)  # no-op noise
        toggle.actions_pressed.clear()
        from smalloldgames.engine import GameAction

        toggle.actions_pressed.add(GameAction.SOUND_TOGGLE)
        self.assertIsNone(settings.update(0.0, toggle))
        self.assertFalse(self.repository.get_sound_enabled())
        self.assertEqual(self.audio.set_enabled_calls[-1], False)

        back = InputState()
        back.actions_pressed.add(GameAction.BACK)
        result = settings.update(0.0, back)

        self.assertIsInstance(result, Transition)
        launcher_again = result.scene
        self.assertIsInstance(launcher_again, LauncherScene)
        self.assertFalse(launcher_again.sound_enabled)

    def test_leaderboard_name_edit_play_and_score_persist_across_launcher(self) -> None:
        launcher = self.make_launcher()
        result = launcher.update(0.0, self._pointer_click(launcher._leaderboard_card_rect()))

        self.assertIsInstance(result, Transition)
        board = result.scene
        self.assertIsInstance(board, LeaderboardScene)

        from smalloldgames.engine import GameAction

        edit = InputState()
        edit.actions_pressed.add(GameAction.EDIT_NAME)
        self.assertIsNone(board.update(0.0, edit))
        self.assertTrue(board.editing_name)

        typing = InputState()
        typing.on_key(glfw.KEY_Z, glfw.PRESS)
        typing.on_key(glfw.KEY_1, glfw.PRESS)
        self.assertIsNone(board.update(0.0, typing))
        self.assertEqual(board.draft_name, "PLAYER1Z")

        save = InputState()
        save.on_key(glfw.KEY_ENTER, glfw.PRESS)
        self.assertIsNone(board.update(0.0, save))
        self.assertFalse(board.editing_name)
        self.assertEqual(self.repository.get_player_name(), "PLAYER1Z")

        select_snake = InputState()
        select_snake.actions_pressed.add(GameAction.NAV_RIGHT)
        self.assertIsNone(board.update(0.0, select_snake))

        play = InputState()
        play.actions_pressed.add(GameAction.CONFIRM)
        result = board.update(0.0, play)

        self.assertIsInstance(result, Transition)
        game = result.scene
        self.assertIsInstance(game, SnakeScene)

        game.score = 40
        game._trigger_game_over()
        self.assertEqual(self.repository.best_score("snake"), 40)

        launcher_again = self.make_launcher()
        self.assertEqual(launcher_again.player_name, "PLAYER1Z")
        self.assertEqual(launcher_again.stats_by_game["snake"].best_score, 40)


if __name__ == "__main__":
    unittest.main()
