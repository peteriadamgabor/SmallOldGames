from __future__ import annotations

import unittest

import glfw

from smalloldgames.engine import GameDefinition, Transition
from smalloldgames.engine.input import InputState
from smalloldgames.menus.home import LauncherScene


class LauncherMenuTests(unittest.TestCase):
    def test_horizontal_and_vertical_navigation_follow_dashboard_layout(self) -> None:
        scene = LauncherScene(self._games(), self._open_leaderboard, self._open_settings)

        inputs = InputState()
        inputs.on_key(glfw.KEY_RIGHT, glfw.PRESS)
        scene.update(0.0, inputs)
        self.assertEqual(scene.selection, 1)

        inputs = InputState()
        inputs.on_key(glfw.KEY_DOWN, glfw.PRESS)
        scene.update(0.0, inputs)
        self.assertEqual(scene.selection, 3)

        inputs = InputState()
        inputs.on_key(glfw.KEY_RIGHT, glfw.PRESS)
        scene.update(0.0, inputs)
        self.assertEqual(scene.selection, 4)

        inputs = InputState()
        inputs.on_key(glfw.KEY_UP, glfw.PRESS)
        scene.update(0.0, inputs)
        self.assertEqual(scene.selection, 2)

    def test_leaderboard_uses_last_selected_game_context(self) -> None:
        scene = LauncherScene(self._games(), self._open_leaderboard, self._open_settings)
        scene.selection = 2
        scene.active_game_selection = 2

        inputs = InputState()
        inputs.on_key(glfw.KEY_TAB, glfw.PRESS)
        result = scene.update(0.0, inputs)

        self.assertEqual(scene.selection, 3)
        self.assertEqual(result, Transition(("leaderboard", "space_invaders")))

    @staticmethod
    def _open_leaderboard(game):
        return ("leaderboard", game.id)

    @staticmethod
    def _open_settings():
        return "settings"

    @staticmethod
    def _games() -> tuple[GameDefinition, ...]:
        return (
            GameDefinition(
                id="sketch_hopper",
                title="SKETCH HOPPER",
                subtitle="ENDLESS JUMPER",
                detail="PRESS ENTER OR SPACE",
                score_key="sketch_hopper",
                art_variant="hopper",
                music_track="sketch_hopper",
                make_scene=lambda: None,
            ),
            GameDefinition(
                id="snake",
                title="SNAKE CLASSIC",
                subtitle="RETRO GRID JUGGERNAUT",
                detail="PRESS ENTER OR SPACE",
                score_key="snake",
                art_variant="snake",
                music_track="snake",
                make_scene=lambda: None,
            ),
            GameDefinition(
                id="space_invaders",
                title="SPACE INVADERS",
                subtitle="ALIEN ONSLAUGHT",
                detail="PRESS ENTER OR SPACE",
                score_key="space_invaders",
                art_variant="space_invaders",
                music_track="space_invaders",
                make_scene=lambda: None,
            ),
        )


if __name__ == "__main__":
    unittest.main()
