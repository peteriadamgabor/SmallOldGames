from __future__ import annotations

import glfw

from smalloldgames.data.storage import ScoreEntry, ScoreRepository, ScoreStats
from smalloldgames.engine import GameDefinition, InputState, Scene
from smalloldgames.rendering.primitives import DrawList

from .common import (
    ACCENT,
    BLACK_HOLE_SPRITE,
    CLOUD_SPRITE,
    GOOD,
    HOPPER_SPRITE,
    MONSTER_SPRITE,
    TEXT_LIGHT,
    TEXT_MUTED,
    draw_menu_background,
)
from .components import BASE_PANEL, draw_button, draw_panel


class LeaderboardScene:
    def __init__(
        self,
        on_back,
        games: tuple[GameDefinition, ...],
        current_game: GameDefinition,
        *,
        score_repository: ScoreRepository | None = None,
    ) -> None:
        self.on_back = on_back
        self.games = games
        self.game = current_game
        self.score_repository = score_repository
        self.editing_name = False
        self.player_name = self._load_player_name()
        self.draft_name = self.player_name
        self._refresh_data()

    def _refresh_data(self) -> None:
        self.top_scores = self._load_top_scores()
        self.stats = self._load_stats()

    def update(self, _: float, inputs: InputState) -> Scene | None:
        if inputs.pointer_pressed:
            if inputs.pointer_in_rect(42, 642, 456, 150):
                self.editing_name = True
                self.draft_name = self.player_name
                return None
            if inputs.pointer_in_rect(42, 120, 210, 72):
                return self.on_back()
            if inputs.pointer_in_rect(288, 120, 210, 72):
                return self.game.make_scene()
            if inputs.pointer_in_rect(42, 860, 60, 60):
                self._cycle_game(-1)
                return None
            if inputs.pointer_in_rect(438, 860, 60, 60):
                self._cycle_game(1)
                return None
        if self.editing_name:
            return self._update_name_editor(inputs)
        if inputs.was_pressed(glfw.KEY_LEFT, glfw.KEY_A):
            self._cycle_game(-1)
        if inputs.was_pressed(glfw.KEY_RIGHT, glfw.KEY_D):
            self._cycle_game(1)
        if inputs.was_pressed(glfw.KEY_ESCAPE, glfw.KEY_BACKSPACE):
            return self.on_back()
        if inputs.was_pressed(glfw.KEY_ENTER, glfw.KEY_SPACE):
            return self.game.make_scene()
        if inputs.was_pressed(glfw.KEY_E):
            self.editing_name = True
            self.draft_name = self.player_name
        return None

    def render(self, draw: DrawList) -> None:
        draw_menu_background(draw)
        self._render_backdrop(draw)

        # Game cycling arrows
        draw.text(64, 874, "<", scale=5, color=ACCENT, centered=True)
        draw.text(476, 874, ">", scale=5, color=ACCENT, centered=True)

        draw.text(draw.width * 0.5, 874, f"{self.game.title}", scale=5, color=TEXT_LIGHT, centered=True)
        draw.text(draw.width * 0.5, 838, "LOCAL SQLITE BOARD", scale=2, color=TEXT_MUTED, centered=True)

        draw_panel(draw, x=42, y=642, width=456, height=150, style=BASE_PANEL)
        draw.text(66, 760, "PLAYER NAME", scale=3, color=TEXT_LIGHT, world=False)
        draw.text(66, 728, self._display_name(), scale=4, color=ACCENT if self.editing_name else GOOD, world=False)
        draw.text(66, 690, self._name_help_text(), scale=2, color=TEXT_MUTED, world=False)
        draw.text(66, 664, "ENTER STARTS GAME   ESC GOES BACK", scale=2, color=TEXT_MUTED, world=False)

        draw_panel(draw, x=42, y=230, width=456, height=388, style=BASE_PANEL)
        draw.text(66, 586, "TOP SCORES", scale=4, color=TEXT_LIGHT, world=False)
        draw.text(284, 586, f"RUNS {self.stats.total_runs:03d}", scale=2, color=TEXT_MUTED, world=False)
        draw.text(284, 564, f"AVG {self.stats.average_score:04d}", scale=2, color=TEXT_MUTED, world=False)
        draw.text(284, 542, f"BEST {self.stats.best_score:05d}", scale=2, color=ACCENT, world=False)

        if not self.top_scores:
            draw.text(draw.width * 0.5, 430, "NO SCORES YET", scale=4, color=ACCENT, centered=True)
            draw.text(draw.width * 0.5, 396, "PLAY A RUN TO CREATE THE BOARD", scale=2, color=TEXT_MUTED, centered=True)
        else:
            row_y = 536
            for index, entry in enumerate(self.top_scores[:8], start=1):
                line = f"{index:02d} {entry.player_name:<10} {entry.score:05d} {entry.short_date}"
                draw.text(66, row_y, line, scale=2, color=TEXT_LIGHT if index <= 3 else TEXT_MUTED, world=False)
                row_y -= 28

        draw_button(draw, x=42, y=120, width=210, height=72, label="BACK", style=BASE_PANEL)
        draw_button(draw, x=288, y=120, width=210, height=72, label="PLAY", label_color=ACCENT, style=BASE_PANEL)

    def _cycle_game(self, direction: int) -> None:
        current_index = 0
        for i, g in enumerate(self.games):
            if g.id == self.game.id:
                current_index = i
                break
        next_index = (current_index + direction) % len(self.games)
        self.game = self.games[next_index]
        self._refresh_data()

    @staticmethod
    def music_track() -> str | None:
        return "launcher"

    def window_title(self) -> str:
        return f"Small Old Games - {self.game.title} Leaderboard"

    def _update_name_editor(self, inputs: InputState) -> Scene | None:
        if inputs.was_pressed(glfw.KEY_ESCAPE):
            self.editing_name = False
            self.draft_name = self.player_name
            return None
        if inputs.was_pressed(glfw.KEY_ENTER):
            self.player_name = self._save_player_name(self.draft_name)
            self.draft_name = self.player_name
            self.editing_name = False
            return None
        if inputs.was_pressed(glfw.KEY_BACKSPACE):
            self.draft_name = self.draft_name[:-1].rstrip()
        for character in _pressed_characters(inputs):
            if len(self.draft_name.replace(" ", "")) >= 10 and character != " ":
                continue
            next_name = f"{self.draft_name}{character}"
            self.draft_name = next_name[:10].upper()
        return None

    def _load_top_scores(self) -> list[ScoreEntry]:
        if self.score_repository is None:
            return []
        return self.score_repository.top_scores(self.game.score_key, limit=8)

    def _load_stats(self) -> ScoreStats:
        if self.score_repository is None:
            return ScoreStats(total_runs=0, average_score=0, best_score=0)
        return self.score_repository.stats(self.game.score_key)

    def _load_player_name(self) -> str:
        if self.score_repository is None:
            return "PLAYER"
        return self.score_repository.get_player_name()

    def _save_player_name(self, player_name: str) -> str:
        if self.score_repository is None:
            return player_name or "PLAYER"
        return self.score_repository.set_player_name(player_name)

    def _display_name(self) -> str:
        return self.draft_name if self.editing_name else self.player_name

    def _name_help_text(self) -> str:
        if self.editing_name:
            return "TYPE A TO Z OR 0 TO 9   ENTER SAVES   ESC CANCELS"
        return "PRESS E OR TAP PANEL TO EDIT THE NAME USED FOR NEW SCORES"

    def _render_backdrop(self, draw: DrawList) -> None:
        draw.sprite(42, 846, CLOUD_SPRITE, width=120, height=56, world=False)
        draw.sprite(378, 828, CLOUD_SPRITE, width=88, height=40, world=False)
        draw.sprite(64, 150, BLACK_HOLE_SPRITE, width=68, height=68, world=False)
        draw.sprite(398, 166, MONSTER_SPRITE, width=74, height=42, world=False)
        draw.sprite(402, 714, HOPPER_SPRITE, width=60, height=60, world=False)


def _pressed_characters(inputs: InputState) -> list[str]:
    characters: list[str] = []
    for key in sorted(inputs.pressed):
        if glfw.KEY_A <= key <= glfw.KEY_Z:
            characters.append(chr(ord("A") + (key - glfw.KEY_A)))
        elif glfw.KEY_0 <= key <= glfw.KEY_9:
            characters.append(chr(ord("0") + (key - glfw.KEY_0)))
        elif key == glfw.KEY_SPACE:
            characters.append(" ")
    return characters
