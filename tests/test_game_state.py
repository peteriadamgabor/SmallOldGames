from __future__ import annotations

import unittest

import glfw

from smalloldgames.engine.game_state import FLOW_CONTINUE, GameFlowMixin
from smalloldgames.engine.input import InputState
from smalloldgames.engine.scene import Transition


class FakeScene(GameFlowMixin):
    def __init__(self):
        self.paused = False
        self.game_over = False
        self.exit_scene_factory = lambda: "exit_scene"
        self._reset_count = 0

    def reset(self):
        self._reset_count += 1
        self.game_over = False
        self.paused = False


class GameFlowTests(unittest.TestCase):
    def test_back_returns_transition(self) -> None:
        scene = FakeScene()
        inputs = InputState()
        inputs.on_key(glfw.KEY_ESCAPE, glfw.PRESS)
        result = scene._handle_game_flow(inputs)
        self.assertIsInstance(result, Transition)

    def test_pause_toggles(self) -> None:
        scene = FakeScene()
        inputs = InputState()
        inputs.on_key(glfw.KEY_P, glfw.PRESS)
        result = scene._handle_game_flow(inputs)
        self.assertIsNone(result)
        self.assertTrue(scene.paused)

    def test_restart_resets(self) -> None:
        scene = FakeScene()
        inputs = InputState()
        inputs.on_key(glfw.KEY_R, glfw.PRESS)
        result = scene._handle_game_flow(inputs)
        self.assertIsNone(result)
        self.assertEqual(scene._reset_count, 1)

    def test_game_over_confirm_resets(self) -> None:
        scene = FakeScene()
        scene.game_over = True
        inputs = InputState()
        inputs.on_key(glfw.KEY_ENTER, glfw.PRESS)
        result = scene._handle_game_flow(inputs)
        self.assertIsNone(result)
        self.assertEqual(scene._reset_count, 1)

    def test_paused_confirm_resumes(self) -> None:
        scene = FakeScene()
        scene.paused = True
        inputs = InputState()
        inputs.on_key(glfw.KEY_ENTER, glfw.PRESS)
        result = scene._handle_game_flow(inputs)
        self.assertIsNone(result)
        self.assertFalse(scene.paused)

    def test_normal_returns_sentinel(self) -> None:
        scene = FakeScene()
        inputs = InputState()
        result = scene._handle_game_flow(inputs)
        self.assertIs(result, FLOW_CONTINUE)

    def test_pause_not_allowed_during_game_over(self) -> None:
        scene = FakeScene()
        scene.game_over = True
        inputs = InputState()
        inputs.on_key(glfw.KEY_P, glfw.PRESS)
        scene._handle_game_flow(inputs)
        # Should go through game_over handler, not pause toggle
        self.assertFalse(scene.paused)


if __name__ == "__main__":
    unittest.main()
