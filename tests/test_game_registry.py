from __future__ import annotations

import sys
import types
import unittest

from smalloldgames.engine import GameDefinition, GameRegistry, SceneContext


class GameRegistryTests(unittest.TestCase):
    def test_primary_and_lookup(self) -> None:
        first = GameDefinition(
            id="a",
            title="A",
            subtitle="AA",
            detail="PLAY",
            score_key="a",
            art_variant="hopper",
            music_track="a",
            make_scene=lambda: None,
        )
        second = GameDefinition(
            id="b",
            title="B",
            subtitle="BB",
            detail="PLAY",
            score_key="b",
            art_variant="board",
            music_track="b",
            make_scene=lambda: None,
        )

        registry = GameRegistry((first, second))

        self.assertEqual(registry.primary(), first)
        self.assertEqual(registry.get("b"), second)

    def test_registry_can_load_game_plugins_from_modules(self) -> None:
        module_name = "tests.dummy_game_plugin"
        module = types.ModuleType(module_name)

        def register_game(*, ctx: SceneContext, on_exit):
            self.assertIsInstance(ctx, SceneContext)
            return GameDefinition(
                id="dummy",
                title="DUMMY",
                subtitle="TEST PLUGIN",
                detail="PLAY",
                score_key="dummy",
                art_variant="hopper",
                music_track=None,
                make_scene=lambda: on_exit(),
            )

        module.register_game = register_game
        sys.modules[module_name] = module
        self.addCleanup(sys.modules.pop, module_name, None)

        registry = GameRegistry.from_modules((module_name,), ctx=SceneContext(), on_exit=lambda: None)

        self.assertEqual(registry.primary().id, "dummy")
        self.assertEqual(registry.get("dummy").title, "DUMMY")


if __name__ == "__main__":
    unittest.main()
