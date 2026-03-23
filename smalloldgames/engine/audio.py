from __future__ import annotations

from array import array
from pathlib import Path
from threading import Event, Lock, Thread
import math
import shutil
import subprocess
import sys
import tempfile
import wave


_SAMPLE_RATE = 22_050

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
}


class AudioEngine:
    def __init__(self) -> None:
        self._effects_dir = Path(tempfile.mkdtemp(prefix="smalloldgames-audio-"))
        self._player = self._detect_player()
        self._winsound = self._load_winsound()
        self.enabled = True
        self._music_thread: Thread | None = None
        self._music_stop = Event()
        self._music_lock = Lock()
        self._music_process: subprocess.Popen[bytes] | None = None
        self._current_music: str | None = None
        self._requested_music: str | None = None

    def play(self, effect_name: str) -> None:
        if not self.enabled:
            return
        segments = _EFFECTS.get(effect_name)
        if segments is None:
            return
        sound_path = self._ensure_effect(effect_name, segments)
        if self._winsound is not None:
            flags = self._winsound.SND_FILENAME | self._winsound.SND_ASYNC | self._winsound.SND_NODEFAULT
            self._winsound.PlaySound(str(sound_path), flags)
            return
        if self._player is None:
            return
        command = [*self._player, str(sound_path)]
        try:
            subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except OSError:
            return

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
        music_path = self._ensure_music(track_name, segments)
        self._current_music = track_name
        if self._winsound is not None:
            flags = self._winsound.SND_FILENAME | self._winsound.SND_ASYNC | self._winsound.SND_LOOP | self._winsound.SND_NODEFAULT
            self._winsound.PlaySound(str(music_path), flags)
            return
        if self._player is None:
            return
        self._music_stop.clear()
        self._music_thread = Thread(target=self._music_loop, args=(music_path,), daemon=True)
        self._music_thread.start()

    def stop_music(self) -> None:
        self._current_music = None
        if self._winsound is not None:
            self._winsound.PlaySound(None, 0)
        self._music_stop.set()
        with self._music_lock:
            process = self._music_process
        if process is not None:
            try:
                process.terminate()
            except OSError:
                pass
        if self._music_thread is not None:
            self._music_thread.join(timeout=0.2)
            self._music_thread = None
        with self._music_lock:
            self._music_process = None
        self._music_stop.clear()

    def close(self) -> None:
        self.stop_music()
        shutil.rmtree(self._effects_dir, ignore_errors=True)

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = enabled
        if not enabled:
            self.stop_music()
        elif self._requested_music is not None:
            self.play_music(self._requested_music)

    @staticmethod
    def _load_winsound():
        if sys.platform != "win32":
            return None
        try:
            import winsound
        except ImportError:
            return None
        return winsound

    @staticmethod
    def _detect_player() -> list[str] | None:
        for command in (["paplay"], ["aplay", "-q"], ["afplay"]):
            if shutil.which(command[0]):
                return command
        return None

    def _music_loop(self, music_path: Path) -> None:
        while not self._music_stop.is_set():
            command = [*self._player, str(music_path)]
            process: subprocess.Popen[bytes] | None = None
            try:
                process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                with self._music_lock:
                    self._music_process = process
                process.wait()
            except OSError:
                break
            finally:
                with self._music_lock:
                    if self._music_process is process:
                        self._music_process = None
            if self._music_stop.wait(0.05):
                break

    def _ensure_effect(self, effect_name: str, segments: tuple[tuple[float, float, float], ...]) -> Path:
        sound_path = self._effects_dir / f"{effect_name}.wav"
        if sound_path.exists():
            return sound_path
        pcm = synthesize_pcm(segments)
        _write_wave(sound_path, pcm)
        return sound_path

    def _ensure_music(self, track_name: str, segments: tuple[tuple[float, float, float], ...]) -> Path:
        music_path = self._effects_dir / f"music_{track_name}.wav"
        if music_path.exists():
            return music_path
        pcm = synthesize_music_pcm(segments, loops=4)
        _write_wave(music_path, pcm)
        return music_path


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


def _write_wave(path: Path, pcm: bytes) -> None:
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(_SAMPLE_RATE)
        wav_file.writeframes(pcm)
