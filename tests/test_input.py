from __future__ import annotations

import unittest

import glfw

from smalloldgames.engine.input import GameAction, InputState, TouchRegion


class InputStateTests(unittest.TestCase):
    def test_touch_regions_map_pointer_press_and_hold_to_actions(self) -> None:
        inputs = InputState()
        inputs.on_cursor_pos(32.0, 28.0)
        inputs.on_pointer(glfw.PRESS)
        inputs.set_touch_regions((TouchRegion(0.0, 0.0, 80.0, 60.0, frozenset({GameAction.FIRE})),))

        self.assertTrue(inputs.action_pressed(GameAction.FIRE))
        self.assertTrue(inputs.action_held(GameAction.FIRE))

        inputs.end_frame()
        inputs.set_touch_regions((TouchRegion(0.0, 0.0, 80.0, 60.0, frozenset({GameAction.FIRE})),))

        self.assertFalse(inputs.action_pressed(GameAction.FIRE))
        self.assertTrue(inputs.action_held(GameAction.FIRE))

    def test_touch_regions_clear_when_pointer_releases(self) -> None:
        inputs = InputState()
        region = TouchRegion(0.0, 0.0, 80.0, 60.0, frozenset({GameAction.MOVE_LEFT}))
        inputs.on_cursor_pos(20.0, 20.0)
        inputs.on_pointer(glfw.PRESS)
        inputs.set_touch_regions((region,))
        inputs.end_frame()

        inputs.on_pointer(glfw.RELEASE)
        inputs.set_touch_regions((region,))

        self.assertFalse(inputs.action_held(GameAction.MOVE_LEFT))


if __name__ == "__main__":
    unittest.main()
