from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .bitmap_font import FONT_5X7

Color = tuple[float, float, float, float]
_FONT_GLYPH_PREFIX = "__font__:"


@dataclass(frozen=True, slots=True)
class Sprite:
    width: int
    height: int
    pixels: tuple[tuple[Color | None, ...], ...]


@dataclass(frozen=True, slots=True)
class PackedSprite:
    width: int
    height: int
    u0: float
    v0: float
    u1: float
    v1: float


@dataclass(frozen=True, slots=True)
class SpriteAtlas:
    width: int
    height: int
    rgba_bytes: bytes
    white_uv: tuple[float, float]
    sprites: dict[str, PackedSprite]


@lru_cache(maxsize=64)
def load_xpm(path: str | Path) -> Sprite:
    sprite_path = Path(path)
    strings = re.findall(r'"([^"]*)"', sprite_path.read_text(encoding="utf-8"))
    if not strings:
        raise ValueError(f"{sprite_path} does not contain XPM string data.")

    width, height, color_count, chars_per_pixel = (int(part) for part in strings[0].split())
    color_lines = strings[1 : 1 + color_count]
    pixel_lines = strings[1 + color_count : 1 + color_count + height]

    palette: dict[str, Color | None] = {}
    for line in color_lines:
        key = line[:chars_per_pixel]
        parts = line[chars_per_pixel:].strip().split()
        if len(parts) < 2 or parts[0] != "c":
            raise ValueError(f"Unsupported XPM color definition in {sprite_path}: {line!r}")
        palette[key] = None if parts[1] == "None" else _parse_hex_color(parts[1])

    pixels: list[tuple[Color | None, ...]] = []
    for line in pixel_lines:
        row: list[Color | None] = []
        for index in range(0, len(line), chars_per_pixel):
            row.append(palette[line[index : index + chars_per_pixel]])
        if len(row) != width:
            raise ValueError(f"Invalid XPM row width in {sprite_path}: {line!r}")
        pixels.append(tuple(row))

    if len(pixels) != height:
        raise ValueError(f"Invalid XPM height in {sprite_path}: expected {height}, got {len(pixels)}")

    return Sprite(width=width, height=height, pixels=tuple(pixels))


def build_sprite_atlas(named_sprites: dict[str, Sprite], *, padding: int = 1) -> SpriteAtlas:
    if not named_sprites:
        raise ValueError("build_sprite_atlas requires at least one sprite.")

    ordered = sorted({**named_sprites, **_build_font_sprites()}.items())
    atlas_width = max(
        64,
        2 + sum(sprite.width + padding for _, sprite in ordered) + padding,
    )

    positions: dict[str, tuple[int, int]] = {}
    cursor_x = 1 + padding
    cursor_y = 1 + padding
    row_height = 0
    used_height = 0

    for name, sprite in ordered:
        if cursor_x + sprite.width + padding >= atlas_width:
            cursor_x = 1 + padding
            cursor_y += row_height + padding
            row_height = 0
        positions[name] = (cursor_x, cursor_y)
        cursor_x += sprite.width + padding
        row_height = max(row_height, sprite.height)
        used_height = max(used_height, cursor_y + sprite.height + padding)

    atlas_height = max(64, used_height + 1 + padding)
    pixels: list[list[tuple[int, int, int, int]]] = [
        [(0, 0, 0, 0) for _ in range(atlas_width)] for _ in range(atlas_height)
    ]

    # Reserve a white texel for flat-color geometry.
    pixels[1][1] = (255, 255, 255, 255)

    packed: dict[str, PackedSprite] = {}
    for name, sprite in ordered:
        x0, y0 = positions[name]
        for row_index, row in enumerate(sprite.pixels):
            for col_index, color in enumerate(row):
                if color is None:
                    continue
                pixels[y0 + row_index][x0 + col_index] = _to_rgba8(color)
        packed[name] = PackedSprite(
            width=sprite.width,
            height=sprite.height,
            u0=x0 / atlas_width,
            v0=y0 / atlas_height,
            u1=(x0 + sprite.width) / atlas_width,
            v1=(y0 + sprite.height) / atlas_height,
        )

    rgba = bytearray()
    for row in pixels:
        for r, g, b, a in row:
            rgba.extend((r, g, b, a))

    white_uv = ((1.5) / atlas_width, (1.5) / atlas_height)
    return SpriteAtlas(
        width=atlas_width,
        height=atlas_height,
        rgba_bytes=bytes(rgba),
        white_uv=white_uv,
        sprites=packed,
    )


def font_glyphs_from_atlas(atlas: SpriteAtlas) -> dict[str, PackedSprite]:
    return {character: atlas.sprites[_font_sprite_name(character)] for character in FONT_5X7}


def _font_sprite_name(character: str) -> str:
    return f"{_FONT_GLYPH_PREFIX}{character}"


def _build_font_sprites() -> dict[str, Sprite]:
    return {_font_sprite_name(character): _bitmap_glyph_sprite(glyph) for character, glyph in FONT_5X7.items()}


def _bitmap_glyph_sprite(glyph: tuple[str, ...]) -> Sprite:
    pixels: list[tuple[Color | None, ...]] = []
    for row in glyph:
        pixels.append(tuple((1.0, 1.0, 1.0, 1.0) if bit == "1" else None for bit in row))
    return Sprite(width=5, height=7, pixels=tuple(pixels))


def _parse_hex_color(value: str) -> Color:
    value = value.lstrip("#")
    if len(value) != 6:
        raise ValueError(f"Unsupported color format: {value!r}")
    return (
        int(value[0:2], 16) / 255.0,
        int(value[2:4], 16) / 255.0,
        int(value[4:6], 16) / 255.0,
        1.0,
    )


def _to_rgba8(color: Color) -> tuple[int, int, int, int]:
    return (
        int(max(0.0, min(1.0, color[0])) * 255),
        int(max(0.0, min(1.0, color[1])) * 255),
        int(max(0.0, min(1.0, color[2])) * 255),
        int(max(0.0, min(1.0, color[3])) * 255),
    )
