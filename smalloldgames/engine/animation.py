"""Frame-based sprite animation system."""

from __future__ import annotations

from dataclasses import dataclass, field

from smalloldgames.assets.sprites import PackedSprite


@dataclass(frozen=True, slots=True)
class Animation:
    """A sequence of sprite frames played at a fixed rate.

    *frames* is a tuple of :class:`PackedSprite` (one per frame).
    *fps* controls playback speed.  When *loop* is ``False`` the
    animation stops on the last frame.
    """

    frames: tuple[PackedSprite, ...]
    fps: float = 8.0
    loop: bool = True

    @property
    def frame_count(self) -> int:
        return len(self.frames)

    @property
    def duration(self) -> float:
        """Total duration of one cycle in seconds."""
        if self.fps <= 0.0:
            return 0.0
        return len(self.frames) / self.fps


@dataclass(slots=True)
class AnimationState:
    """Mutable playback state for an :class:`Animation`."""

    animation: Animation
    timer: float = 0.0
    _frame_index: int = 0
    finished: bool = False

    @property
    def frame_index(self) -> int:
        return self._frame_index

    @property
    def current_frame(self) -> PackedSprite:
        """The sprite for the current frame."""
        return self.animation.frames[self._frame_index]

    def tick(self, dt: float) -> None:
        """Advance the animation by *dt* seconds."""
        if self.finished or not self.animation.frames:
            return
        self.timer += dt
        frame_duration = 1.0 / self.animation.fps if self.animation.fps > 0.0 else 0.0
        if frame_duration <= 0.0:
            return
        while self.timer >= frame_duration:
            self.timer -= frame_duration
            self._frame_index += 1
            if self._frame_index >= self.animation.frame_count:
                if self.animation.loop:
                    self._frame_index = 0
                else:
                    self._frame_index = self.animation.frame_count - 1
                    self.finished = True
                    return

    def reset(self) -> None:
        """Restart the animation from the first frame."""
        self.timer = 0.0
        self._frame_index = 0
        self.finished = False

    def set_animation(self, animation: Animation) -> None:
        """Switch to a different animation, resetting playback."""
        if animation is self.animation:
            return
        self.animation = animation
        self.reset()


@dataclass(slots=True)
class AnimationSet:
    """Named collection of animations with a current state.

    Typical usage: create with idle/run/jump animations, then call
    ``play("run")`` to switch states.
    """

    animations: dict[str, Animation] = field(default_factory=dict)
    state: AnimationState | None = None
    current_name: str = ""

    def add(self, name: str, animation: Animation) -> None:
        self.animations[name] = animation

    def play(self, name: str) -> None:
        """Switch to the named animation. No-op if already playing it."""
        if name == self.current_name and self.state is not None:
            return
        animation = self.animations.get(name)
        if animation is None:
            return
        self.current_name = name
        if self.state is None:
            self.state = AnimationState(animation)
        else:
            self.state.set_animation(animation)

    def tick(self, dt: float) -> None:
        if self.state is not None:
            self.state.tick(dt)

    @property
    def current_frame(self) -> PackedSprite | None:
        if self.state is None:
            return None
        return self.state.current_frame
