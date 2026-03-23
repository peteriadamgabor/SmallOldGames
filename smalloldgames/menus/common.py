from __future__ import annotations

from smalloldgames.assets import COMBINED_ATLAS
from smalloldgames.rendering.primitives import DrawList

Color = tuple[float, float, float, float]

BG_BOTTOM: Color = (0.08, 0.09, 0.16, 1.0)
BG_TOP: Color = (0.18, 0.25, 0.42, 1.0)
PANEL: Color = (0.13, 0.16, 0.24, 1.0)
PANEL_TOP: Color = (0.24, 0.28, 0.39, 1.0)
PANEL_ACTIVE: Color = (0.19, 0.68, 0.33, 1.0)
PANEL_IDLE: Color = PANEL
PANEL_TOP_ACTIVE: Color = (0.35, 0.85, 0.48, 1.0)
PANEL_TOP_IDLE: Color = PANEL_TOP
TEXT_LIGHT: Color = (0.94, 0.97, 0.93, 1.0)
TEXT_MUTED: Color = (0.71, 0.76, 0.83, 1.0)
ACCENT: Color = (1.0, 0.84, 0.29, 1.0)
GOOD: Color = (0.43, 0.86, 0.54, 1.0)

CLOUD_SPRITE = COMBINED_ATLAS.sprites["cloud"]
HOPPER_SPRITE = COMBINED_ATLAS.sprites["hopper"]
MONSTER_SPRITE = COMBINED_ATLAS.sprites["monster"]
BLACK_HOLE_SPRITE = COMBINED_ATLAS.sprites["black_hole"]
PLATFORM_STABLE_SPRITE = COMBINED_ATLAS.sprites["platform_stable"]
PLATFORM_MOVING_SPRITE = COMBINED_ATLAS.sprites["platform_moving"]
SNAKE_HEAD_SPRITE = COMBINED_ATLAS.sprites.get("snake_head")
SNAKE_BODY_SPRITE = COMBINED_ATLAS.sprites.get("snake_body")
FOOD_SPRITE = COMBINED_ATLAS.sprites.get("food")


def fit_scale(draw: DrawList, text: str, *, preferred: int, minimum: int, max_width: float) -> int:
    for scale in range(preferred, minimum - 1, -1):
        if draw.measure_text(text, scale=scale) <= max_width:
            return scale
    return minimum


def render_background_clouds(draw: DrawList) -> None:
    for x, y, width, height in (
        (22.0, 828.0, 102.0, 48.0),
        (398.0, 800.0, 92.0, 44.0),
        (58.0, 666.0, 118.0, 56.0),
        (370.0, 612.0, 86.0, 40.0),
        (202.0, 244.0, 116.0, 54.0),
    ):
        draw.sprite(x, y, CLOUD_SPRITE, width=width, height=height, world=False)


def draw_menu_background(draw: DrawList) -> None:
    draw.gradient_quad(
        0,
        0,
        draw.width,
        draw.height,
        bottom_left=BG_BOTTOM,
        bottom_right=BG_BOTTOM,
        top_right=BG_TOP,
        top_left=BG_TOP,
        world=False,
    )
    render_background_clouds(draw)
