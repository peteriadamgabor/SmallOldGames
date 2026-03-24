"""Shared touch-control helpers for game scenes."""

from __future__ import annotations

from dataclasses import dataclass

from smalloldgames.menus.components import draw_button
from smalloldgames.rendering.primitives import DrawList

from .input import GameAction, TouchRegion


@dataclass(frozen=True, slots=True)
class TouchButton:
    """Declarative definition of an on-screen touch button."""

    x: float
    y: float
    width: float
    height: float
    label: str
    actions: frozenset[GameAction]
    label_scale: float = 2.0


def render_touch_buttons(draw: DrawList, buttons: tuple[TouchButton, ...]) -> None:
    """Render all touch buttons using the standard ``draw_button`` helper."""
    for btn in buttons:
        draw_button(
            draw, x=btn.x, y=btn.y, width=btn.width, height=btn.height,
            label=btn.label, label_scale=btn.label_scale,
        )


def build_touch_regions(
    buttons: tuple[TouchButton, ...],
    *,
    enabled: bool = True,
    active: bool = True,
) -> tuple[TouchRegion, ...]:
    """Build ``TouchRegion`` tuple from button definitions.

    Returns empty tuple when *enabled* or *active* is ``False``.
    """
    if not enabled or not active:
        return ()
    return tuple(
        TouchRegion(btn.x, btn.y, btn.width, btn.height, btn.actions)
        for btn in buttons
    )
