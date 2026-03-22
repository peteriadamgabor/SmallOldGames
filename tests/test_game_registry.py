from __future__ import annotations

import unittest

from smalloldgames.engine import GameDefinition, GameRegistry


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


if __name__ == "__main__":
    unittest.main()
