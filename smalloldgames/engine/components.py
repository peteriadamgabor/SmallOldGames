from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Position:
    x: float
    y: float


@dataclass(slots=True)
class Velocity:
    vx: float = 0.0
    vy: float = 0.0


@dataclass(slots=True)
class Lifetime:
    remaining: float


@dataclass(slots=True)
class Size:
    width: float
    height: float
