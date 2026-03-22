from __future__ import annotations

import unittest

from smalloldgames.engine.audio import synthesize_music_pcm, synthesize_pcm


class AudioTests(unittest.TestCase):
    def test_synthesized_pcm_is_not_empty(self) -> None:
        pcm = synthesize_pcm(((440.0, 0.05, 0.25), (660.0, 0.05, 0.20)))
        self.assertGreater(len(pcm), 1000)
        self.assertEqual(len(pcm) % 2, 0)

    def test_synthesized_music_pcm_is_longer_than_single_effect(self) -> None:
        music = synthesize_music_pcm(((440.0, 0.12, 0.08), (660.0, 0.12, 0.07)), loops=3)
        self.assertGreater(len(music), 10_000)
        self.assertEqual(len(music) % 2, 0)


if __name__ == "__main__":
    unittest.main()
