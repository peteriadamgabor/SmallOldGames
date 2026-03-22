from __future__ import annotations

import unittest

from smalloldgames.engine.app import WINDOW_HEIGHT, WINDOW_WIDTH, _content_rect


class AppLayoutTests(unittest.TestCase):
    def test_content_rect_letterboxes_wider_window(self) -> None:
        x, y, width, height = _content_rect(1200, 960)
        self.assertEqual(height, 960.0)
        self.assertEqual(width, WINDOW_WIDTH * (960 / WINDOW_HEIGHT))
        self.assertGreater(x, 0.0)
        self.assertEqual(y, 0.0)

    def test_content_rect_letterboxes_taller_window(self) -> None:
        x, y, width, height = _content_rect(540, 1400)
        self.assertEqual(width, 540.0)
        self.assertEqual(height, WINDOW_HEIGHT * (540 / WINDOW_WIDTH))
        self.assertEqual(x, 0.0)
        self.assertGreater(y, 0.0)


if __name__ == "__main__":
    unittest.main()
