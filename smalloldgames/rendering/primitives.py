from __future__ import annotations

from array import array
from dataclasses import dataclass, field
from functools import lru_cache

from smalloldgames.assets.bitmap_font import FONT_5X7, normalize_text
from smalloldgames.assets.sprites import PackedSprite

Color = tuple[float, float, float, float]


@lru_cache(maxsize=256)
def _cached_normalize(value: str) -> str:
    return normalize_text(value)


@dataclass(slots=True)
class DrawList:
    width: int
    height: int
    white_uv: tuple[float, float]
    font_glyphs: dict[str, PackedSprite] = field(default_factory=dict)
    camera_y: float = 0.0
    vertices: array = field(default_factory=lambda: array("f"))
    _inv_w: float = 0.0
    _inv_h: float = 0.0
    _cam_y: float = 0.0

    def __post_init__(self) -> None:
        self._inv_w = 2.0 / self.width
        self._inv_h = 2.0 / self.height

    def set_camera(self, camera_y: float) -> None:
        self.camera_y = camera_y
        self._cam_y = camera_y

    def clear(self) -> None:
        del self.vertices[:]

    def gradient_quad(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        *,
        bottom_left: Color,
        bottom_right: Color,
        top_right: Color,
        top_left: Color,
        world: bool = True,
    ) -> None:
        inv_w = self._inv_w
        inv_h = self._inv_h
        cam = self._cam_y if world else 0.0
        x0 = x * inv_w - 1.0
        y0 = (y - cam) * inv_h - 1.0
        x1 = (x + width) * inv_w - 1.0
        y1 = (y + height - cam) * inv_h - 1.0
        u, v = self.white_uv
        bl_r, bl_g, bl_b, bl_a = bottom_left
        br_r, br_g, br_b, br_a = bottom_right
        tr_r, tr_g, tr_b, tr_a = top_right
        tl_r, tl_g, tl_b, tl_a = top_left
        self.vertices.extend(
            (
                x0,
                y0,
                bl_r,
                bl_g,
                bl_b,
                bl_a,
                u,
                v,
                x1,
                y0,
                br_r,
                br_g,
                br_b,
                br_a,
                u,
                v,
                x1,
                y1,
                tr_r,
                tr_g,
                tr_b,
                tr_a,
                u,
                v,
                x0,
                y0,
                bl_r,
                bl_g,
                bl_b,
                bl_a,
                u,
                v,
                x1,
                y1,
                tr_r,
                tr_g,
                tr_b,
                tr_a,
                u,
                v,
                x0,
                y1,
                tl_r,
                tl_g,
                tl_b,
                tl_a,
                u,
                v,
            )
        )

    def quad(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Color,
        *,
        world: bool = True,
    ) -> None:
        inv_w = self._inv_w
        inv_h = self._inv_h
        cam = self._cam_y if world else 0.0
        x0 = x * inv_w - 1.0
        y0 = (y - cam) * inv_h - 1.0
        x1 = (x + width) * inv_w - 1.0
        y1 = (y + height - cam) * inv_h - 1.0
        r, g, b, a = color
        u, v = self.white_uv
        self.vertices.extend(
            (
                x0,
                y0,
                r,
                g,
                b,
                a,
                u,
                v,
                x1,
                y0,
                r,
                g,
                b,
                a,
                u,
                v,
                x1,
                y1,
                r,
                g,
                b,
                a,
                u,
                v,
                x0,
                y0,
                r,
                g,
                b,
                a,
                u,
                v,
                x1,
                y1,
                r,
                g,
                b,
                a,
                u,
                v,
                x0,
                y1,
                r,
                g,
                b,
                a,
                u,
                v,
            )
        )

    def triangle(
        self,
        p0: tuple[float, float],
        p1: tuple[float, float],
        p2: tuple[float, float],
        color: Color,
        *,
        world: bool = True,
    ) -> None:
        inv_w = self._inv_w
        inv_h = self._inv_h
        cam = self._cam_y if world else 0.0
        r, g, b, a = color
        u, v = self.white_uv
        self.vertices.extend(
            (
                p0[0] * inv_w - 1.0,
                (p0[1] - cam) * inv_h - 1.0,
                r,
                g,
                b,
                a,
                u,
                v,
                p1[0] * inv_w - 1.0,
                (p1[1] - cam) * inv_h - 1.0,
                r,
                g,
                b,
                a,
                u,
                v,
                p2[0] * inv_w - 1.0,
                (p2[1] - cam) * inv_h - 1.0,
                r,
                g,
                b,
                a,
                u,
                v,
            )
        )

    def text(
        self,
        x: float,
        y: float,
        value: str,
        *,
        scale: float,
        color: Color,
        centered: bool = False,
        world: bool = False,
    ) -> None:
        text = _cached_normalize(value)
        if centered:
            x -= self.measure_text(text, scale=scale) * 0.5
        inv_w = self._inv_w
        inv_h = self._inv_h
        cam = self._cam_y if world else 0.0
        r, g, b, a = color
        font_glyphs = self.font_glyphs
        vertices = self.vertices
        char_step = 6 * scale
        glyph_w = 5 * scale
        glyph_h = 7 * scale
        cursor_x = x
        for character in text:
            if character == " ":
                cursor_x += char_step
                continue
            sprite = font_glyphs.get(character)
            if sprite is not None:
                x0 = cursor_x * inv_w - 1.0
                y0 = (y - cam) * inv_h - 1.0
                x1 = (cursor_x + glyph_w) * inv_w - 1.0
                y1 = (y + glyph_h - cam) * inv_h - 1.0
                u0, u1 = sprite.u0, sprite.u1
                v0, v1 = sprite.v1, sprite.v0
                vertices.extend(
                    (
                        x0,
                        y0,
                        r,
                        g,
                        b,
                        a,
                        u0,
                        v0,
                        x1,
                        y0,
                        r,
                        g,
                        b,
                        a,
                        u1,
                        v0,
                        x1,
                        y1,
                        r,
                        g,
                        b,
                        a,
                        u1,
                        v1,
                        x0,
                        y0,
                        r,
                        g,
                        b,
                        a,
                        u0,
                        v0,
                        x1,
                        y1,
                        r,
                        g,
                        b,
                        a,
                        u1,
                        v1,
                        x0,
                        y1,
                        r,
                        g,
                        b,
                        a,
                        u0,
                        v1,
                    )
                )
            else:
                self._draw_bitmap_glyph(cursor_x, y, FONT_5X7[character], scale=scale, color=color, world=world)
            cursor_x += char_step

    def sprite(
        self,
        x: float,
        y: float,
        sprite: PackedSprite,
        *,
        width: float,
        height: float,
        world: bool = True,
        flip_x: bool = False,
    ) -> None:
        inv_w = self._inv_w
        inv_h = self._inv_h
        cam = self._cam_y if world else 0.0
        x0 = x * inv_w - 1.0
        y0 = (y - cam) * inv_h - 1.0
        x1 = (x + width) * inv_w - 1.0
        y1 = (y + height - cam) * inv_h - 1.0
        u0, u1 = (sprite.u1, sprite.u0) if flip_x else (sprite.u0, sprite.u1)
        v0, v1 = sprite.v1, sprite.v0
        self.vertices.extend(
            (
                x0,
                y0,
                1.0,
                1.0,
                1.0,
                1.0,
                u0,
                v0,
                x1,
                y0,
                1.0,
                1.0,
                1.0,
                1.0,
                u1,
                v0,
                x1,
                y1,
                1.0,
                1.0,
                1.0,
                1.0,
                u1,
                v1,
                x0,
                y0,
                1.0,
                1.0,
                1.0,
                1.0,
                u0,
                v0,
                x1,
                y1,
                1.0,
                1.0,
                1.0,
                1.0,
                u1,
                v1,
                x0,
                y1,
                1.0,
                1.0,
                1.0,
                1.0,
                u0,
                v1,
            )
        )

    @staticmethod
    def measure_text(value: str, *, scale: float) -> float:
        return max(len(_cached_normalize(value)) * 6 * scale - scale, 0.0)

    def _draw_bitmap_glyph(
        self,
        x: float,
        y: float,
        glyph: tuple[str, ...],
        *,
        scale: float,
        color: Color,
        world: bool,
    ) -> None:
        for row_index, row in enumerate(glyph):
            for col_index, bit in enumerate(row):
                if bit == "1":
                    self.quad(
                        x + col_index * scale,
                        y + (6 - row_index) * scale,
                        scale,
                        scale,
                        color,
                        world=world,
                    )
