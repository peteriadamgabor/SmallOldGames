"""Reusable camera with follow-target and screen shake."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(slots=True)
class Camera:
    """2-D camera that tracks a target Y position and supports screen shake."""

    y: float = 0.0
    follow_offset: float = 0.35
    viewport_height: float = 960.0

    # Shake state
    shake_intensity: float = 0.0
    shake_decay: float = 20.0
    _shake_phase: float = 0.0

    def follow_y(self, target_y: float) -> None:
        """Move camera up to keep *target_y* in view (never scrolls down)."""
        threshold = target_y - self.viewport_height * self.follow_offset
        self.y = max(self.y, threshold)

    def add_shake(self, intensity: float) -> None:
        """Add screen shake, taking the max of current and new intensity."""
        self.shake_intensity = max(self.shake_intensity, intensity)

    def tick(self, dt: float) -> None:
        """Decay shake over time."""
        self._shake_phase += dt * 36.0
        self.shake_intensity = max(0.0, self.shake_intensity - self.shake_decay * dt)

    def offset_y(self) -> float:
        """Current camera Y including shake offset."""
        if self.shake_intensity <= 0.0:
            return self.y
        return self.y + math.sin(self._shake_phase) * self.shake_intensity

    def reset(self) -> None:
        """Reset camera to origin with no shake."""
        self.y = 0.0
        self.shake_intensity = 0.0
        self._shake_phase = 0.0
