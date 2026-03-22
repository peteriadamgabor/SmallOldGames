from __future__ import annotations

from smalloldgames.assets.catalog import SPRITES_DIR
from smalloldgames.assets.sprites import build_sprite_atlas, load_xpm


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


SKETCH_HOPPER_ATLAS = build_sprite_atlas({name: load_xpm(path) for name, path in SKETCH_HOPPER_SPRITE_PATHS.items()})
