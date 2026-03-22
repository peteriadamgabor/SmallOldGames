from __future__ import annotations

import glfw

from smalloldgames.engine import GameDefinition
from smalloldgames.engine import InputState
from smalloldgames.rendering.primitives import DrawList
from smalloldgames.data.storage import ScoreRepository

from .components import ACTIVE_CARD, IDLE_CARD, draw_panel, draw_play_badge
from .common import (
    ACCENT,
    CLOUD_SPRITE,
    HOPPER_SPRITE,
    MONSTER_SPRITE,
    PLATFORM_MOVING_SPRITE,
    PLATFORM_STABLE_SPRITE,
    TEXT_LIGHT,
    TEXT_MUTED,
    draw_menu_background,
    fit_scale,
)


class LauncherScene:
    def __init__(
        self,
        games: tuple[GameDefinition, ...],
        on_open_leaderboard,
        *,
        score_repository: ScoreRepository | None = None,
    ) -> None:
        self.games = games
        self.on_open_leaderboard = on_open_leaderboard
        self.score_repository = score_repository
        self.selection = 0
        self.player_name = self._load_player_name()
        self.stats_by_game = {game.id: self._load_stats(game.score_key) for game in self.games}

    def update(self, _: float, inputs: InputState) -> object | None:
        if inputs.pointer_pressed:
            for index, game in enumerate(self.games):
                if inputs.pointer_in_rect(*self._game_card_rect(index)):
                    return game.make_scene()
            if inputs.pointer_in_rect(*self._leaderboard_card_rect()):
                return self.on_open_leaderboard(self._selected_game())
        if inputs.was_pressed(glfw.KEY_UP, glfw.KEY_W):
            self.selection = (self.selection - 1) % (len(self.games) + 1)
        if inputs.was_pressed(glfw.KEY_DOWN, glfw.KEY_S):
            self.selection = (self.selection + 1) % (len(self.games) + 1)
        if inputs.was_pressed(glfw.KEY_TAB, glfw.KEY_L):
            return self.on_open_leaderboard(self._selected_game())
        if inputs.was_pressed(glfw.KEY_ENTER, glfw.KEY_SPACE):
            if self.selection < len(self.games):
                return self.games[self.selection].make_scene()
            return self.on_open_leaderboard(self._selected_game())
        if inputs.was_pressed(glfw.KEY_P):
            return self._selected_game().make_scene()
        return None

    def render(self, draw: DrawList) -> None:
        title_scale = fit_scale(draw, "SMALL OLD GAMES", preferred=7, minimum=4, max_width=draw.width - 48)
        subtitle_scale = fit_scale(
            draw,
            "RETRO MOBILE REMAKES IN PYTHON + VULKAN",
            preferred=3,
            minimum=1,
            max_width=draw.width - 44,
        )
        draw_menu_background(draw)
        draw.text(draw.width * 0.5, 826, "SMALL OLD GAMES", scale=title_scale, color=TEXT_LIGHT, centered=True)
        draw.text(
            draw.width * 0.5,
            780,
            "RETRO MOBILE REMAKES IN PYTHON + VULKAN",
            scale=subtitle_scale,
            color=TEXT_MUTED,
            centered=True,
        )

        for index, game in enumerate(self.games):
            stats = self.stats_by_game[game.id]
            self._draw_card(
                draw,
                bottom=self._card_bottom(index),
                title=game.title,
                subtitle=game.subtitle,
                detail=f"{game.detail}   BEST {stats.best_score:05d}",
                active=self.selection == index,
                variant=game.art_variant,
            )

        board_game = self._selected_game()
        board_stats = self.stats_by_game[board_game.id]
        self._draw_card(
            draw,
            bottom=self._card_bottom(len(self.games)),
            title="LOCAL BOARD",
            subtitle=f"PLAYER {self.player_name}",
            detail=f"{board_game.title} BEST {board_stats.best_score:05d} RUNS {board_stats.total_runs:03d}",
            active=self.selection == len(self.games),
            variant="board",
        )

        draw.text(draw.width * 0.5, 170, "ARROWS OR W S SELECT", scale=3, color=TEXT_MUTED, centered=True)
        draw.text(draw.width * 0.5, 138, "ENTER OPENS   TAP CARD OR TAB / L", scale=2, color=ACCENT, centered=True)
        draw.text(draw.width * 0.5, 110, "DURING GAME: A D MOVE   SPACE SHOOTS", scale=2, color=TEXT_MUTED, centered=True)
        draw.text(draw.width * 0.5, 86, "R RESTARTS   ESC RETURNS", scale=2, color=TEXT_MUTED, centered=True)

    @staticmethod
    def music_track() -> str | None:
        return "launcher"

    @staticmethod
    def window_title() -> str:
        return "Small Old Games - Launcher"

    def _draw_card(
        self,
        draw: DrawList,
        *,
        bottom: float,
        title: str,
        subtitle: str,
        detail: str,
        active: bool,
        variant: str,
    ) -> None:
        draw_panel(
            draw,
            x=60,
            y=bottom,
            width=420,
            height=135,
            style=ACTIVE_CARD if active else IDLE_CARD,
            inset=12,
        )
        title_scale = fit_scale(draw, title, preferred=5, minimum=3, max_width=250)
        subtitle_scale = fit_scale(draw, subtitle, preferred=3, minimum=2, max_width=250)
        draw.text(98, bottom + 78, title, scale=title_scale, color=TEXT_LIGHT, world=False)
        draw.text(98, bottom + 48, subtitle, scale=subtitle_scale, color=TEXT_MUTED, world=False)
        draw.text(98, bottom + 23, detail, scale=2, color=ACCENT if active else TEXT_MUTED, world=False)
        self._draw_card_art(draw, bottom=bottom, variant=variant)
        draw_play_badge(draw, x=352, y=bottom + 80, active=active)

    def _draw_card_art(self, draw: DrawList, *, bottom: float, variant: str) -> None:
        if variant == "hopper":
            draw.sprite(330, bottom + 72, CLOUD_SPRITE, width=90, height=42, world=False)
            draw.sprite(316, bottom + 16, PLATFORM_STABLE_SPRITE, width=120, height=28, world=False)
            draw.sprite(350, bottom + 42, HOPPER_SPRITE, width=56, height=56, world=False)
            return
        draw.sprite(334, bottom + 74, CLOUD_SPRITE, width=84, height=38, world=False)
        draw.sprite(314, bottom + 20, PLATFORM_MOVING_SPRITE, width=112, height=26, world=False)
        draw.sprite(346, bottom + 44, MONSTER_SPRITE, width=68, height=38, world=False)

    def _load_player_name(self) -> str:
        if self.score_repository is None:
            return "PLAYER"
        return self.score_repository.get_player_name()

    def _load_stats(self, score_key: str):
        if self.score_repository is None:
            from smalloldgames.data.storage import ScoreStats

            return ScoreStats(total_runs=0, average_score=0, best_score=0)
        return self.score_repository.stats(score_key)

    def _selected_game(self) -> GameDefinition:
        if self.selection < len(self.games):
            return self.games[self.selection]
        return self.games[0]

    @staticmethod
    def _card_bottom(index: int) -> float:
        return 500.0 - index * 185.0

    def _game_card_rect(self, index: int) -> tuple[float, float, float, float]:
        return (60.0, self._card_bottom(index), 420.0, 135.0)

    def _leaderboard_card_rect(self) -> tuple[float, float, float, float]:
        return self._game_card_rect(len(self.games))
