from __future__ import annotations

from .catalog import SPRITES_DIR
from .sprites import build_sprite_atlas, load_xpm

_HOPPER_DIR = SPRITES_DIR / "sketch_hopper"
_SNAKE_DIR = SPRITES_DIR / "snake"
_INVADERS_DIR = SPRITES_DIR / "space_invaders"

SKETCH_HOPPER_SPRITE_PATHS = {
    "black_hole": _HOPPER_DIR / "black_hole.xpm",
    "boots": _HOPPER_DIR / "boots.xpm",
    "cloud": _HOPPER_DIR / "cloud.xpm",
    "hopper": _HOPPER_DIR / "hopper.xpm",
    "enemy_shot": _HOPPER_DIR / "enemy_shot.xpm",
    "jetpack": _HOPPER_DIR / "jetpack.xpm",
    "monster": _HOPPER_DIR / "monster.xpm",
    "spring": _HOPPER_DIR / "spring.xpm",
    "projectile": _HOPPER_DIR / "projectile.xpm",
    "propeller": _HOPPER_DIR / "propeller.xpm",
    "platform_stable": _HOPPER_DIR / "platform_stable.xpm",
    "platform_moving": _HOPPER_DIR / "platform_moving.xpm",
    "platform_broken": _HOPPER_DIR / "platform_broken.xpm",
    "shield": _HOPPER_DIR / "shield.xpm",
    "rocket": _HOPPER_DIR / "rocket.xpm",
    "ufo": _HOPPER_DIR / "ufo.xpm",
}

SNAKE_SPRITE_PATHS = {
    "snake_head": _SNAKE_DIR / "snake_head.xpm",
    "snake_body": _SNAKE_DIR / "snake_body.xpm",
    "food": _SNAKE_DIR / "food.xpm",
}

SPACE_INVADERS_SPRITE_PATHS = {
    "cannon": _INVADERS_DIR / "cannon.xpm",
    "invader_a": _INVADERS_DIR / "invader_a.xpm",
    "invader_b": _INVADERS_DIR / "invader_b.xpm",
    "invader_c": _INVADERS_DIR / "invader_c.xpm",
}

# Combine all unique sprite paths
ALL_SPRITE_PATHS = {**SKETCH_HOPPER_SPRITE_PATHS, **SNAKE_SPRITE_PATHS, **SPACE_INVADERS_SPRITE_PATHS}

COMBINED_ATLAS = build_sprite_atlas({name: load_xpm(path) for name, path in ALL_SPRITE_PATHS.items()})

# Legacy exports for individual games if they still need their own limited views
SKETCH_HOPPER_ATLAS = COMBINED_ATLAS
SNAKE_ATLAS = COMBINED_ATLAS
SPACE_INVADERS_ATLAS = COMBINED_ATLAS
