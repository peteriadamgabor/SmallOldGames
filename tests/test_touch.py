from __future__ import annotations

import unittest

from smalloldgames.engine.input import GameAction
from smalloldgames.engine.touch import TouchButton, build_touch_regions, render_touch_buttons
from smalloldgames.rendering.primitives import DrawList


def _make_draw() -> DrawList:
    return DrawList(width=540, height=960, white_uv=(0.0, 0.0))


SAMPLE_BUTTONS = (
    TouchButton(10, 40, 100, 80, "LEFT", frozenset({GameAction.MOVE_LEFT})),
    TouchButton(430, 40, 100, 80, "RIGHT", frozenset({GameAction.MOVE_RIGHT})),
)


class BuildTouchRegionsTests(unittest.TestCase):
    def test_enabled(self) -> None:
        regions = build_touch_regions(SAMPLE_BUTTONS, enabled=True)
        self.assertEqual(len(regions), 2)
        self.assertEqual(regions[0].x, 10)
        self.assertEqual(regions[0].actions, frozenset({GameAction.MOVE_LEFT}))

    def test_disabled(self) -> None:
        regions = build_touch_regions(SAMPLE_BUTTONS, enabled=False)
        self.assertEqual(regions, ())

    def test_inactive(self) -> None:
        regions = build_touch_regions(SAMPLE_BUTTONS, enabled=True, active=False)
        self.assertEqual(regions, ())


class RenderTouchButtonsTests(unittest.TestCase):
    def test_renders_vertices(self) -> None:
        draw = _make_draw()
        render_touch_buttons(draw, SAMPLE_BUTTONS)
        self.assertGreater(len(draw.vertices), 0)


if __name__ == "__main__":
    unittest.main()
