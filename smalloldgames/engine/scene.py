from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from smalloldgames.rendering.primitives import DrawList

from .input import InputState

if TYPE_CHECKING:
    from smalloldgames.data.storage import ScoreRepository

    from .audio import AudioEngine


@dataclass(frozen=True, slots=True)
class Transition:
    """Replace the current scene with a new one."""

    scene: Scene


@dataclass(frozen=True, slots=True)
class Push:
    """Push a new scene onto the stack (current scene is paused beneath)."""

    scene: Scene


@dataclass(frozen=True, slots=True)
class Pop:
    """Pop the current scene off the stack, returning to the one beneath."""


SceneResult = Transition | Push | Pop | None


@dataclass(slots=True)
class SceneContext:
    """Shared dependencies available to all scenes."""

    score_repository: ScoreRepository | None = None
    audio: AudioEngine | None = None


class Scene(Protocol):
    def update(self, dt: float, inputs: InputState) -> SceneResult: ...

    def render(self, draw: DrawList) -> None: ...

    def window_title(self) -> str: ...

    def music_track(self) -> str | None: ...

    def on_enter(self) -> None: ...

    def on_exit(self) -> None: ...
