from __future__ import annotations

from smalloldgames.engine.game_registry import GameDefinition
from smalloldgames.engine.scene import SceneContext

from .snake_game.scene import SnakeScene

__all__ = ["SnakeScene", "register_game"]


def register_game(*, ctx: SceneContext, on_exit) -> GameDefinition:
    return GameDefinition(
        id="snake",
        title="SNAKE CLASSIC",
        subtitle="RETRO GRID JUGGERNAUT",
        detail="PRESS ENTER OR SPACE",
        score_key="snake",
        art_variant="snake",
        music_track="launcher",
        make_scene=lambda: SnakeScene(on_exit, ctx=ctx),
    )
