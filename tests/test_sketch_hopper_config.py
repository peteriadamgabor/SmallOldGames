from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from smalloldgames.games.sketch_hopper_game.config import (
    SketchHopperConfig,
    load_sketch_hopper_config,
    reset_sketch_hopper_config,
    save_sketch_hopper_config,
)
from smalloldgames.games.sketch_hopper import SketchHopperScene


class SketchHopperConfigTests(unittest.TestCase):
    def test_load_sketch_hopper_config_reads_overrides(self) -> None:
        with TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "sketch_hopper.toml"
            config_path.write_text(
                """
[player]
gravity = -1500.0

[monsters]
monster_min_height = 3200.0

[pickups]
pickup_min_gap_y = 1400.0
""".strip(),
                encoding="utf-8",
            )
            config = load_sketch_hopper_config(config_path)
            self.assertEqual(config.gravity, -1500.0)
            self.assertEqual(config.monster_min_height, 3200.0)
            self.assertEqual(config.pickup_min_gap_y, 1400.0)

    def test_scene_uses_injected_config(self) -> None:
        config = SketchHopperConfig(monster_min_height=3456.0, pickup_spawn_chance_base=0.005)
        scene = SketchHopperScene(lambda: None, config=config, seed=7)
        self.assertEqual(scene.monster_min_height, 3456.0)
        self.assertEqual(scene.pickup_spawn_chance_base, 0.005)

    def test_saved_override_can_be_loaded_and_reset(self) -> None:
        with TemporaryDirectory() as temp_dir:
            override_path = Path(temp_dir) / "override.toml"
            config = SketchHopperConfig(monster_spawn_chance=0.81, ufo_min_height=6123.0)
            save_sketch_hopper_config(config, override_path)
            loaded = load_sketch_hopper_config(override_path)
            self.assertEqual(loaded.monster_spawn_chance, 0.81)
            self.assertEqual(loaded.ufo_min_height, 6123.0)
            reset_sketch_hopper_config(override_path)
            self.assertFalse(override_path.exists())


if __name__ == "__main__":
    unittest.main()
