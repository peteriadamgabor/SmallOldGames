from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass

from smalloldgames.engine import GameAction, InputState, Scene, SceneContext, SceneResult, TouchRegion
from smalloldgames.engine.collision import aabb_overlaps_raw
from smalloldgames.engine.game_state import FLOW_CONTINUE, GameFlowMixin
from smalloldgames.engine.particles import EmitterConfig, ParticleEmitter
from smalloldgames.engine.persistence import PersistenceMixin
from smalloldgames.engine.physics import clamp
from smalloldgames.engine.touch import TouchButton, render_touch_buttons
from smalloldgames.engine.ui import draw_gradient_background, draw_overlay_panel, draw_score_hud
from smalloldgames.menus.common import TEXT_MUTED
from smalloldgames.rendering.primitives import DrawList

from .assets import SPACE_INVADERS_ATLAS

# ---------------------------------------------------------------------------
# Sprites
# ---------------------------------------------------------------------------
CANNON_SPRITE = SPACE_INVADERS_ATLAS.sprites["cannon"]
INVADER_A_SPRITE = SPACE_INVADERS_ATLAS.sprites["invader_a"]
INVADER_B_SPRITE = SPACE_INVADERS_ATLAS.sprites["invader_b"]
INVADER_C_SPRITE = SPACE_INVADERS_ATLAS.sprites["invader_c"]
UFO_SPRITE = SPACE_INVADERS_ATLAS.sprites["ufo"]
INVADER_SPRITES = (INVADER_C_SPRITE, INVADER_B_SPRITE, INVADER_A_SPRITE)

# ---------------------------------------------------------------------------
# Colors
# ---------------------------------------------------------------------------
Color = tuple[float, float, float, float]
SHIELD_COLOR: Color = (0.2, 0.85, 0.3, 1.0)
BULLET_COLOR: Color = (1.0, 1.0, 1.0, 1.0)
BOMB_COLOR: Color = (1.0, 0.3, 0.3, 1.0)
LIVES_COLOR: Color = (0.2, 0.85, 0.3, 1.0)
UFO_COLOR: Color = (1.0, 0.2, 0.4, 1.0)

_ALIEN_KILL_PARTICLES = EmitterConfig(
    rate=0.0, life_min=0.15, life_max=0.35, speed_min=40.0, speed_max=100.0,
    angle_min=0.0, angle_max=math.tau, size_min=2.0, size_max=4.0,
    color_start=(0.43, 0.86, 0.54, 1.0), color_end=(0.43, 0.86, 0.54, 0.0),
    gravity=0.0, max_particles=10,
)

_UFO_KILL_PARTICLES = EmitterConfig(
    rate=0.0, life_min=0.2, life_max=0.45, speed_min=50.0, speed_max=120.0,
    angle_min=0.0, angle_max=math.tau, size_min=3.0, size_max=6.0,
    color_start=(1.0, 0.2, 0.4, 1.0), color_end=(1.0, 0.8, 0.2, 0.0),
    gravity=0.0, max_particles=14,
)

_PLAYER_HIT_PARTICLES = EmitterConfig(
    rate=0.0, life_min=0.3, life_max=0.5, speed_min=40.0, speed_max=90.0,
    angle_min=0.0, angle_max=math.tau, size_min=2.0, size_max=5.0,
    color_start=(1.0, 0.3, 0.3, 1.0), color_end=(1.0, 0.3, 0.3, 0.0),
    gravity=-60.0, max_particles=12,
)

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
PLAY_LEFT = 20.0
PLAY_RIGHT = 520.0

ALIEN_COLS = 11
ALIEN_ROWS = 5
ALIEN_W = 30.0
ALIEN_H = 22.0
ALIEN_SPACING_X = 40.0
ALIEN_SPACING_Y = 34.0
ALIEN_STEP_X = 4.0
ALIEN_DROP_Y = 18.0

PLAYER_W = 38.0
PLAYER_H = 25.0
PLAYER_Y = 200.0
PLAYER_SPEED = 280.0

BULLET_W = 3.0
BULLET_H = 10.0
BULLET_SPEED = 500.0

BOMB_W = 3.0
BOMB_H = 10.0
BOMB_SPEED = 180.0

SHIELD_BLOCK = 5.0
SHIELD_Y = 290.0
SHIELD_POSITIONS = (80.0, 195.0, 310.0, 425.0)

UFO_W = 40.0
UFO_H = 20.0
UFO_Y = 770.0
UFO_SPEED = 120.0

BASE_STEP_INTERVAL = 0.7
MIN_STEP_INTERVAL = 0.04
MAX_PLAYER_BULLETS = 1
MAX_ALIEN_BOMBS = 3
BOMB_CHANCE_PER_TICK = 0.008
UFO_INTERVAL_MIN = 12.0
UFO_INTERVAL_MAX = 22.0

ALIEN_POINTS = (10, 20, 30)

INITIAL_GRID_X = 60.0
INITIAL_GRID_Y = 500.0

# Shield block offsets (col, row) — each block is SHIELD_BLOCK px
SHIELD_SHAPE: frozenset[tuple[int, int]] = frozenset(
    [
        (2, 4),
        (3, 4),
        (4, 4),
        (5, 4),
        (6, 4),
        (7, 4),
        (1, 3),
        (2, 3),
        (3, 3),
        (4, 3),
        (5, 3),
        (6, 3),
        (7, 3),
        (8, 3),
        (0, 2),
        (1, 2),
        (2, 2),
        (3, 2),
        (4, 2),
        (5, 2),
        (6, 2),
        (7, 2),
        (8, 2),
        (9, 2),
        (0, 1),
        (1, 1),
        (2, 1),
        (3, 1),
        (4, 1),
        (5, 1),
        (6, 1),
        (7, 1),
        (8, 1),
        (9, 1),
        (0, 0),
        (1, 0),
        (2, 0),
        (7, 0),
        (8, 0),
        (9, 0),
    ]
)


# ---------------------------------------------------------------------------
# Domain objects
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class Alien:
    col: int
    row: int
    alien_type: int
    alive: bool = True


@dataclass(slots=True)
class Bullet:
    x: float
    y: float


@dataclass(slots=True)
class Bomb:
    x: float
    y: float


# ---------------------------------------------------------------------------
# Scene
# ---------------------------------------------------------------------------
class SpaceInvadersScene(GameFlowMixin, PersistenceMixin):
    _game_name = "space_invaders"
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
        self.rng = random.Random(seed)
        self.player_name = self._load_player_name()
        self.best_score = self._load_best_score()
        self.touch_controls_enabled = self._load_touch_controls_enabled()
        self.reset()

    # -----------------------------------------------------------------------
    # State management
    # -----------------------------------------------------------------------
    def reset(self) -> None:
        self.score = 0
        self.lives = 3
        self.wave = 1
        self.game_over = False
        self.paused = False
        self.score_saved = False

        self.player_x = 270.0
        self.player_hit_timer = 0.0

        self.aliens: list[Alien] = []
        self.grid_x = INITIAL_GRID_X
        self.grid_y = INITIAL_GRID_Y
        self.grid_dir = 1.0
        self.step_timer = 0.0
        self.anim_frame = 0

        self.bullets: list[Bullet] = []
        self.bombs: list[Bomb] = []

        self.shields: list[set[tuple[int, int]]] = []

        self.ufo_active = False
        self.ufo_x = 0.0
        self.ufo_dir = 1.0
        self.ufo_timer = 0.0
        self._emitters: list[ParticleEmitter] = []

        self._spawn_wave()

    def _spawn_wave(self) -> None:
        self.aliens.clear()
        self.bullets.clear()
        self.bombs.clear()
        for row in range(ALIEN_ROWS):
            if row <= 1:
                alien_type = 0
            elif row <= 3:
                alien_type = 1
            else:
                alien_type = 2
            for col in range(ALIEN_COLS):
                self.aliens.append(Alien(col=col, row=row, alien_type=alien_type))

        self.grid_x = INITIAL_GRID_X
        self.grid_y = INITIAL_GRID_Y - min(self.wave - 1, 6) * ALIEN_DROP_Y
        self.grid_dir = 1.0
        self.step_timer = 0.0
        self.anim_frame = 0
        self.ufo_active = False
        self.ufo_timer = self.rng.uniform(UFO_INTERVAL_MIN, UFO_INTERVAL_MAX)

        self.shields = [set(SHIELD_SHAPE) for _ in SHIELD_POSITIONS]

    # -----------------------------------------------------------------------
    # Scene protocol
    # -----------------------------------------------------------------------
    def update(self, dt: float, inputs: InputState) -> SceneResult:
        result = self._handle_game_flow(inputs)
        if result is not FLOW_CONTINUE:
            return result

        self._update_player(dt, inputs)
        self._update_bullets(dt)
        self._update_bombs(dt)
        self._update_aliens(dt)
        self._update_ufo(dt)
        self._check_wave_clear()
        self._tick_emitters(dt)
        return None

    def render(self, draw: DrawList) -> None:
        self._render_background(draw)
        self._render_shields(draw)
        self._render_aliens(draw)
        self._render_ufo(draw)
        self._render_player(draw)
        self._render_bullets(draw)
        self._render_bombs(draw)
        self._render_emitters(draw)
        self._render_hud(draw)
        if self.touch_controls_enabled and not self.game_over and not self.paused:
            self._render_touch_controls(draw)
        if self.paused:
            self._render_overlay(draw, "PAUSED", "PRESS P OR TAP TO RESUME")
        elif self.game_over:
            self._render_overlay(draw, "GAME OVER", "PRESS R OR TAP TO RESTART")

    @staticmethod
    def music_track() -> str | None:
        return "space_invaders"

    def window_title(self) -> str:
        return f"Small Old Games - Space Invaders - Score {self.score}"

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    # -----------------------------------------------------------------------
    # Player
    # -----------------------------------------------------------------------
    def _update_player(self, dt: float, inputs: InputState) -> None:
        if self.player_hit_timer > 0.0:
            self.player_hit_timer -= dt
            return

        move = inputs.action_axis(GameAction.MOVE_LEFT, GameAction.MOVE_RIGHT)

        self.player_x += move * PLAYER_SPEED * dt
        self.player_x = clamp(self.player_x, PLAY_LEFT + PLAYER_W * 0.5, PLAY_RIGHT - PLAYER_W * 0.5)

        should_fire = inputs.action_pressed(GameAction.FIRE)

        if should_fire and len(self.bullets) < MAX_PLAYER_BULLETS:
            self.bullets.append(Bullet(x=self.player_x, y=PLAYER_Y + PLAYER_H))
            if self.audio:
                self.audio.play("shoot")

    # -----------------------------------------------------------------------
    # Bullets (player)
    # -----------------------------------------------------------------------
    def _update_bullets(self, dt: float) -> None:
        for bullet in self.bullets[:]:
            bullet.y += BULLET_SPEED * dt
            if bullet.y > 900.0:
                self.bullets.remove(bullet)
                continue
            if self._bullet_vs_aliens(bullet):
                if bullet in self.bullets:
                    self.bullets.remove(bullet)
                continue
            if self._bullet_vs_shields(bullet) and bullet in self.bullets:
                self.bullets.remove(bullet)

    def _bullet_vs_aliens(self, bullet: Bullet) -> bool:
        for alien in self.aliens:
            if not alien.alive:
                continue
            ax = self.grid_x + alien.col * ALIEN_SPACING_X - ALIEN_W * 0.5
            ay = self.grid_y + alien.row * ALIEN_SPACING_Y - ALIEN_H * 0.5
            if aabb_overlaps_raw(
                bullet.x - BULLET_W * 0.5, bullet.y - BULLET_H * 0.5, BULLET_W, BULLET_H,
                ax, ay, ALIEN_W, ALIEN_H,
            ):
                alien.alive = False
                self.score += ALIEN_POINTS[alien.alien_type]
                self._burst(ax + ALIEN_W * 0.5, ay + ALIEN_H * 0.5, _ALIEN_KILL_PARTICLES, 8)
                if self.audio:
                    self.audio.play("hit")
                return True
        return False

    def _bullet_vs_shields(self, bullet: Bullet) -> bool:
        for i, shield in enumerate(self.shields):
            sx = SHIELD_POSITIONS[i]
            for block in list(shield):
                bx = sx + block[0] * SHIELD_BLOCK
                by = SHIELD_Y + block[1] * SHIELD_BLOCK
                if aabb_overlaps_raw(
                    bullet.x - BULLET_W * 0.5, bullet.y - BULLET_H * 0.5, BULLET_W, BULLET_H,
                    bx, by, SHIELD_BLOCK, SHIELD_BLOCK,
                ):
                    shield.discard(block)
                    return True
        return False

    # -----------------------------------------------------------------------
    # Bombs (alien)
    # -----------------------------------------------------------------------
    def _update_bombs(self, dt: float) -> None:
        for bomb in self.bombs[:]:
            bomb.y -= BOMB_SPEED * dt
            if bomb.y < 0.0:
                if bomb in self.bombs:
                    self.bombs.remove(bomb)
                continue
            if self._bomb_vs_player(bomb):
                if bomb in self.bombs:
                    self.bombs.remove(bomb)
                continue
            if self._bomb_vs_shields(bomb) and bomb in self.bombs:
                self.bombs.remove(bomb)

    def _bomb_vs_player(self, bomb: Bomb) -> bool:
        if self.player_hit_timer > 0.0:
            return False
        if aabb_overlaps_raw(
            bomb.x - BOMB_W * 0.5, bomb.y - BOMB_H * 0.5, BOMB_W, BOMB_H,
            self.player_x - PLAYER_W * 0.5, PLAYER_Y, PLAYER_W, PLAYER_H,
        ):
            self._player_killed()
            return True
        return False

    def _bomb_vs_shields(self, bomb: Bomb) -> bool:
        for i, shield in enumerate(self.shields):
            sx = SHIELD_POSITIONS[i]
            for block in list(shield):
                bx = sx + block[0] * SHIELD_BLOCK
                by = SHIELD_Y + block[1] * SHIELD_BLOCK
                if aabb_overlaps_raw(
                    bomb.x - BOMB_W * 0.5, bomb.y - BOMB_H * 0.5, BOMB_W, BOMB_H,
                    bx, by, SHIELD_BLOCK, SHIELD_BLOCK,
                ):
                    shield.discard(block)
                    return True
        return False

    def _player_killed(self) -> None:
        self.lives -= 1
        self.player_hit_timer = 2.0
        self.bombs.clear()
        self._burst(self.player_x, PLAYER_Y + PLAYER_H * 0.5, _PLAYER_HIT_PARTICLES, 12)
        if self.audio:
            self.audio.play("game_over" if self.lives <= 0 else "break")
        if self.lives <= 0:
            self.game_over = True
            self._finalize_score()

    # -----------------------------------------------------------------------
    # Aliens
    # -----------------------------------------------------------------------
    def _update_aliens(self, dt: float) -> None:
        alive_count = sum(1 for a in self.aliens if a.alive)
        if alive_count == 0:
            return

        speed_factor = alive_count / (ALIEN_COLS * ALIEN_ROWS)
        interval = max(MIN_STEP_INTERVAL, BASE_STEP_INTERVAL * speed_factor)

        self.step_timer += dt
        if self.step_timer >= interval:
            self.step_timer -= interval
            self._step_aliens()
            self.anim_frame = 1 - self.anim_frame

        if len(self.bombs) < MAX_ALIEN_BOMBS and self.rng.random() < BOMB_CHANCE_PER_TICK:
            self._alien_fire()

    def _step_aliens(self) -> None:
        min_col, max_col = ALIEN_COLS, -1
        min_row = ALIEN_ROWS
        for alien in self.aliens:
            if alien.alive:
                min_col = min(min_col, alien.col)
                max_col = max(max_col, alien.col)
                min_row = min(min_row, alien.row)

        if max_col < 0:
            return

        next_x = self.grid_x + ALIEN_STEP_X * self.grid_dir
        left_edge = next_x + min_col * ALIEN_SPACING_X - ALIEN_W * 0.5
        right_edge = next_x + max_col * ALIEN_SPACING_X + ALIEN_W * 0.5

        if left_edge < PLAY_LEFT or right_edge > PLAY_RIGHT:
            self.grid_dir = -self.grid_dir
            self.grid_y -= ALIEN_DROP_Y
            lowest_y = self.grid_y + min_row * ALIEN_SPACING_Y - ALIEN_H * 0.5
            if lowest_y <= PLAYER_Y + PLAYER_H:
                self.game_over = True
                self._finalize_score()
        else:
            self.grid_x = next_x

    def _alien_fire(self) -> None:
        alive_aliens = [a for a in self.aliens if a.alive]
        if not alive_aliens:
            return
        columns: dict[int, list[Alien]] = {}
        for alien in alive_aliens:
            columns.setdefault(alien.col, []).append(alien)
        col = self.rng.choice(list(columns.keys()))
        bottom_alien = min(columns[col], key=lambda a: a.row)
        bx = self.grid_x + bottom_alien.col * ALIEN_SPACING_X
        by = self.grid_y + bottom_alien.row * ALIEN_SPACING_Y - ALIEN_H * 0.5
        self.bombs.append(Bomb(x=bx, y=by))
        if self.audio:
            self.audio.play("enemy_shot")

    # -----------------------------------------------------------------------
    # UFO
    # -----------------------------------------------------------------------
    def _update_ufo(self, dt: float) -> None:
        if self.ufo_active:
            self.ufo_x += UFO_SPEED * self.ufo_dir * dt
            if self.ufo_x < -UFO_W or self.ufo_x > 540.0 + UFO_W:
                self.ufo_active = False
                self.ufo_timer = self.rng.uniform(UFO_INTERVAL_MIN, UFO_INTERVAL_MAX)
            for bullet in self.bullets[:]:
                if aabb_overlaps_raw(
                    bullet.x - BULLET_W * 0.5, bullet.y - BULLET_H * 0.5, BULLET_W, BULLET_H,
                    self.ufo_x - UFO_W * 0.5, UFO_Y - UFO_H * 0.5, UFO_W, UFO_H,
                ):
                    ufo_points = self.rng.choice([50, 100, 150, 300])
                    self.score += ufo_points
                    self._burst(self.ufo_x, UFO_Y, _UFO_KILL_PARTICLES, 12)
                    self.ufo_active = False
                    self.ufo_timer = self.rng.uniform(UFO_INTERVAL_MIN, UFO_INTERVAL_MAX)
                    self.bullets.remove(bullet)
                    if self.audio:
                        self.audio.play("ufo_hit")
                    break
        else:
            self.ufo_timer -= dt
            if self.ufo_timer <= 0.0:
                self.ufo_active = True
                self.ufo_dir = self.rng.choice([-1.0, 1.0])
                self.ufo_x = -UFO_W if self.ufo_dir > 0 else 540.0 + UFO_W

    # -----------------------------------------------------------------------
    # Wave clear
    # -----------------------------------------------------------------------
    def _check_wave_clear(self) -> None:
        if self.game_over:
            return
        if any(a.alive for a in self.aliens):
            return
        self.wave += 1
        self._spawn_wave()

    # -----------------------------------------------------------------------
    # Rendering
    # -----------------------------------------------------------------------
    def _render_background(self, draw: DrawList) -> None:
        draw_gradient_background(draw)

    def _render_shields(self, draw: DrawList) -> None:
        for i, shield in enumerate(self.shields):
            sx = SHIELD_POSITIONS[i]
            for block in shield:
                draw.quad(
                    sx + block[0] * SHIELD_BLOCK,
                    SHIELD_Y + block[1] * SHIELD_BLOCK,
                    SHIELD_BLOCK,
                    SHIELD_BLOCK,
                    SHIELD_COLOR,
                    world=False,
                )

    def _render_aliens(self, draw: DrawList) -> None:
        for alien in self.aliens:
            if not alien.alive:
                continue
            ax = self.grid_x + alien.col * ALIEN_SPACING_X - ALIEN_W * 0.5
            ay = self.grid_y + alien.row * ALIEN_SPACING_Y - ALIEN_H * 0.5
            sprite = INVADER_SPRITES[alien.alien_type]
            flip = self.anim_frame == 1
            draw.sprite(ax, ay, sprite, width=ALIEN_W, height=ALIEN_H, world=False, flip_x=flip)

    def _render_ufo(self, draw: DrawList) -> None:
        if not self.ufo_active:
            return
        draw.sprite(
            self.ufo_x - UFO_W * 0.5,
            UFO_Y - UFO_H * 0.5,
            UFO_SPRITE,
            width=UFO_W,
            height=UFO_H,
            world=False,
        )

    def _render_player(self, draw: DrawList) -> None:
        if self.player_hit_timer > 0.0 and int(self.player_hit_timer * 8) % 2 == 0:
            return
        draw.sprite(
            self.player_x - PLAYER_W * 0.5,
            PLAYER_Y,
            CANNON_SPRITE,
            width=PLAYER_W,
            height=PLAYER_H,
            world=False,
        )

    def _render_bullets(self, draw: DrawList) -> None:
        for bullet in self.bullets:
            draw.quad(
                bullet.x - BULLET_W * 0.5,
                bullet.y - BULLET_H * 0.5,
                BULLET_W,
                BULLET_H,
                BULLET_COLOR,
                world=False,
            )

    def _render_bombs(self, draw: DrawList) -> None:
        for bomb in self.bombs:
            draw.quad(
                bomb.x - BOMB_W * 0.5,
                bomb.y - BOMB_H * 0.5,
                BOMB_W,
                BOMB_H,
                BOMB_COLOR,
                world=False,
            )

    def _render_hud(self, draw: DrawList) -> None:
        draw_score_hud(
            draw,
            title="SPACE INVADERS",
            title_y=906.0,
            score=self.score,
            best_score=self.best_score,
            score_y=864.0,
            score_format="05d",
            score_label="SCORE",
            best_label="BEST",
            margin_x=30.0,
            extra_text=f"WAVE {self.wave}",
            extra_y=864.0,
            extra_color=TEXT_MUTED,
        )

        lx = 30.0
        for i in range(self.lives):
            draw.sprite(lx + i * 32, 820, CANNON_SPRITE, width=24.0, height=16.0, world=False)

    # -----------------------------------------------------------------------
    # Particles
    # -----------------------------------------------------------------------
    def _burst(self, x: float, y: float, config: EmitterConfig, count: int) -> None:
        emitter = ParticleEmitter(x=x, y=y, active=False, config=config)
        emitter.burst(count)
        self._emitters.append(emitter)

    def _tick_emitters(self, dt: float) -> None:
        alive: list[ParticleEmitter] = []
        for emitter in self._emitters:
            emitter.tick(dt)
            if emitter.alive:
                alive.append(emitter)
        self._emitters = alive

    def _render_emitters(self, draw: DrawList) -> None:
        for emitter in self._emitters:
            emitter.render(draw, world=False)

    def _on_pause_input(self, inputs: InputState) -> SceneResult:
        if inputs.action_pressed(GameAction.CONFIRM) or (
            self.touch_controls_enabled and inputs.pointer_pressed and inputs.pointer_in_rect(120, 310, 300, 80)
        ):
            self.paused = False
        return None

    def _on_game_over_input(self, inputs: InputState) -> SceneResult:
        if (
            inputs.action_pressed(GameAction.CONFIRM)
            or inputs.action_pressed(GameAction.RESTART)
            or (self.touch_controls_enabled and inputs.pointer_pressed and inputs.pointer_in_rect(120, 310, 300, 80))
        ):
            self.reset()
        return None

    _TOUCH_VISUALS = (
        TouchButton(10, 40, 110, 100, "LEFT", frozenset({GameAction.MOVE_LEFT})),
        TouchButton(420, 40, 110, 100, "RIGHT", frozenset({GameAction.MOVE_RIGHT})),
        TouchButton(190, 40, 160, 100, "FIRE", frozenset({GameAction.FIRE}), label_scale=3),
    )

    def _render_touch_controls(self, draw: DrawList) -> None:
        render_touch_buttons(draw, self._TOUCH_VISUALS)

    def touch_regions(self) -> tuple[TouchRegion, ...]:
        if not self.touch_controls_enabled or self.game_over or self.paused:
            return ()
        return (
            TouchRegion(0, 0, 120, 180, frozenset({GameAction.MOVE_LEFT})),
            TouchRegion(420, 0, 120, 180, frozenset({GameAction.MOVE_RIGHT})),
            TouchRegion(170, 0, 200, 180, frozenset({GameAction.FIRE})),
        )

    def _render_overlay(self, draw: DrawList, title: str, subtitle: str) -> None:
        draw_overlay_panel(
            draw,
            title=title,
            title_y=500.0,
            subtitle=subtitle,
            subtitle_y=416.0,
            score_line=f"SCORE  {self.score:05d}",
            score_y=456.0,
        )

