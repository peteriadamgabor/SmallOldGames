"""Static rendering assets and asset-loading helpers."""

from .atlas import COMBINED_ATLAS
from .catalog import CONFIG_DIR, PROJECT_ASSETS_DIR, PROJECT_ROOT, SHADERS_DIR, SPRITES_DIR
from .sprites import PackedSprite, Sprite, SpriteAtlas, build_sprite_atlas, font_glyphs_from_atlas, load_xpm

__all__ = [
    "COMBINED_ATLAS",
    "CONFIG_DIR",
    "PROJECT_ASSETS_DIR",
    "PROJECT_ROOT",
    "SHADERS_DIR",
    "SPRITES_DIR",
    "PackedSprite",
    "Sprite",
    "SpriteAtlas",
    "build_sprite_atlas",
    "font_glyphs_from_atlas",
    "load_xpm",
]
