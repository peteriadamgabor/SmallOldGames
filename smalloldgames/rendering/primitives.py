from __future__ import annotations

from array import array
from dataclasses import dataclass, field
from functools import lru_cache

from smalloldgames.assets.bitmap_font import FONT_5X7, normalize_text
from smalloldgames.assets.sprites import PackedSprite

Color = tuple[float, float, float, float]

FLOATS_PER_VERTEX = 8
FONT_GLYPH_WIDTH = 5
FONT_GLYPH_HEIGHT = 7
FONT_CHAR_STEP = 6  # glyph width + 1px spacing


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

    def _emit_quad(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        r0: float,
        g0: float,
        b0: float,
        a0: float,
        r1: float,
        g1: float,
        b1: float,
        a1: float,
        r2: float,
        g2: float,
        b2: float,
        a2: float,
        r3: float,
        g3: float,
        b3: float,
        a3: float,
        u0: float,
        v0: float,
        u1: float,
        v1: float,
    ) -> None:
        """Emit 6 vertices (two triangles) for a quad.

        Corners: (x0,y0)=bottom-left, (x1,y0)=bottom-right,
                 (x1,y1)=top-right, (x0,y1)=top-left.
        Colors: 0=BL, 1=BR, 2=TR, 3=TL.
        UVs: (u0,v0)=BL, (u1,v1)=TR.
        """
        self.vertices.extend(
            (
                x0,
                y0,
                r0,
                g0,
                b0,
                a0,
                u0,
                v0,
                x1,
                y0,
                r1,
                g1,
                b1,
                a1,
                u1,
                v0,
                x1,
                y1,
                r2,
                g2,
                b2,
                a2,
                u1,
                v1,
                x0,
                y0,
                r0,
                g0,
                b0,
                a0,
                u0,
                v0,
                x1,
                y1,
                r2,
                g2,
                b2,
                a2,
                u1,
                v1,
                x0,
                y1,
                r3,
                g3,
                b3,
                a3,
                u0,
                v1,
            )
        )

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
        self._emit_quad(
            x0,
            y0,
            x1,
            y1,
            bl_r,
            bl_g,
            bl_b,
            bl_a,
            br_r,
            br_g,
            br_b,
            br_a,
            tr_r,
            tr_g,
            tr_b,
            tr_a,
            tl_r,
            tl_g,
            tl_b,
            tl_a,
            u,
            v,
            u,
            v,
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
        self._emit_quad(x0, y0, x1, y1, r, g, b, a, r, g, b, a, r, g, b, a, r, g, b, a, u, v, u, v)

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
        char_step = FONT_CHAR_STEP * scale
        glyph_w = FONT_GLYPH_WIDTH * scale
        glyph_h = FONT_GLYPH_HEIGHT * scale
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
                su0, su1 = sprite.u0, sprite.u1
                sv0, sv1 = sprite.v1, sprite.v0
                self._emit_quad(
                    x0,
                    y0,
                    x1,
                    y1,
                    r,
                    g,
                    b,
                    a,
                    r,
                    g,
                    b,
                    a,
                    r,
                    g,
                    b,
                    a,
                    r,
                    g,
                    b,
                    a,
                    su0,
                    sv0,
                    su1,
                    sv1,
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
        self._emit_quad(
            x0,
            y0,
            x1,
            y1,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            1.0,
            u0,
            v0,
            u1,
            v1,
        )

    @staticmethod
    @lru_cache(maxsize=256)
    def measure_text(value: str, *, scale: float) -> float:
        return max(len(_cached_normalize(value)) * FONT_CHAR_STEP * scale - scale, 0.0)

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
                        y + (FONT_GLYPH_HEIGHT - 1 - row_index) * scale,
                        scale,
                        scale,
                        color,
                        world=world,
                    )
