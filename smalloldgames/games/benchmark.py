from __future__ import annotations

from smalloldgames.engine.game_registry import GameDefinition
from smalloldgames.engine.scene import SceneContext

from .benchmark_game import BenchmarkScene

__all__ = ["BenchmarkScene", "register_game"]


def register_game(*, ctx: SceneContext, on_exit) -> GameDefinition:
    return GameDefinition(
        id="benchmark",
        title="BENCHMARK",
        subtitle="AUTOMATED STRESS TEST",
        detail="PRESS ENTER TO RUN",
        score_key="benchmark",
        art_variant="benchmark",
        music_track=None,
        make_scene=lambda: BenchmarkScene(on_exit, ctx=ctx),
    )
