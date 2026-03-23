from __future__ import annotations

import random
from collections.abc import Callable

from smalloldgames.engine import GameAction, InputState, Scene, SceneContext, SceneResult, TouchRegion, Transition
from smalloldgames.menus.common import (
    ACCENT,
    BG_BOTTOM,
    BG_TOP,
    GOOD,
    TEXT_LIGHT,
    TEXT_MUTED,
)
from smalloldgames.menus.components import BASE_PANEL, draw_button, draw_panel
from smalloldgames.rendering.primitives import DrawList

from .assets import SNAKE_ATLAS


class SnakeScene:
    grid_size = 20
    cell_size = 24
    grid_offset_x = 30
    grid_offset_y = 240

    def __init__(
        self,
        on_exit: Callable[[], Scene],
        *,
        ctx: SceneContext | None = None,
        seed: int | None = None,
    ) -> None:
        self.exit_scene_factory = on_exit
        self.score_repository = ctx.score_repository if ctx else None
        self.audio = ctx.audio if ctx else None
        self.random = random.Random(seed)
        self.player_name = self._load_player_name()
        self.best_score = self._load_best_score()
        self.sound_enabled = self._load_sound_enabled()
        self.touch_controls_enabled = self._load_touch_controls_enabled()
        self.reset()

    def reset(self) -> None:
        self.snake = [(10, 10), (10, 11), (10, 12)]
        self.direction = (0, -1)
        self.next_direction = (0, -1)
        self.food = self._spawn_food()
        self.score = 0
        self.game_over = False
        self.paused = False
        self.move_timer = 0.0
        self.move_speed = 0.15
        self.score_saved = False

    def update(self, dt: float, inputs: InputState) -> SceneResult:
        if inputs.action_pressed(GameAction.BACK):
            return Transition(self.exit_scene_factory())
        if inputs.action_pressed(GameAction.PAUSE):
            self.paused = not self.paused
            return None
        if inputs.action_pressed(GameAction.RESTART):
            self.reset()
            return None

        if self.game_over:
            if inputs.action_pressed(GameAction.CONFIRM) or (
                inputs.pointer_pressed and inputs.pointer_in_rect(100, 300, 340, 100)
            ):
                self.reset()
            return None

        if self.paused:
            if inputs.action_pressed(GameAction.CONFIRM) or (
                inputs.pointer_pressed and inputs.pointer_in_rect(100, 300, 340, 100)
            ):
                self.paused = False
            return None

        self._handle_input(inputs)

        self.move_timer += dt
        if self.move_timer >= self.move_speed:
            self.move_timer = 0.0
            self._step()

        return None

    def render(self, draw: DrawList) -> None:
        # Background
        draw.gradient_quad(
            0,
            0,
            draw.width,
            draw.height,
            bottom_left=BG_BOTTOM,
            bottom_right=BG_BOTTOM,
            top_right=BG_TOP,
            top_left=BG_TOP,
            world=False,
        )

        # Grid area
        draw_panel(
            draw,
            x=self.grid_offset_x - 4,
            y=self.grid_offset_y - 4,
            width=self.grid_size * self.cell_size + 8,
            height=self.grid_size * self.cell_size + 8,
            style=BASE_PANEL,
        )

        # Food
        fx, fy = self._grid_to_screen(self.food)
        draw.sprite(fx, fy, SNAKE_ATLAS.sprites["food"], width=self.cell_size, height=self.cell_size, world=False)

        # Snake
        for i, pos in enumerate(self.snake):
            sx, sy = self._grid_to_screen(pos)
            sprite_name = "snake_head" if i == 0 else "snake_body"
            draw.sprite(
                sx, sy, SNAKE_ATLAS.sprites[sprite_name], width=self.cell_size, height=self.cell_size, world=False
            )

        # HUD
        draw.text(draw.width * 0.5, 888, "SNAKE CLASSIC", scale=3, color=TEXT_LIGHT, centered=True)
        draw.text(60, 820, f"SCORE: {self.score:04d}", scale=2, color=GOOD)
        best_text = f"BEST: {self.best_score:04d}"
        best_width = draw.measure_text(best_text, scale=2)
        draw.text(draw.width - 60 - best_width, 820, best_text, scale=2, color=ACCENT)

        if self.touch_controls_enabled:
            self._render_touch_controls(draw)

        if self.paused:
            self._render_overlay(draw, "PAUSED", "PRESS P OR TAP TO RESUME")
        elif self.game_over:
            self._render_overlay(draw, "GAME OVER", "PRESS R OR TAP TO RESTART")

    def _step(self) -> None:
        self.direction = self.next_direction
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])

        # Check wall collision
        if new_head[0] < 0 or new_head[0] >= self.grid_size or new_head[1] < 0 or new_head[1] >= self.grid_size:
            self._trigger_game_over()
            return

        # Check self collision
        if new_head in self.snake:
            self._trigger_game_over()
            return

        self.snake.insert(0, new_head)

        if new_head == self.food:
            self.score += 10
            self.food = self._spawn_food()
            self.move_speed = max(0.08, 0.15 - (self.score / 500.0) * 0.07)
            if self.audio:
                self.audio.play("jump")  # Reusing jump as a 'pick up' sound
        else:
            self.snake.pop()

    def _handle_input(self, inputs: InputState) -> None:
        if inputs.action_pressed(GameAction.NAV_UP) and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif inputs.action_pressed(GameAction.NAV_DOWN) and self.direction != (0, 1):
            self.next_direction = (0, -1)
        elif inputs.action_pressed(GameAction.NAV_LEFT) and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif inputs.action_pressed(GameAction.NAV_RIGHT) and self.direction != (-1, 0):
            self.next_direction = (1, 0)

    def _spawn_food(self) -> tuple[int, int]:
        while True:
            pos = (self.random.randint(0, self.grid_size - 1), self.random.randint(0, self.grid_size - 1))
            if pos not in self.snake:
                return pos

    def _grid_to_screen(self, pos: tuple[int, int]) -> tuple[float, float]:
        return (self.grid_offset_x + pos[0] * self.cell_size, self.grid_offset_y + pos[1] * self.cell_size)

    def _trigger_game_over(self) -> None:
        self.game_over = True
        if self.audio:
            self.audio.play("hit")
        self._finalize_score()

    def _finalize_score(self) -> None:
        if self.score_saved or self.score_repository is None:
            return
        self.score_repository.record_score("snake", self.score)
        self.score_saved = True
        self.best_score = self._load_best_score()

    def _load_best_score(self) -> int:
        if self.score_repository is None:
            return 0
        return self.score_repository.best_score("snake")

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

    def _render_overlay(self, draw: DrawList, title: str, subtitle: str) -> None:
        draw.quad(0, 0, draw.width, draw.height, (0, 0, 0, 0.6), world=False)
        draw.text(draw.width * 0.5, 420, title, scale=4, color=TEXT_LIGHT, centered=True)
        draw.text(draw.width * 0.5, 370, subtitle, scale=1.5, color=TEXT_MUTED, centered=True)

    def _render_touch_controls(self, draw: DrawList) -> None:
        # D-pad style touch hints
        draw_button(draw, x=210, y=140, width=120, height=80, label="UP", label_scale=2)
        draw_button(draw, x=210, y=0, width=120, height=80, label="DOWN", label_scale=2)
        draw_button(draw, x=100, y=70, width=110, height=80, label="LEFT", label_scale=2)
        draw_button(draw, x=330, y=70, width=110, height=80, label="RIGHT", label_scale=2)

    def touch_regions(self) -> tuple[TouchRegion, ...]:
        if not self.touch_controls_enabled:
            return ()
        return (
            TouchRegion(210, 140, 120, 80, frozenset({GameAction.NAV_UP})),
            TouchRegion(210, 0, 120, 80, frozenset({GameAction.NAV_DOWN})),
            TouchRegion(100, 70, 110, 80, frozenset({GameAction.NAV_LEFT})),
            TouchRegion(330, 70, 110, 80, frozenset({GameAction.NAV_RIGHT})),
        )

    @staticmethod
    def music_track() -> str | None:
        return "launcher"  # Could add a snake specific track later

    def window_title(self) -> str:
        return f"Small Old Games - Snake - Score {self.score}"

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass
