from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from .scene import Scene


@dataclass(frozen=True, slots=True)
class GameDefinition:
    id: str
    title: str
    subtitle: str
    detail: str
    score_key: str
    art_variant: str
    music_track: str | None
    make_scene: Callable[[], Scene]


class GameRegistry:
    def __init__(self, games: Iterable[GameDefinition]) -> None:
        self._games = tuple(games)
        if not self._games:
            raise ValueError("game registry requires at least one game")

    def all(self) -> tuple[GameDefinition, ...]:
        return self._games

    def primary(self) -> GameDefinition:
        return self._games[0]

    def get(self, game_id: str) -> GameDefinition:
        for game in self._games:
            if game.id == game_id:
                return game
        raise KeyError(game_id)
