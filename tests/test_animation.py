from __future__ import annotations

import unittest

from smalloldgames.assets.sprites import PackedSprite
from smalloldgames.engine.animation import Animation, AnimationSet, AnimationState


def _sprite(name: str) -> PackedSprite:
    """Create a dummy PackedSprite for testing."""
    return PackedSprite(width=16, height=16, u0=0.0, v0=0.0, u1=0.1, v1=0.1)


FRAME_A = _sprite("a")
FRAME_B = _sprite("b")
FRAME_C = _sprite("c")


class AnimationTests(unittest.TestCase):
    def test_frame_count(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B, FRAME_C), fps=10)
        self.assertEqual(anim.frame_count, 3)

    def test_duration(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B), fps=10)
        self.assertAlmostEqual(anim.duration, 0.2)

    def test_duration_zero_fps(self) -> None:
        anim = Animation(frames=(FRAME_A,), fps=0)
        self.assertAlmostEqual(anim.duration, 0.0)


class AnimationStateTests(unittest.TestCase):
    def test_starts_at_frame_zero(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B), fps=10)
        state = AnimationState(anim)
        self.assertEqual(state.frame_index, 0)
        self.assertIs(state.current_frame, FRAME_A)

    def test_advances_frame(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B, FRAME_C), fps=10)
        state = AnimationState(anim)
        state.tick(0.1)  # 1 frame at 10fps
        self.assertEqual(state.frame_index, 1)

    def test_loops(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B), fps=10, loop=True)
        state = AnimationState(anim)
        state.tick(0.2)  # 2 frames = full cycle
        self.assertEqual(state.frame_index, 0)
        self.assertFalse(state.finished)

    def test_no_loop_stops_at_last_frame(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B), fps=10, loop=False)
        state = AnimationState(anim)
        state.tick(0.5)  # Well past the end
        self.assertEqual(state.frame_index, 1)
        self.assertTrue(state.finished)

    def test_reset(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B), fps=10, loop=False)
        state = AnimationState(anim)
        state.tick(0.5)
        state.reset()
        self.assertEqual(state.frame_index, 0)
        self.assertFalse(state.finished)

    def test_set_animation(self) -> None:
        anim1 = Animation(frames=(FRAME_A, FRAME_B), fps=10)
        anim2 = Animation(frames=(FRAME_C,), fps=5)
        state = AnimationState(anim1)
        state.tick(0.1)
        state.set_animation(anim2)
        self.assertEqual(state.frame_index, 0)
        self.assertIs(state.current_frame, FRAME_C)

    def test_set_same_animation_is_noop(self) -> None:
        anim = Animation(frames=(FRAME_A, FRAME_B), fps=10)
        state = AnimationState(anim)
        state.tick(0.1)
        state.set_animation(anim)
        self.assertEqual(state.frame_index, 1)  # Not reset

    def test_finished_does_not_advance(self) -> None:
        anim = Animation(frames=(FRAME_A,), fps=10, loop=False)
        state = AnimationState(anim)
        state.tick(0.5)
        self.assertTrue(state.finished)
        state.tick(1.0)
        self.assertEqual(state.frame_index, 0)


class AnimationSetTests(unittest.TestCase):
    def test_play_and_tick(self) -> None:
        aset = AnimationSet()
        aset.add("idle", Animation(frames=(FRAME_A,), fps=1))
        aset.add("run", Animation(frames=(FRAME_B, FRAME_C), fps=10))
        aset.play("idle")
        self.assertIs(aset.current_frame, FRAME_A)
        aset.play("run")
        self.assertIs(aset.current_frame, FRAME_B)
        aset.tick(0.1)
        self.assertIs(aset.current_frame, FRAME_C)

    def test_play_same_name_is_noop(self) -> None:
        aset = AnimationSet()
        aset.add("idle", Animation(frames=(FRAME_A, FRAME_B), fps=10))
        aset.play("idle")
        aset.tick(0.1)
        aset.play("idle")  # Should NOT reset
        self.assertEqual(aset.state.frame_index, 1)

    def test_play_unknown_name(self) -> None:
        aset = AnimationSet()
        aset.play("nonexistent")
        self.assertIsNone(aset.current_frame)

    def test_tick_without_play(self) -> None:
        aset = AnimationSet()
        aset.tick(1.0)  # Should not crash


if __name__ == "__main__":
    unittest.main()
