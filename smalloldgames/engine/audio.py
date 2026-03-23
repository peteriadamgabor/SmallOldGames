from __future__ import annotations

import math
from array import array
from collections.abc import Generator
from dataclasses import dataclass
from threading import Lock
from typing import Protocol

import miniaudio

_SAMPLE_RATE = 22_050
_MAX_ACTIVE_EFFECTS = 8

_EFFECTS: dict[str, tuple[tuple[float, float, float], ...]] = {
    "jump": ((720.0, 0.06, 0.35), (860.0, 0.04, 0.28)),
    "spring": ((520.0, 0.04, 0.32), (820.0, 0.05, 0.34), (1120.0, 0.08, 0.28)),
    "trampoline": ((430.0, 0.04, 0.28), (680.0, 0.05, 0.30), (980.0, 0.06, 0.28), (1320.0, 0.08, 0.26)),
    "shoot": ((930.0, 0.03, 0.22), (1180.0, 0.03, 0.18)),
    "hit": ((220.0, 0.05, 0.35), (160.0, 0.06, 0.30)),
    "ufo_hit": ((340.0, 0.04, 0.28), (520.0, 0.05, 0.26), (180.0, 0.07, 0.24)),
    "jetpack": ((450.0, 0.04, 0.22), (620.0, 0.05, 0.24), (780.0, 0.05, 0.20)),
    "propeller": ((620.0, 0.04, 0.18), (760.0, 0.04, 0.18), (920.0, 0.05, 0.20)),
    "shield": ((780.0, 0.05, 0.26), (1040.0, 0.06, 0.20), (1240.0, 0.05, 0.16)),
    "rocket": ((260.0, 0.05, 0.18), (460.0, 0.06, 0.22), (760.0, 0.07, 0.26), (1120.0, 0.08, 0.24)),
    "boots": ((540.0, 0.03, 0.18), (740.0, 0.03, 0.20), (980.0, 0.04, 0.18)),
    "enemy_shot": ((240.0, 0.04, 0.18), (180.0, 0.05, 0.16)),
    "break": ((180.0, 0.03, 0.24), (140.0, 0.04, 0.20), (110.0, 0.05, 0.18)),
    "game_over": ((420.0, 0.08, 0.30), (260.0, 0.12, 0.28), (180.0, 0.14, 0.24)),
}

_MUSIC_TRACKS: dict[str, tuple[tuple[float, float, float], ...]] = {
    "launcher": (
        (392.0, 0.18, 0.07),
        (523.25, 0.18, 0.06),
        (659.25, 0.22, 0.06),
        (523.25, 0.18, 0.05),
        (440.0, 0.18, 0.06),
        (523.25, 0.18, 0.05),
        (587.33, 0.22, 0.06),
        (523.25, 0.18, 0.05),
    ),
    "sketch_hopper": (
        (523.25, 0.15, 0.06),
        (659.25, 0.15, 0.06),
        (783.99, 0.18, 0.06),
        (659.25, 0.15, 0.05),
        (587.33, 0.15, 0.06),
        (659.25, 0.15, 0.05),
        (698.46, 0.18, 0.06),
        (783.99, 0.21, 0.05),
        (659.25, 0.15, 0.06),
        (587.33, 0.15, 0.05),
        (523.25, 0.18, 0.06),
        (659.25, 0.18, 0.05),
    ),
    "space_invaders": (
        (110.0, 0.28, 0.08),
        (90.0, 0.28, 0.08),
        (82.0, 0.28, 0.07),
        (75.0, 0.28, 0.07),
        (110.0, 0.28, 0.06),
        (130.0, 0.28, 0.07),
        (110.0, 0.28, 0.06),
        (90.0, 0.32, 0.07),
    ),
}


class AudioBackend(Protocol):
    def play_effect(self, pcm: bytes) -> bool: ...

    def play_music(self, pcm: bytes) -> None: ...

    def stop_music(self) -> None: ...

    def stop_effects(self) -> None: ...

    def close(self) -> None: ...


@dataclass(slots=True)
class _Voice:
    samples: array
    cursor: int = 0
    loop: bool = False


class _NullAudioBackend:
    def play_effect(self, pcm: bytes) -> bool:
        return False

    def play_music(self, pcm: bytes) -> None:
        return None

    def stop_music(self) -> None:
        return None

    def stop_effects(self) -> None:
        return None

    def close(self) -> None:
        return None


class _MiniaudioBackend:
    def __init__(self) -> None:
        self._lock = Lock()
        self._closed = False
        self._effects: list[_Voice] = []
        self._music: _Voice | None = None
        self._device = miniaudio.PlaybackDevice(
            output_format=miniaudio.SampleFormat.SIGNED16,
            nchannels=1,
            sample_rate=_SAMPLE_RATE,
            buffersize_msec=70,
            app_name="SmallOldGames",
        )
        self._stream = self._stream_generator()
        next(self._stream)
        self._device.start(self._stream)

    def play_effect(self, pcm: bytes) -> bool:
        voice = _voice_from_pcm(pcm)
        with self._lock:
            self._effects = [effect for effect in self._effects if effect.cursor < len(effect.samples)]
            if len(self._effects) >= _MAX_ACTIVE_EFFECTS:
                return False
            self._effects.append(voice)
        return True

    def play_music(self, pcm: bytes) -> None:
        with self._lock:
            self._music = _voice_from_pcm(pcm, loop=True)

    def stop_music(self) -> None:
        with self._lock:
            self._music = None

    def stop_effects(self) -> None:
        with self._lock:
            self._effects.clear()

    def close(self) -> None:
        with self._lock:
            self._closed = True
            self._music = None
            self._effects.clear()
        self._device.close()

    def _stream_generator(self) -> Generator[bytes | array, int]:
        frame_count = yield b""
        while True:
            frame_count = yield self._mix_frames(frame_count)

    def _mix_frames(self, frame_count: int) -> array:
        if frame_count <= 0:
            return array("h")
        mixed = array("i", [0]) * frame_count
        with self._lock:
            if self._closed:
                return array("h", [0]) * frame_count
            music = self._music
            effects = list(self._effects)
        if music is not None:
            self._mix_voice(mixed, music)
        remaining_effects: list[_Voice] = []
        for effect in effects:
            if self._mix_voice(mixed, effect):
                remaining_effects.append(effect)
        with self._lock:
            self._effects = remaining_effects
            if music is not None and not music.loop and music.cursor >= len(music.samples):
                self._music = None
        return array("h", (_clamp_sample(sample) for sample in mixed))

    @staticmethod
    def _mix_voice(mixed: array, voice: _Voice) -> bool:
        total_samples = len(voice.samples)
        for index in range(len(mixed)):
            if voice.cursor >= total_samples:
                if not voice.loop:
                    return False
                voice.cursor = 0
            mixed[index] += voice.samples[voice.cursor]
            voice.cursor += 1
        return True


class AudioEngine:
    def __init__(self) -> None:
        self.enabled = True
        self._backend = _create_audio_backend()
        self._current_music: str | None = None
        self._requested_music: str | None = None
        self._effect_cache: dict[str, bytes] = {}
        self._music_cache: dict[str, bytes] = {}

    def play(self, effect_name: str) -> None:
        if not self.enabled:
            return
        segments = _EFFECTS.get(effect_name)
        if segments is None:
            return
        self._backend.play_effect(self._effect_clip(effect_name, segments))

    def play_music(self, track_name: str | None) -> None:
        self._requested_music = track_name
        if track_name == self._current_music:
            return
        self.stop_music()
        if not self.enabled or track_name is None:
            return
        segments = _MUSIC_TRACKS.get(track_name)
        if segments is None:
            return
        self._backend.play_music(self._music_clip(track_name, segments))
        self._current_music = track_name

    def stop_music(self) -> None:
        self._backend.stop_music()
        self._current_music = None

    def close(self) -> None:
        self.stop_music()
        self._backend.stop_effects()
        self._backend.close()

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.stop_music()
            self._backend.stop_effects()
        elif self._requested_music is not None:
            self.play_music(self._requested_music)

    def _effect_clip(self, effect_name: str, segments: tuple[tuple[float, float, float], ...]) -> bytes:
        clip = self._effect_cache.get(effect_name)
        if clip is None:
            clip = synthesize_pcm(segments)
            self._effect_cache[effect_name] = clip
        return clip

    def _music_clip(self, track_name: str, segments: tuple[tuple[float, float, float], ...]) -> bytes:
        clip = self._music_cache.get(track_name)
        if clip is None:
            clip = synthesize_music_pcm(segments, loops=1)
            self._music_cache[track_name] = clip
        return clip


def _create_audio_backend() -> AudioBackend:
    try:
        return _MiniaudioBackend()
    except Exception:
        return _NullAudioBackend()


def synthesize_pcm(segments: tuple[tuple[float, float, float], ...]) -> bytes:
    samples = array("h")
    for frequency, duration, volume in segments:
        count = max(1, int(_SAMPLE_RATE * duration))
        fade = max(1, min(count // 6, 160))
        for index in range(count):
            envelope = 1.0
            if index < fade:
                envelope = index / fade
            elif index >= count - fade:
                envelope = (count - index - 1) / fade
            value = math.sin((index / _SAMPLE_RATE) * math.tau * frequency)
            samples.append(int(max(-1.0, min(1.0, value * volume * envelope)) * 32767))
        samples.extend((0,) * max(1, int(_SAMPLE_RATE * 0.008)))
    return samples.tobytes()


def synthesize_music_pcm(
    segments: tuple[tuple[float, float, float], ...],
    *,
    loops: int = 2,
) -> bytes:
    samples = array("h")
    for loop_index in range(max(1, loops)):
        phase_offset = loop_index * 0.35
        for note_index, (frequency, duration, volume) in enumerate(segments):
            count = max(1, int(_SAMPLE_RATE * duration))
            fade = max(1, min(count // 5, 260))
            harmony = frequency * (2.0 if note_index % 4 == 0 else 1.5)
            for index in range(count):
                envelope = 1.0
                if index < fade:
                    envelope = index / fade
                elif index >= count - fade:
                    envelope = (count - index - 1) / fade
                t = index / _SAMPLE_RATE
                lead = math.sin((t + phase_offset) * math.tau * frequency)
                pad = math.sin((t + phase_offset * 0.7) * math.tau * harmony) * 0.35
                bass = math.sin((t + phase_offset * 0.4) * math.tau * max(80.0, frequency * 0.5)) * 0.25
                value = (lead + pad + bass) * volume * envelope
                samples.append(int(max(-1.0, min(1.0, value)) * 32767))
            samples.extend((0,) * max(1, int(_SAMPLE_RATE * 0.018)))
    return samples.tobytes()


def _voice_from_pcm(pcm: bytes, *, loop: bool = False) -> _Voice:
    samples = array("h")
    samples.frombytes(pcm)
    return _Voice(samples=samples, loop=loop)


def _clamp_sample(value: int) -> int:
    return max(-32768, min(32767, value))
