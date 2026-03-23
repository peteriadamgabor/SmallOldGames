from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class QueueFamilies:
    graphics: int
    present: int
