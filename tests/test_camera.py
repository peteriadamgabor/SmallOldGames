from __future__ import annotations

import unittest

from smalloldgames.engine.camera import Camera


class CameraTests(unittest.TestCase):
    def test_follow_y_moves_up(self) -> None:
        cam = Camera(follow_offset=0.35, viewport_height=960.0)
        cam.follow_y(500.0)
        self.assertGreater(cam.y, 0.0)

    def test_follow_y_does_not_scroll_down(self) -> None:
        cam = Camera()
        cam.y = 200.0
        cam.follow_y(100.0)
        self.assertEqual(cam.y, 200.0)

    def test_offset_y_without_shake(self) -> None:
        cam = Camera()
        cam.y = 100.0
        self.assertEqual(cam.offset_y(), 100.0)

    def test_offset_y_with_shake(self) -> None:
        cam = Camera()
        cam.y = 100.0
        cam.add_shake(10.0)
        cam._shake_phase = 1.0  # Non-zero phase to get non-zero sin
        offset = cam.offset_y()
        self.assertNotEqual(offset, 100.0)

    def test_shake_decays_over_time(self) -> None:
        cam = Camera(shake_decay=20.0)
        cam.add_shake(10.0)
        cam.tick(0.25)
        self.assertAlmostEqual(cam.shake_intensity, 5.0)

    def test_shake_does_not_go_negative(self) -> None:
        cam = Camera(shake_decay=100.0)
        cam.add_shake(1.0)
        cam.tick(1.0)
        self.assertEqual(cam.shake_intensity, 0.0)

    def test_add_shake_takes_max(self) -> None:
        cam = Camera()
        cam.add_shake(5.0)
        cam.add_shake(3.0)
        self.assertEqual(cam.shake_intensity, 5.0)
        cam.add_shake(8.0)
        self.assertEqual(cam.shake_intensity, 8.0)

    def test_reset(self) -> None:
        cam = Camera()
        cam.y = 500.0
        cam.add_shake(10.0)
        cam._shake_phase = 5.0
        cam.reset()
        self.assertEqual(cam.y, 0.0)
        self.assertEqual(cam.shake_intensity, 0.0)
        self.assertEqual(cam._shake_phase, 0.0)


if __name__ == "__main__":
    unittest.main()
