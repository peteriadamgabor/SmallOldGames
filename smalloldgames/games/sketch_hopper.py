from __future__ import annotations

from smalloldgames.engine.game_registry import GameDefinition
from smalloldgames.engine.scene import SceneContext

from .sketch_hopper_game import (
    BALANCE_FIELDS,
    THEMES,
    BlackHole,
    Cloud,
    Color,
    ImpactEffect,
    Monster,
    Pickup,
    Platform,
    Player,
    Projectile,
    SketchHopperScene,
)

__all__ = [
    "BALANCE_FIELDS",
    "THEMES",
    "BlackHole",
    "Cloud",
    "Color",
    "ImpactEffect",
    "Monster",
    "Pickup",
    "Platform",
    "Player",
    "Projectile",
    "register_game",
    "SketchHopperScene",
]


def register_game(*, ctx: SceneContext, on_exit) -> GameDefinition:
    return GameDefinition(
        id="sketch_hopper",
        title="SKETCH HOPPER",
        subtitle="ENDLESS JUMPER",
        detail="PRESS ENTER OR SPACE",
        score_key="sketch_hopper",
        art_variant="hopper",
        music_track="sketch_hopper",
        make_scene=lambda: SketchHopperScene(on_exit, ctx=ctx),
    )
