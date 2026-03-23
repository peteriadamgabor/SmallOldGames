from __future__ import annotations

import glfw

from smalloldgames.data.storage import ScoreRepository
from smalloldgames.engine import GameDefinition, InputState, Scene
from smalloldgames.rendering.primitives import DrawList

from .common import (
    ACCENT,
    BLACK_HOLE_SPRITE,
    CANNON_SPRITE,
    CLOUD_SPRITE,
    FOOD_SPRITE,
    GOOD,
    HOPPER_SPRITE,
    INVADER_A_SPRITE,
    INVADER_B_SPRITE,
    MONSTER_SPRITE,
    PLATFORM_MOVING_SPRITE,
    PLATFORM_STABLE_SPRITE,
    SNAKE_BODY_SPRITE,
    SNAKE_HEAD_SPRITE,
    TEXT_LIGHT,
    TEXT_MUTED,
    draw_menu_background,
    fit_scale,
)
from .components import ACTIVE_CARD, IDLE_CARD, draw_panel, draw_play_badge

HERO_RECT = (48.0, 428.0, 444.0, 250.0)
GAME_ROW_X = 48.0
GAME_ROW_Y = 278.0
GAME_ROW_WIDTH = 444.0
GAME_CARD_HEIGHT = 118.0
GAME_CARD_GAP = 24.0
ACTION_ROW_Y = 146.0
ACTION_CARD_WIDTH = 210.0
ACTION_CARD_HEIGHT = 100.0
ACTION_CARD_GAP = 24.0


class LauncherScene:
    def __init__(
        self,
        games: tuple[GameDefinition, ...],
        on_open_leaderboard,
        on_open_settings,
        *,
        score_repository: ScoreRepository | None = None,
    ) -> None:
        self.games = games
        self.on_open_leaderboard = on_open_leaderboard
        self.on_open_settings = on_open_settings
        self.score_repository = score_repository
        self.selection = 0
        self.active_game_selection = 0
        self.player_name = self._load_player_name()
        self.sound_enabled = self._load_sound_enabled()
        self.touch_controls_enabled = self._load_touch_controls_enabled()
        self.stats_by_game = {game.id: self._load_stats(game.score_key) for game in self.games}

    def update(self, _: float, inputs: InputState) -> Scene | None:
        if inputs.pointer_pressed:
            for index in range(self._item_count()):
                if inputs.pointer_in_rect(*self._selection_rect(index)):
                    self._set_selection(index)
                    return self._activate_selection()

        if inputs.was_pressed(glfw.KEY_LEFT, glfw.KEY_A):
            self._move_selection(-1.0, 0.0)
        if inputs.was_pressed(glfw.KEY_RIGHT, glfw.KEY_D):
            self._move_selection(1.0, 0.0)
        if inputs.was_pressed(glfw.KEY_UP, glfw.KEY_W):
            self._move_selection(0.0, 1.0)
        if inputs.was_pressed(glfw.KEY_DOWN, glfw.KEY_S):
            self._move_selection(0.0, -1.0)

        if inputs.was_pressed(glfw.KEY_TAB, glfw.KEY_L):
            self._set_selection(len(self.games))
            return self.on_open_leaderboard(self._active_game())
        if inputs.was_pressed(glfw.KEY_ENTER, glfw.KEY_SPACE):
            return self._activate_selection()
        if inputs.was_pressed(glfw.KEY_P):
            return self._active_game().make_scene()
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
        draw.text(draw.width * 0.5, 834, "SMALL OLD GAMES", scale=title_scale, color=TEXT_LIGHT, centered=True)
        draw.text(
            draw.width * 0.5,
            790,
            "RETRO MOBILE REMAKES IN PYTHON + VULKAN",
            scale=subtitle_scale,
            color=TEXT_MUTED,
            centered=True,
        )

        self._draw_feature_panel(draw)

        for index, game in enumerate(self.games):
            stats = self.stats_by_game[game.id]
            self._draw_game_card(
                draw,
                index=index,
                title=game.title,
                detail=f"BEST {stats.best_score:05d}",
                active=self.selection == index,
                variant=game.art_variant,
            )

        board_game = self._active_game()
        board_stats = self.stats_by_game[board_game.id]
        self._draw_action_card(
            draw,
            x=self._leaderboard_card_rect()[0],
            y=self._leaderboard_card_rect()[1],
            width=ACTION_CARD_WIDTH,
            height=ACTION_CARD_HEIGHT,
            title="LOCAL BOARD",
            detail=f"{board_game.title} {board_stats.total_runs:03d} RUNS",
            active=self.selection == len(self.games),
            variant="board",
        )
        self._draw_action_card(
            draw,
            x=self._settings_card_rect()[0],
            y=self._settings_card_rect()[1],
            width=ACTION_CARD_WIDTH,
            height=ACTION_CARD_HEIGHT,
            title="SETTINGS",
            detail=f"SOUND {'ON' if self.sound_enabled else 'OFF'}",
            active=self.selection == len(self.games) + 1,
            variant="settings",
        )

        draw.text(draw.width * 0.5, 82, "ARROWS / WASD MOVE   ENTER OPENS", scale=3, color=TEXT_MUTED, centered=True)
        draw.text(draw.width * 0.5, 52, "TAB LOCAL BOARD   P QUICK PLAY", scale=2, color=ACCENT, centered=True)

    @staticmethod
    def music_track() -> str | None:
        return "launcher"

    @staticmethod
    def window_title() -> str:
        return "Small Old Games - Launcher"

    def _draw_feature_panel(self, draw: DrawList) -> None:
        x, y, width, height = HERO_RECT
        draw_panel(
            draw,
            x=x,
            y=y,
            width=width,
            height=height,
            style=ACTIVE_CARD if self.selection >= len(self.games) else IDLE_CARD,
            inset=14,
        )

        title, subtitle, detail_lines, status_color, variant = self._feature_copy()
        title_scale = fit_scale(draw, title, preferred=6, minimum=3, max_width=220)
        subtitle_scale = fit_scale(draw, subtitle, preferred=3, minimum=2, max_width=220)
        draw.text(x + 24, y + 196, title, scale=title_scale, color=TEXT_LIGHT, world=False)
        draw.text(x + 24, y + 162, subtitle, scale=subtitle_scale, color=TEXT_MUTED, world=False)
        for index, line in enumerate(detail_lines):
            color = status_color if index == 0 else TEXT_MUTED
            draw.text(x + 24, y + 118 - index * 28, line, scale=2, color=color, world=False)
        self._draw_feature_art(draw, x=x, y=y, variant=variant)

    def _draw_game_card(
        self,
        draw: DrawList,
        *,
        index: int,
        title: str,
        detail: str,
        active: bool,
        variant: str,
    ) -> None:
        x, y, width, height = self._game_card_rect(index)
        draw_panel(
            draw,
            x=x,
            y=y,
            width=width,
            height=height,
            style=ACTIVE_CARD if active else IDLE_CARD,
            inset=10,
        )
        title_scale = fit_scale(draw, title, preferred=3, minimum=2, max_width=width - 24)
        draw.text(x + 14, y + 26, detail, scale=2, color=ACCENT if active else TEXT_MUTED, world=False)
        draw.text(x + 14, y + 50, title, scale=title_scale, color=TEXT_LIGHT, world=False)
        self._draw_tile_art(draw, x=x, y=y, width=width, height=height, variant=variant)
        draw_play_badge(draw, x=x + 22, y=y + height - 34, active=active)

    def _draw_action_card(
        self,
        draw: DrawList,
        *,
        x: float,
        y: float,
        width: float,
        height: float,
        title: str,
        detail: str,
        active: bool,
        variant: str,
    ) -> None:
        draw_panel(
            draw,
            x=x,
            y=y,
            width=width,
            height=height,
            style=ACTIVE_CARD if active else IDLE_CARD,
            inset=10,
        )
        title_scale = fit_scale(draw, title, preferred=4, minimum=2, max_width=width - 104)
        draw.text(x + 20, y + 52, title, scale=title_scale, color=TEXT_LIGHT, world=False)
        draw.text(x + 20, y + 24, detail, scale=2, color=ACCENT if active else TEXT_MUTED, world=False)
        self._draw_action_art(draw, x=x, y=y, variant=variant)

    def _draw_tile_art(self, draw: DrawList, *, x: float, y: float, width: float, height: float, variant: str) -> None:
        center_x = x + width * 0.5
        art_y = y + 78
        if variant == "hopper":
            draw.sprite(center_x - 40, art_y + 8, CLOUD_SPRITE, width=76, height=34, world=False)
            draw.sprite(center_x - 46, art_y - 38, PLATFORM_STABLE_SPRITE, width=92, height=22, world=False)
            draw.sprite(center_x - 20, art_y - 20, HOPPER_SPRITE, width=40, height=40, world=False)
            return
        if variant == "snake" and SNAKE_HEAD_SPRITE and SNAKE_BODY_SPRITE and FOOD_SPRITE:
            draw.sprite(center_x - 34, art_y - 24, SNAKE_BODY_SPRITE, width=28, height=28, world=False)
            draw.sprite(center_x - 6, art_y - 24, SNAKE_HEAD_SPRITE, width=28, height=28, world=False)
            draw.sprite(center_x + 16, art_y + 2, FOOD_SPRITE, width=22, height=22, world=False)
            return
        if variant == "space_invaders" and INVADER_A_SPRITE and INVADER_B_SPRITE and CANNON_SPRITE:
            draw.sprite(center_x - 34, art_y, INVADER_A_SPRITE, width=24, height=16, world=False)
            draw.sprite(center_x - 6, art_y, INVADER_A_SPRITE, width=24, height=16, world=False)
            draw.sprite(center_x - 20, art_y - 24, INVADER_B_SPRITE, width=24, height=16, world=False)
            draw.sprite(center_x - 12, art_y - 52, CANNON_SPRITE, width=26, height=18, world=False)
            return
        draw.sprite(center_x - 20, art_y - 18, HOPPER_SPRITE, width=40, height=40, world=False)

    def _draw_feature_art(self, draw: DrawList, *, x: float, y: float, variant: str) -> None:
        if variant == "hopper":
            draw.sprite(x + 286, y + 168, CLOUD_SPRITE, width=112, height=52, world=False)
            draw.sprite(x + 256, y + 64, PLATFORM_STABLE_SPRITE, width=148, height=34, world=False)
            draw.sprite(x + 304, y + 106, HOPPER_SPRITE, width=76, height=76, world=False)
            return
        if variant == "snake" and SNAKE_HEAD_SPRITE and SNAKE_BODY_SPRITE and FOOD_SPRITE:
            draw.sprite(x + 254, y + 88, SNAKE_BODY_SPRITE, width=54, height=54, world=False)
            draw.sprite(x + 302, y + 88, SNAKE_BODY_SPRITE, width=54, height=54, world=False)
            draw.sprite(x + 350, y + 88, SNAKE_HEAD_SPRITE, width=54, height=54, world=False)
            draw.sprite(x + 326, y + 150, FOOD_SPRITE, width=44, height=44, world=False)
            draw.sprite(x + 278, y + 178, CLOUD_SPRITE, width=112, height=50, world=False)
            return
        if variant == "space_invaders" and INVADER_A_SPRITE and INVADER_B_SPRITE and CANNON_SPRITE:
            draw.sprite(x + 258, y + 178, INVADER_A_SPRITE, width=36, height=24, world=False)
            draw.sprite(x + 304, y + 178, INVADER_A_SPRITE, width=36, height=24, world=False)
            draw.sprite(x + 350, y + 178, INVADER_A_SPRITE, width=36, height=24, world=False)
            draw.sprite(x + 278, y + 138, INVADER_B_SPRITE, width=36, height=24, world=False)
            draw.sprite(x + 324, y + 138, INVADER_B_SPRITE, width=36, height=24, world=False)
            draw.sprite(x + 300, y + 78, CANNON_SPRITE, width=44, height=28, world=False)
            return
        if variant == "board":
            draw.sprite(x + 274, y + 174, CLOUD_SPRITE, width=104, height=46, world=False)
            draw.sprite(x + 256, y + 78, PLATFORM_MOVING_SPRITE, width=136, height=30, world=False)
            draw.sprite(x + 300, y + 112, MONSTER_SPRITE, width=76, height=42, world=False)
            return
        draw.sprite(x + 280, y + 168, CLOUD_SPRITE, width=98, height=42, world=False)
        draw.sprite(x + 308, y + 94, BLACK_HOLE_SPRITE, width=78, height=78, world=False)

    def _draw_action_art(self, draw: DrawList, *, x: float, y: float, variant: str) -> None:
        if variant == "board":
            draw.sprite(x + 140, y + 22, PLATFORM_MOVING_SPRITE, width=54, height=14, world=False)
            draw.sprite(x + 152, y + 34, MONSTER_SPRITE, width=44, height=24, world=False)
            return
        draw.sprite(x + 148, y + 32, BLACK_HOLE_SPRITE, width=46, height=46, world=False)

    def _feature_copy(self) -> tuple[str, str, tuple[str, str, str], tuple[float, float, float, float], str]:
        if self.selection < len(self.games):
            game = self.games[self.selection]
            stats = self.stats_by_game[game.id]
            return (
                game.title,
                game.subtitle,
                (
                    game.detail,
                    f"BEST {stats.best_score:05d}   RUNS {stats.total_runs:03d}",
                    f"AVERAGE {stats.average_score:05d}   PLAYER {self.player_name}",
                ),
                ACCENT,
                game.art_variant,
            )

        if self.selection == len(self.games):
            game = self._active_game()
            stats = self.stats_by_game[game.id]
            return (
                "LOCAL BOARD",
                f"PLAYER {self.player_name}",
                (
                    f"{game.title} SCORE HISTORY",
                    f"BEST {stats.best_score:05d}   RUNS {stats.total_runs:03d}",
                    f"AVERAGE {stats.average_score:05d}   ENTER TO OPEN",
                ),
                GOOD,
                "board",
            )

        return (
            "SETTINGS",
            "PERSISTENT PREFERENCES",
            (
                f"SOUND {'ON' if self.sound_enabled else 'OFF'}",
                f"TOUCH {'ON' if self.touch_controls_enabled else 'OFF'}",
                f"PLAYER NAME {self.player_name}",
            ),
            GOOD,
            "settings",
        )

    def _activate_selection(self) -> Scene | None:
        if self.selection < len(self.games):
            return self._active_game().make_scene()
        if self.selection == len(self.games):
            return self.on_open_leaderboard(self._active_game())
        return self.on_open_settings()

    def _move_selection(self, dx: float, dy: float) -> None:
        current_x, current_y = self._rect_center(self._selection_rect(self.selection))
        best_index = self.selection
        best_score: tuple[float, float] | None = None

        for index in range(self._item_count()):
            if index == self.selection:
                continue
            candidate_x, candidate_y = self._rect_center(self._selection_rect(index))
            offset_x = candidate_x - current_x
            offset_y = candidate_y - current_y
            primary_distance = offset_x * dx + offset_y * dy
            if primary_distance <= 0.0:
                continue
            secondary_distance = abs(offset_x * dy - offset_y * dx)
            score = (secondary_distance, primary_distance)
            if best_score is None or score < best_score:
                best_index = index
                best_score = score

        self._set_selection(best_index)

    def _set_selection(self, index: int) -> None:
        self.selection = index
        if index < len(self.games):
            self.active_game_selection = index

    def _load_player_name(self) -> str:
        if self.score_repository is None:
            return "PLAYER"
        return self.score_repository.get_player_name()

    def _load_sound_enabled(self) -> bool:
        if self.score_repository is None:
            return True
        return self.score_repository.get_sound_enabled()

    def _load_touch_controls_enabled(self) -> bool:
        if self.score_repository is None:
            return True
        return self.score_repository.get_touch_controls_enabled()

    def _load_stats(self, score_key: str):
        if self.score_repository is None:
            from smalloldgames.data.storage import ScoreStats

            return ScoreStats(total_runs=0, average_score=0, best_score=0)
        return self.score_repository.stats(score_key)

    def _active_game(self) -> GameDefinition:
        return self.games[self.active_game_selection]

    def _item_count(self) -> int:
        return len(self.games) + 2

    def _selection_rect(self, index: int) -> tuple[float, float, float, float]:
        if index < len(self.games):
            return self._game_card_rect(index)
        if index == len(self.games):
            return self._leaderboard_card_rect()
        return self._settings_card_rect()

    @staticmethod
    def _rect_center(rect: tuple[float, float, float, float]) -> tuple[float, float]:
        x, y, width, height = rect
        return (x + width * 0.5, y + height * 0.5)

    def _game_card_rect(self, index: int) -> tuple[float, float, float, float]:
        card_width = (GAME_ROW_WIDTH - GAME_CARD_GAP * (len(self.games) - 1)) / len(self.games)
        return (GAME_ROW_X + index * (card_width + GAME_CARD_GAP), GAME_ROW_Y, card_width, GAME_CARD_HEIGHT)

    def _leaderboard_card_rect(self) -> tuple[float, float, float, float]:
        return (GAME_ROW_X, ACTION_ROW_Y, ACTION_CARD_WIDTH, ACTION_CARD_HEIGHT)

    def _settings_card_rect(self) -> tuple[float, float, float, float]:
        return (GAME_ROW_X + ACTION_CARD_WIDTH + ACTION_CARD_GAP, ACTION_ROW_Y, ACTION_CARD_WIDTH, ACTION_CARD_HEIGHT)
