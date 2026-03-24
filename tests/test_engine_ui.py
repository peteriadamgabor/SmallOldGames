from __future__ import annotations

import unittest

from smalloldgames.engine.ui import draw_fullscreen_scrim, draw_overlay_panel, draw_score_hud
from smalloldgames.rendering.primitives import DrawList


def _make_draw() -> DrawList:
    return DrawList(width=540, height=960, white_uv=(0.0, 0.0))


class FullscreenScrimTests(unittest.TestCase):
    def test_emits_vertices(self) -> None:
        draw = _make_draw()
        draw_fullscreen_scrim(draw)
        self.assertGreater(len(draw.vertices), 0)


class OverlayPanelTests(unittest.TestCase):
    def test_renders_title(self) -> None:
        draw = _make_draw()
        draw_overlay_panel(draw, title="PAUSED")
        self.assertGreater(len(draw.vertices), 0)

    def test_no_scrim_option(self) -> None:
        draw_with = _make_draw()
        draw_overlay_panel(draw_with, title="A", scrim=True)
        draw_without = _make_draw()
        draw_overlay_panel(draw_without, title="A", scrim=False)
        # With scrim should have more vertices (the scrim quad)
        self.assertGreater(len(draw_with.vertices), len(draw_without.vertices))

    def test_with_subtitle_and_score(self) -> None:
        draw = _make_draw()
        draw_overlay_panel(
            draw,
            title="GAME OVER",
            subtitle="TAP TO RESTART",
            score_line="SCORE 01234",
        )
        self.assertGreater(len(draw.vertices), 0)


class ScoreHudTests(unittest.TestCase):
    def test_renders_score_and_best(self) -> None:
        draw = _make_draw()
        draw_score_hud(draw, title="SNAKE", score=100, best_score=500)
        self.assertGreater(len(draw.vertices), 0)

    def test_with_extra_text(self) -> None:
        draw_base = _make_draw()
        draw_score_hud(draw_base, title="X", score=0, best_score=0)
        draw_extra = _make_draw()
        draw_score_hud(draw_extra, title="X", score=0, best_score=0, extra_text="WAVE 3", extra_y=800.0)
        self.assertGreater(len(draw_extra.vertices), len(draw_base.vertices))


if __name__ == "__main__":
    unittest.main()
