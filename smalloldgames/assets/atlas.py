from __future__ import annotations

from .catalog import SPRITES_DIR
from .sprites import build_sprite_atlas, load_xpm

SKETCH_HOPPER_SPRITE_PATHS = {
    "black_hole": SPRITES_DIR / "black_hole.xpm",
    "boots": SPRITES_DIR / "boots.xpm",
    "cloud": SPRITES_DIR / "cloud.xpm",
    "hopper": SPRITES_DIR / "hopper.xpm",
    "enemy_shot": SPRITES_DIR / "enemy_shot.xpm",
    "jetpack": SPRITES_DIR / "jetpack.xpm",
    "monster": SPRITES_DIR / "monster.xpm",
    "spring": SPRITES_DIR / "spring.xpm",
    "projectile": SPRITES_DIR / "projectile.xpm",
    "propeller": SPRITES_DIR / "propeller.xpm",
    "platform_stable": SPRITES_DIR / "platform_stable.xpm",
    "platform_moving": SPRITES_DIR / "platform_moving.xpm",
    "platform_broken": SPRITES_DIR / "platform_broken.xpm",
    "shield": SPRITES_DIR / "shield.xpm",
    "rocket": SPRITES_DIR / "rocket.xpm",
    "ufo": SPRITES_DIR / "ufo.xpm",
}

SNAKE_SPRITE_PATHS = {
    "snake_head": SPRITES_DIR / "snake_head.xpm",
    "snake_body": SPRITES_DIR / "snake_body.xpm",
    "food": SPRITES_DIR / "food.xpm",
}

SPACE_INVADERS_SPRITE_PATHS = {
    "cannon": SPRITES_DIR / "cannon.xpm",
    "invader_a": SPRITES_DIR / "invader_a.xpm",
    "invader_b": SPRITES_DIR / "invader_b.xpm",
    "invader_c": SPRITES_DIR / "invader_c.xpm",
}

# Combine all unique sprite paths
ALL_SPRITE_PATHS = {**SKETCH_HOPPER_SPRITE_PATHS, **SNAKE_SPRITE_PATHS, **SPACE_INVADERS_SPRITE_PATHS}

COMBINED_ATLAS = build_sprite_atlas({name: load_xpm(path) for name, path in ALL_SPRITE_PATHS.items()})

# Legacy exports for individual games if they still need their own limited views
SKETCH_HOPPER_ATLAS = COMBINED_ATLAS
SNAKE_ATLAS = COMBINED_ATLAS
SPACE_INVADERS_ATLAS = COMBINED_ATLAS
