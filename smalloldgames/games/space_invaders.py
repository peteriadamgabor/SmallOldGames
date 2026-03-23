from __future__ import annotations

from smalloldgames.engine.game_registry import GameDefinition
from smalloldgames.engine.scene import SceneContext

from .space_invaders_game.scene import SpaceInvadersScene

__all__ = ["SpaceInvadersScene", "register_game"]


def register_game(*, ctx: SceneContext, on_exit) -> GameDefinition:
    return GameDefinition(
        id="space_invaders",
        title="SPACE INVADERS",
        subtitle="ALIEN ONSLAUGHT",
        detail="PRESS ENTER OR SPACE",
        score_key="space_invaders",
        art_variant="space_invaders",
        music_track="space_invaders",
        make_scene=lambda: SpaceInvadersScene(on_exit, ctx=ctx),
    )
