from __future__ import annotations

import unittest

from smalloldgames.engine.debug_overlay import DebugOverlay, FrameProfile


class _FakeDrawList:
    def __init__(self) -> None:
        self.quad_calls = 0
        self.text_values: list[str] = []

    def quad(self, *_args, **_kwargs) -> None:
        self.quad_calls += 1

    def text(self, _x: float, _y: float, value: str, *, scale: float, color, centered: bool = False, world: bool = False) -> None:
        self.text_values.append(value)


class DebugOverlayTests(unittest.TestCase):
    def test_record_frame_keeps_latest_profile(self) -> None:
        overlay = DebugOverlay(history_size=3)

        overlay.record_frame(FrameProfile(frame_ms=10.0, scene_name="One"))
        overlay.record_frame(FrameProfile(frame_ms=12.0, scene_name="Two"))

        self.assertEqual(overlay.profile.scene_name, "Two")
        self.assertEqual(list(overlay._frame_history), [10.0, 12.0])

    def test_render_draws_profile_panel_with_graph(self) -> None:
        overlay = DebugOverlay(history_size=4)
        for frame_ms in (8.4, 9.1, 12.0):
            overlay.record_frame(
                FrameProfile(
                    fps=118.0,
                    frame_ms=frame_ms,
                    update_ms=1.2,
                    render_ms=0.7,
                    submit_ms=0.5,
                    idle_ms=6.0,
                    fixed_updates=1,
                    vertex_count=432,
                    scene_name="Launcher",
                    scene_stack_depth=0,
                )
            )
        draw = _FakeDrawList()

        overlay.render(draw)

        self.assertGreaterEqual(draw.quad_calls, 4)
        self.assertTrue(any("FPS 118" in value for value in draw.text_values))
        self.assertTrue(any("UPD 1.2  REN 0.7  GPU 0.5" == value for value in draw.text_values))
        self.assertTrue(any("LAUNCHER" in value for value in draw.text_values))


if __name__ == "__main__":
    unittest.main()
