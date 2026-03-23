from __future__ import annotations

import unittest
from pathlib import Path

from smalloldgames.assets.sprites import load_xpm
from smalloldgames.games.sketch_hopper_game.assets import SKETCH_HOPPER_ATLAS


class SpriteTests(unittest.TestCase):
    def test_xpm_loader_reads_dimensions_and_transparency(self) -> None:
        sprite = load_xpm(Path("assets/sprites/sketch_hopper/hopper.xpm"))
        self.assertEqual((sprite.width, sprite.height), (16, 16))
        self.assertIsNone(sprite.pixels[0][0])
        self.assertIsNotNone(sprite.pixels[3][8])

    def test_platform_sprite_dimensions(self) -> None:
        sprite = load_xpm(Path("assets/sprites/sketch_hopper/platform_stable.xpm"))
        self.assertEqual((sprite.width, sprite.height), (24, 8))

    def test_cloud_sprite_is_registered_in_atlas(self) -> None:
        sprite = load_xpm(Path("assets/sprites/sketch_hopper/cloud.xpm"))
        self.assertEqual((sprite.width, sprite.height), (32, 16))
        self.assertIn("cloud", SKETCH_HOPPER_ATLAS.sprites)

    def test_black_hole_and_jetpack_sprites_load(self) -> None:
        black_hole = load_xpm(Path("assets/sprites/sketch_hopper/black_hole.xpm"))
        jetpack = load_xpm(Path("assets/sprites/sketch_hopper/jetpack.xpm"))
        self.assertEqual((black_hole.width, black_hole.height), (16, 16))
        self.assertEqual((jetpack.width, jetpack.height), (16, 16))

    def test_new_gameplay_sprites_are_registered(self) -> None:
        shield = load_xpm(Path("assets/sprites/sketch_hopper/shield.xpm"))
        propeller = load_xpm(Path("assets/sprites/sketch_hopper/propeller.xpm"))
        ufo = load_xpm(Path("assets/sprites/sketch_hopper/ufo.xpm"))
        boots = load_xpm(Path("assets/sprites/sketch_hopper/boots.xpm"))
        rocket = load_xpm(Path("assets/sprites/sketch_hopper/rocket.xpm"))
        enemy_shot = load_xpm(Path("assets/sprites/sketch_hopper/enemy_shot.xpm"))
        self.assertEqual((shield.width, shield.height), (12, 12))
        self.assertEqual((propeller.width, propeller.height), (12, 14))
        self.assertEqual((ufo.width, ufo.height), (16, 8))
        self.assertEqual((boots.width, boots.height), (12, 12))
        self.assertEqual((rocket.width, rocket.height), (12, 18))
        self.assertEqual((enemy_shot.width, enemy_shot.height), (8, 8))
        self.assertIn("boots", SKETCH_HOPPER_ATLAS.sprites)
        self.assertIn("enemy_shot", SKETCH_HOPPER_ATLAS.sprites)
        self.assertIn("rocket", SKETCH_HOPPER_ATLAS.sprites)
        self.assertIn("shield", SKETCH_HOPPER_ATLAS.sprites)
        self.assertIn("propeller", SKETCH_HOPPER_ATLAS.sprites)
        self.assertIn("ufo", SKETCH_HOPPER_ATLAS.sprites)


if __name__ == "__main__":
    unittest.main()
