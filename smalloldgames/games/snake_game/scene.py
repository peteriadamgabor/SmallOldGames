from __future__ import annotations

import random
from collections.abc import Callable

from smalloldgames.engine import GameAction, InputState, Scene, SceneContext, SceneResult, TouchRegion
from smalloldgames.engine.game_state import FLOW_CONTINUE, GameFlowMixin
from smalloldgames.engine.persistence import PersistenceMixin
from smalloldgames.engine.touch import TouchButton, build_touch_regions, render_touch_buttons
from smalloldgames.engine.ui import draw_gradient_background, draw_overlay_panel, draw_score_hud
from smalloldgames.menus.components import BASE_PANEL, draw_panel
from smalloldgames.rendering.primitives import DrawList

from .assets import SNAKE_ATLAS


class SnakeScene(GameFlowMixin, PersistenceMixin):
    _game_name = "snake"
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
        result = self._handle_game_flow(inputs)
        if result is not FLOW_CONTINUE:
            return result

        self._handle_input(inputs)

        self.move_timer += dt
        if self.move_timer >= self.move_speed:
            self.move_timer = 0.0
            self._step()

        return None

    def render(self, draw: DrawList) -> None:
        draw_gradient_background(draw)

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
        draw_score_hud(draw, title="SNAKE CLASSIC", score=self.score, best_score=self.best_score)

        if self.touch_controls_enabled:
            self._render_touch_controls(draw)

        if self.paused:
            draw_overlay_panel(
                draw, title="PAUSED", title_y=420.0, subtitle="PRESS P OR TAP TO RESUME", subtitle_y=370.0,
            )
        elif self.game_over:
            draw_overlay_panel(
                draw, title="GAME OVER", title_y=420.0, subtitle="PRESS R OR TAP TO RESTART", subtitle_y=370.0,
            )

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
        self._play_sound("hit")
        self._finalize_score()

    _TOUCH_LAYOUT = (
        TouchButton(210, 140, 120, 80, "UP", frozenset({GameAction.NAV_UP})),
        TouchButton(210, 0, 120, 80, "DOWN", frozenset({GameAction.NAV_DOWN})),
        TouchButton(100, 70, 110, 80, "LEFT", frozenset({GameAction.NAV_LEFT})),
        TouchButton(330, 70, 110, 80, "RIGHT", frozenset({GameAction.NAV_RIGHT})),
    )

    def _render_touch_controls(self, draw: DrawList) -> None:
        render_touch_buttons(draw, self._TOUCH_LAYOUT)

    def touch_regions(self) -> tuple[TouchRegion, ...]:
        return build_touch_regions(self._TOUCH_LAYOUT, enabled=self.touch_controls_enabled)

    @staticmethod
    def music_track() -> str | None:
        return "launcher"  # Could add a snake specific track later

    def window_title(self) -> str:
        return f"Small Old Games - Snake - Score {self.score}"

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass
