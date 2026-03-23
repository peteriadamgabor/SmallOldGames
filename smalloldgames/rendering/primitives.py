from __future__ import annotations

from array import array
from dataclasses import dataclass, field

from smalloldgames.assets.bitmap_font import FONT_5X7, normalize_text
from smalloldgames.assets.sprites import PackedSprite

Color = tuple[float, float, float, float]


@dataclass(slots=True)
class DrawList:
    width: int
    height: int
    white_uv: tuple[float, float]
    font_glyphs: dict[str, PackedSprite] = field(default_factory=dict)
    camera_y: float = 0.0
    vertices: array = field(default_factory=lambda: array("f"))

    def set_camera(self, camera_y: float) -> None:
        self.camera_y = camera_y

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
        uv = self.white_uv
        x0, y0 = self._to_ndc(x, y, world)
        x1, y1 = self._to_ndc(x + width, y + height, world)
        self._push_vertex(x0, y0, bottom_left, uv)
        self._push_vertex(x1, y0, bottom_right, uv)
        self._push_vertex(x1, y1, top_right, uv)
        self._push_vertex(x0, y0, bottom_left, uv)
        self._push_vertex(x1, y1, top_right, uv)
        self._push_vertex(x0, y1, top_left, uv)

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
        self.gradient_quad(
            x,
            y,
            width,
            height,
            bottom_left=color,
            bottom_right=color,
            top_right=color,
            top_left=color,
            world=world,
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
        uv = self.white_uv
        self._push_vertex(*self._to_ndc(*p0, world), color, uv)
        self._push_vertex(*self._to_ndc(*p1, world), color, uv)
        self._push_vertex(*self._to_ndc(*p2, world), color, uv)

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
        text = normalize_text(value)
        if centered:
            x -= self.measure_text(text, scale=scale) * 0.5
        cursor_x = x
        for character in text:
            if character == " ":
                cursor_x += 6 * scale
                continue
            sprite = self.font_glyphs.get(character)
            if sprite is None:
                self._draw_bitmap_glyph(cursor_x, y, FONT_5X7[character], scale=scale, color=color, world=world)
            else:
                self._textured_quad(cursor_x, y, 5 * scale, 7 * scale, color, sprite, world=world)
            cursor_x += 6 * scale

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
        self._textured_quad(x, y, width, height, (1.0, 1.0, 1.0, 1.0), sprite, world=world, flip_x=flip_x)

    @staticmethod
    def measure_text(value: str, *, scale: float) -> float:
        return max(len(normalize_text(value)) * 6 * scale - scale, 0.0)

    def _push_vertex(self, x: float, y: float, color: Color, uv: tuple[float, float]) -> None:
        self.vertices.extend((x, y, *color, *uv))

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

    def _textured_quad(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        color: Color,
        sprite: PackedSprite,
        *,
        world: bool,
        flip_x: bool = False,
    ) -> None:
        x0, y0 = self._to_ndc(x, y, world)
        x1, y1 = self._to_ndc(x + width, y + height, world)
        u0, u1 = (sprite.u1, sprite.u0) if flip_x else (sprite.u0, sprite.u1)
        v0, v1 = sprite.v1, sprite.v0
        self._push_vertex(x0, y0, color, (u0, v0))
        self._push_vertex(x1, y0, color, (u1, v0))
        self._push_vertex(x1, y1, color, (u1, v1))
        self._push_vertex(x0, y0, color, (u0, v0))
        self._push_vertex(x1, y1, color, (u1, v1))
        self._push_vertex(x0, y1, color, (u0, v1))

    def _to_ndc(self, x: float, y: float, world: bool) -> tuple[float, float]:
        screen_y = y - self.camera_y if world else y
        return (x / self.width) * 2.0 - 1.0, (screen_y / self.height) * 2.0 - 1.0
