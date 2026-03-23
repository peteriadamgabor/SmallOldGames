from __future__ import annotations

from pathlib import Path

from smalloldgames.assets import COMBINED_ATLAS, SHADERS_DIR, font_glyphs_from_atlas
from smalloldgames.assets.sprites import PackedSprite
from smalloldgames.rendering.primitives import DrawList
from smalloldgames.rendering.vulkan_renderer import VulkanRenderer


class ResourceRegistry:
    """Centralized access to shared runtime assets and rendering helpers."""

    def __init__(self, *, shader_dir: Path | None = None, sprite_atlas=COMBINED_ATLAS) -> None:
        self.shader_dir = shader_dir or SHADERS_DIR
        self.sprite_atlas = sprite_atlas
        self._font_glyphs: dict[str, PackedSprite] | None = None

    def font_glyphs(self) -> dict[str, PackedSprite]:
        if self._font_glyphs is None:
            self._font_glyphs = font_glyphs_from_atlas(self.sprite_atlas)
        return self._font_glyphs

    def create_renderer(self, window, *, canvas_width: int, canvas_height: int) -> VulkanRenderer:
        return VulkanRenderer(
            window,
            shader_dir=self.shader_dir,
            sprite_atlas=self.sprite_atlas,
            canvas_width=canvas_width,
            canvas_height=canvas_height,
        )

    def create_draw_list(self, width: int, height: int) -> DrawList:
        return DrawList(
            width,
            height,
            white_uv=self.sprite_atlas.white_uv,
            font_glyphs=self.font_glyphs(),
        )
