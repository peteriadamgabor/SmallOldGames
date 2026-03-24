from __future__ import annotations

import unittest
from unittest.mock import Mock, patch

from smalloldgames.engine.audio import (
    _MAX_ACTIVE_EFFECTS,
    AudioEngine,
    _MiniaudioBackend,
    _NullAudioBackend,
    synthesize_music_pcm,
    synthesize_pcm,
)


class _FakeBackend:
    def __init__(self) -> None:
        self.effect_calls: list[bytes] = []
        self.music_calls: list[bytes] = []
        self.stop_music_calls = 0
        self.stop_effects_calls = 0
        self.close_calls = 0

    def play_effect(self, pcm: bytes) -> bool:
        self.effect_calls.append(pcm)
        return True

    def play_music(self, pcm: bytes) -> None:
        self.music_calls.append(pcm)

    def stop_music(self) -> None:
        self.stop_music_calls += 1

    def stop_effects(self) -> None:
        self.stop_effects_calls += 1

    def close(self) -> None:
        self.close_calls += 1


class _FakePlaybackDevice:
    def __init__(self, *args, **kwargs) -> None:
        self.start = Mock()
        self.close = Mock()


class AudioTests(unittest.TestCase):
    def test_synthesized_pcm_is_not_empty(self) -> None:
        pcm = synthesize_pcm(((440.0, 0.05, 0.25), (660.0, 0.05, 0.20)))
        self.assertGreater(len(pcm), 1000)
        self.assertEqual(len(pcm) % 2, 0)

    def test_synthesized_music_pcm_is_longer_than_single_effect(self) -> None:
        music = synthesize_music_pcm(((440.0, 0.12, 0.08), (660.0, 0.12, 0.07)), loops=3)
        self.assertGreater(len(music), 10_000)
        self.assertEqual(len(music) % 2, 0)

    def test_play_uses_backend_and_caches_effect_clip(self) -> None:
        backend = _FakeBackend()
        with patch("smalloldgames.engine.audio._create_audio_backend", return_value=backend):
            engine = AudioEngine()
        self.addCleanup(engine.close)

        # Effects are pre-warmed during init, so play should use cache
        engine.play("jump")
        engine.play("jump")

        self.assertEqual(len(backend.effect_calls), 2)
        # Both calls should use the same cached clip
        self.assertEqual(backend.effect_calls[0], backend.effect_calls[1])

    def test_stop_music_delegates_to_backend_and_clears_track(self) -> None:
        backend = _FakeBackend()
        with patch("smalloldgames.engine.audio._create_audio_backend", return_value=backend):
            engine = AudioEngine()
        self.addCleanup(engine.close)
        engine._current_music = "launcher"

        engine.stop_music()

        self.assertEqual(backend.stop_music_calls, 1)
        self.assertIsNone(engine._current_music)

    def test_set_enabled_false_stops_audio_and_true_restarts_requested_track(self) -> None:
        backend = _FakeBackend()
        with patch("smalloldgames.engine.audio._create_audio_backend", return_value=backend):
            engine = AudioEngine()
        self.addCleanup(engine.close)
        engine._requested_music = "launcher"

        with patch.object(engine, "play_music") as play_music:
            engine.set_enabled(False)
            engine.set_enabled(True)

        self.assertEqual(backend.stop_music_calls, 1)
        self.assertEqual(backend.stop_effects_calls, 1)
        play_music.assert_called_once_with("launcher")

    def test_miniaudio_backend_caps_active_effects(self) -> None:
        with patch("smalloldgames.engine.audio.miniaudio.PlaybackDevice", _FakePlaybackDevice):
            backend = _MiniaudioBackend()
        self.addCleanup(backend.close)
        pcm = synthesize_pcm(((440.0, 0.02, 0.2),))

        for _ in range(_MAX_ACTIVE_EFFECTS):
            self.assertTrue(backend.play_effect(pcm))

        self.assertFalse(backend.play_effect(pcm))

    def test_miniaudio_backend_mixes_music_and_effects(self) -> None:
        with patch("smalloldgames.engine.audio.miniaudio.PlaybackDevice", _FakePlaybackDevice):
            backend = _MiniaudioBackend()
        self.addCleanup(backend.close)
        backend.play_music(synthesize_music_pcm(((220.0, 0.03, 0.05),), loops=1))
        backend.play_effect(synthesize_pcm(((660.0, 0.02, 0.18),)))

        mixed = backend._mix_frames(128)

        self.assertEqual(len(mixed), 128)
        self.assertTrue(any(sample != 0 for sample in mixed))

    def test_null_backend_is_safe_noop(self) -> None:
        backend = _NullAudioBackend()
        self.assertFalse(backend.play_effect(b"\x00\x00"))
        backend.play_music(b"\x00\x00")
        backend.stop_music()
        backend.stop_effects()
        backend.close()

    def test_close_stops_backend(self) -> None:
        backend = _FakeBackend()
        with patch("smalloldgames.engine.audio._create_audio_backend", return_value=backend):
            engine = AudioEngine()

        engine.close()

        self.assertEqual(backend.stop_music_calls, 1)
        self.assertEqual(backend.stop_effects_calls, 1)
        self.assertEqual(backend.close_calls, 1)


if __name__ == "__main__":
    unittest.main()
