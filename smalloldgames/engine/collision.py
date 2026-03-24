"""Shared collision detection primitives."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AABB:
    """Axis-aligned bounding box."""

    x: float
    y: float
    width: float
    height: float


def aabb_overlaps(a: AABB, b: AABB) -> bool:
    """Test if two axis-aligned bounding boxes overlap."""
    return a.x < b.x + b.width and a.x + a.width > b.x and a.y < b.y + b.height and a.y + a.height > b.y


def aabb_overlaps_raw(
    ax: float,
    ay: float,
    aw: float,
    ah: float,
    bx: float,
    by: float,
    bw: float,
    bh: float,
) -> bool:
    """Raw float AABB overlap test — avoids object allocation on hot paths."""
    return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def covered_cells(
    x: float,
    y: float,
    width: float,
    height: float,
    cell_size: float,
) -> list[tuple[int, int]]:
    """Return the grid cells that a rectangle overlaps."""
    min_cx = math.floor(x / cell_size)
    max_cx = math.floor((x + width) / cell_size)
    min_cy = math.floor(y / cell_size)
    max_cy = math.floor((y + height) / cell_size)
    return [(cx, cy) for cx in range(min_cx, max_cx + 1) for cy in range(min_cy, max_cy + 1)]


class SpatialHash:
    """Grid-based broadphase for collision detection.

    Insert entities with their bounding box, then query a region to find
    which entity IDs overlap that region.
    """

    def __init__(self, cell_size: float) -> None:
        self.cell_size = cell_size
        self._buckets: dict[tuple[int, int], list[int]] = {}

    def clear(self) -> None:
        self._buckets.clear()

    def insert(self, entity_id: int, x: float, y: float, w: float, h: float) -> None:
        for cell in covered_cells(x, y, w, h, self.cell_size):
            self._buckets.setdefault(cell, []).append(entity_id)

    def query(self, x: float, y: float, w: float, h: float) -> set[int]:
        result: set[int] = set()
        for cell in covered_cells(x, y, w, h, self.cell_size):
            for eid in self._buckets.get(cell, ()):
                result.add(eid)
        return result
