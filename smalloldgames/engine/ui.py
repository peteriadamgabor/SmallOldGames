"""Shared UI overlay and HUD widgets for game scenes."""

from __future__ import annotations

from smalloldgames.rendering.primitives import Color, DrawList

# Scrim colour used behind pause / game-over overlays
_SCRIM: Color = (0.0, 0.0, 0.0, 0.6)


def draw_gradient_background(
    draw: DrawList,
    *,
    bottom: Color = (0.08, 0.09, 0.16, 1.0),
    top: Color = (0.18, 0.25, 0.42, 1.0),
) -> None:
    """Full-screen vertical gradient used as scene background."""
    draw.gradient_quad(
        0, 0, draw.width, draw.height,
        bottom_left=bottom, bottom_right=bottom,
        top_right=top, top_left=top,
        world=False,
    )


def draw_fullscreen_scrim(draw: DrawList, *, alpha: float = 0.6) -> None:
    """Dark overlay behind pause / game-over panels."""
    draw.quad(0, 0, draw.width, draw.height, (0.0, 0.0, 0.0, alpha), world=False)


def draw_overlay_panel(
    draw: DrawList,
    *,
    title: str,
    title_y: float = 500.0,
    title_scale: float = 4.0,
    title_color: Color = (0.94, 0.97, 0.93, 1.0),
    subtitle: str = "",
    subtitle_y: float | None = None,
    subtitle_scale: float = 1.5,
    subtitle_color: Color = (0.71, 0.76, 0.83, 1.0),
    score_line: str = "",
    score_y: float | None = None,
    score_scale: float = 3.0,
    score_color: Color = (1.0, 0.84, 0.29, 1.0),
    scrim: bool = True,
    scrim_alpha: float = 0.6,
) -> None:
    """Centred overlay with title, optional subtitle and score line.

    This replaces the duplicated ``_render_overlay`` in Snake, Space Invaders
    and the game-over / pause screens in Sketch Hopper.
    """
    if scrim:
        draw_fullscreen_scrim(draw, alpha=scrim_alpha)
    cx = draw.width * 0.5
    draw.text(cx, title_y, title, scale=title_scale, color=title_color, centered=True)
    if score_line:
        sy = score_y if score_y is not None else title_y - 44.0
        draw.text(cx, sy, score_line, scale=score_scale, color=score_color, centered=True)
    if subtitle:
        default_sub_y = (title_y - 44.0) if not score_line else (title_y - 84.0)
        sy = subtitle_y if subtitle_y is not None else default_sub_y
        draw.text(cx, sy, subtitle, scale=subtitle_scale, color=subtitle_color, centered=True)


def draw_score_hud(
    draw: DrawList,
    *,
    title: str,
    title_y: float = 888.0,
    title_scale: float = 3.0,
    title_color: Color = (0.94, 0.97, 0.93, 1.0),
    score: int,
    best_score: int,
    score_y: float = 820.0,
    score_format: str = "04d",
    score_label: str = "SCORE",
    best_label: str = "BEST",
    score_color: Color = (0.43, 0.86, 0.54, 1.0),
    best_color: Color = (1.0, 0.84, 0.29, 1.0),
    margin_x: float = 60.0,
    extra_text: str = "",
    extra_y: float = 0.0,
    extra_scale: float = 2.0,
    extra_color: Color = (0.71, 0.76, 0.83, 1.0),
) -> None:
    """Standard top-of-screen score + best display, used by all games."""
    draw.text(draw.width * 0.5, title_y, title, scale=title_scale, color=title_color, centered=True)
    score_text = f"{score_label}: {score:{score_format}}"
    draw.text(margin_x, score_y, score_text, scale=2, color=score_color)
    best_text = f"{best_label}: {best_score:{score_format}}"
    best_width = draw.measure_text(best_text, scale=2)
    draw.text(draw.width - margin_x - best_width, score_y, best_text, scale=2, color=best_color)
    if extra_text:
        draw.text(draw.width * 0.5, extra_y, extra_text, scale=extra_scale, color=extra_color, centered=True)
