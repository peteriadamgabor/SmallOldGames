from __future__ import annotations

from typing import Protocol

from smalloldgames.rendering.primitives import DrawList

from .input import InputState


class Scene(Protocol):
    def update(self, dt: float, inputs: InputState) -> Scene | None: ...

    def render(self, draw: DrawList) -> None: ...

    def window_title(self) -> str: ...

    def music_track(self) -> str | None: ...
