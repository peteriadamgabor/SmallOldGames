from __future__ import annotations

import unittest

from smalloldgames.assets.sprites import Sprite, build_sprite_atlas, font_glyphs_from_atlas
from smalloldgames.rendering.primitives import DrawList


class DrawListTextTests(unittest.TestCase):
    def test_text_uses_one_quad_per_character_when_font_glyphs_are_available(self) -> None:
        atlas = build_sprite_atlas({"dummy": Sprite(width=1, height=1, pixels=(((1.0, 1.0, 1.0, 1.0),),))})
        draw = DrawList(540, 960, white_uv=atlas.white_uv, font_glyphs=font_glyphs_from_atlas(atlas))

        draw.text(20.0, 30.0, "AB1", scale=2.0, color=(1.0, 0.5, 0.25, 1.0))

        self.assertEqual(len(draw.vertices) // 8, 18)

    def test_text_falls_back_to_bitmap_quads_without_font_glyphs(self) -> None:
        draw = DrawList(540, 960, white_uv=(0.0, 0.0))

        draw.text(20.0, 30.0, "A", scale=1.0, color=(1.0, 1.0, 1.0, 1.0))

        self.assertEqual(len(draw.vertices) // 8, 108)


if __name__ == "__main__":
    unittest.main()
