from __future__ import annotations

import importlib
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from typing import Protocol

from .scene import Scene, SceneContext

SceneFactory = Callable[[], Scene]
SceneExitFactory = Callable[[], Scene]


@dataclass(frozen=True, slots=True)
class GameDefinition:
    id: str
    title: str
    subtitle: str
    detail: str
    score_key: str
    art_variant: str
    music_track: str | None
    make_scene: SceneFactory


class GamePlugin(Protocol):
    def register_game(self, *, ctx: SceneContext, on_exit: SceneExitFactory) -> GameDefinition: ...


def load_game_definition(module_name: str, *, ctx: SceneContext, on_exit: SceneExitFactory) -> GameDefinition:
    module = importlib.import_module(module_name)
    register_game = getattr(module, "register_game", None)
    if register_game is None or not callable(register_game):
        raise TypeError(f"Game module {module_name!r} does not define a callable register_game() hook.")
    return register_game(ctx=ctx, on_exit=on_exit)


class GameRegistry:
    def __init__(self, games: Iterable[GameDefinition]) -> None:
        self._games = tuple(games)
        if not self._games:
            raise ValueError("game registry requires at least one game")
        self._by_id = {game.id: game for game in self._games}
        if len(self._by_id) != len(self._games):
            raise ValueError("game registry requires unique game ids")

    @classmethod
    def from_modules(
        cls,
        module_names: Sequence[str],
        *,
        ctx: SceneContext,
        on_exit: SceneExitFactory,
    ) -> GameRegistry:
        return cls(load_game_definition(module_name, ctx=ctx, on_exit=on_exit) for module_name in module_names)

    def all(self) -> tuple[GameDefinition, ...]:
        return self._games

    def primary(self) -> GameDefinition:
        return self._games[0]

    def get(self, game_id: str) -> GameDefinition:
        try:
            return self._by_id[game_id]
        except KeyError:
            raise KeyError(game_id) from None
