from __future__ import annotations

from dataclasses import dataclass

from smalloldgames.rendering.primitives import DrawList

from .common import (
    ACCENT,
    PANEL,
    PANEL_ACTIVE,
    PANEL_IDLE,
    PANEL_TOP,
    PANEL_TOP_ACTIVE,
    PANEL_TOP_IDLE,
    TEXT_LIGHT,
)

Color = tuple[float, float, float, float]

CARD_FILL: Color = (0.08, 0.09, 0.12, 0.45)
BUTTON_FILL: Color = (0.06, 0.08, 0.10, 0.55)


@dataclass(frozen=True, slots=True)
class PanelStyle:
    bottom: Color
    top: Color
    fill: Color = CARD_FILL


BASE_PANEL = PanelStyle(PANEL, PANEL_TOP)
IDLE_CARD = PanelStyle(PANEL_IDLE, PANEL_TOP_IDLE)
ACTIVE_CARD = PanelStyle(PANEL_ACTIVE, PANEL_TOP_ACTIVE)


def draw_panel(
    draw: DrawList,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    style: PanelStyle = BASE_PANEL,
    inset: float = 0.0,
) -> None:
    draw.gradient_quad(
        x,
        y,
        width,
        height,
        bottom_left=style.bottom,
        bottom_right=style.bottom,
        top_right=style.top,
        top_left=style.top,
        world=False,
    )
    if inset > 0.0:
        draw.quad(
            x + inset,
            y + inset,
            width - inset * 2.0,
            height - inset * 2.0,
            style.fill,
            world=False,
        )


def draw_button(
    draw: DrawList,
    *,
    x: float,
    y: float,
    width: float,
    height: float,
    label: str,
    label_scale: float = 3.0,
    label_color: Color = TEXT_LIGHT,
    style: PanelStyle = BASE_PANEL,
) -> None:
    draw_panel(draw, x=x, y=y, width=width, height=height, style=style)
    draw.text(x + width * 0.5, y + height * 0.39, label, scale=label_scale, color=label_color, centered=True)


def draw_play_badge(draw: DrawList, *, x: float, y: float, active: bool) -> None:
    if not active:
        return
    draw.quad(x, y, 86, 24, BUTTON_FILL, world=False)
    draw.text(x + 13, y + 8, "PLAY", scale=3, color=ACCENT, world=False)
