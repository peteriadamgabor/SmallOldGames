"""Shared physics primitives for velocity, gravity, and boundaries."""

from __future__ import annotations


def integrate_velocity(
    x: float,
    y: float,
    vx: float,
    vy: float,
    dt: float,
) -> tuple[float, float]:
    """Euler integration: return ``(new_x, new_y)``."""
    return x + vx * dt, y + vy * dt


def apply_gravity(vy: float, gravity: float, dt: float) -> float:
    """Return updated vertical velocity after applying *gravity* for *dt*."""
    return vy + gravity * dt


def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to ``[lo, hi]``."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def wrap_x(x: float, world_width: float) -> float:
    """Wrap *x* with modulo so it stays in ``[0, world_width)``."""
    return x % world_width


def bounce_x(
    x: float,
    vx: float,
    width: float,
    min_x: float,
    max_x: float,
) -> tuple[float, float]:
    """Clamp position and reverse velocity on boundary contact.

    *width* is the object width; *min_x* and *max_x* are the world edges.
    Returns ``(new_x, new_vx)``.
    """
    if x <= min_x:
        return min_x, abs(vx)
    right_edge = max_x - width
    if x >= right_edge:
        return right_edge, -abs(vx)
    return x, vx
