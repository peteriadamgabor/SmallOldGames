from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from smalloldgames.engine.audio import AudioEngine, _MAX_ACTIVE_EFFECTS, synthesize_music_pcm, synthesize_pcm


class _FakeProcess:
    def __init__(self, *, alive: bool = True) -> None:
        self.alive = alive
        self.terminate = Mock(side_effect=self._terminate)
        self.wait = Mock()

    def _terminate(self) -> None:
        self.alive = False

    def poll(self):
        return None if self.alive else 0


class AudioTests(unittest.TestCase):
    def test_synthesized_pcm_is_not_empty(self) -> None:
        pcm = synthesize_pcm(((440.0, 0.05, 0.25), (660.0, 0.05, 0.20)))
        self.assertGreater(len(pcm), 1000)
        self.assertEqual(len(pcm) % 2, 0)

    def test_synthesized_music_pcm_is_longer_than_single_effect(self) -> None:
        music = synthesize_music_pcm(((440.0, 0.12, 0.08), (660.0, 0.12, 0.07)), loops=3)
        self.assertGreater(len(music), 10_000)
        self.assertEqual(len(music) % 2, 0)

    def test_play_respects_max_active_effects_cap(self) -> None:
        engine = AudioEngine()
        self.addCleanup(engine.close)
        engine._winsound = None
        engine._player = ["fake-player"]
        engine._active_effects = [_FakeProcess() for _ in range(_MAX_ACTIVE_EFFECTS)]

        with (
            patch.object(engine, "_ensure_effect", return_value=Path("/tmp/effect.wav")),
            patch("smalloldgames.engine.audio.subprocess.Popen") as popen,
        ):
            engine.play("jump")

        popen.assert_not_called()

    def test_stop_music_terminates_process_and_joins_thread(self) -> None:
        engine = AudioEngine()
        self.addCleanup(engine.close)
        process = _FakeProcess()
        thread = Mock()
        engine._music_process = process
        engine._music_thread = thread
        engine._current_music = "launcher"

        engine.stop_music()

        process.terminate.assert_called_once()
        thread.join.assert_called_once()
        self.assertIsNone(engine._music_process)
        self.assertIsNone(engine._music_thread)
        self.assertIsNone(engine._current_music)
        self.assertFalse(engine._music_stop.is_set())

    def test_set_enabled_false_stops_audio_and_true_restarts_requested_track(self) -> None:
        engine = AudioEngine()
        self.addCleanup(engine.close)
        engine._requested_music = "launcher"

        with (
            patch.object(engine, "stop_music") as stop_music,
            patch.object(engine, "_stop_effects") as stop_effects,
            patch.object(engine, "play_music") as play_music,
        ):
            engine.set_enabled(False)
            engine.set_enabled(True)

        stop_music.assert_called_once()
        stop_effects.assert_called_once()
        play_music.assert_called_once_with("launcher")


if __name__ == "__main__":
    unittest.main()
