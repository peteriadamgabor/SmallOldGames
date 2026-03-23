from __future__ import annotations

from collections.abc import Callable
import random

import glfw

from smalloldgames.data.storage import ScoreRepository
from smalloldgames.engine import ComponentListProxy, World
from smalloldgames.engine import InputState
from smalloldgames.engine import Scene
from smalloldgames.engine.audio import AudioEngine
from smalloldgames.rendering.primitives import DrawList

from .config import SketchHopperConfig, load_sketch_hopper_config
from .rendering import SketchHopperRenderingMixin
from .shared import Color, ImpactEffect, Platform, Player, Projectile, Monster, Cloud, Pickup, BlackHole
from .systems import SketchHopperSystemsMixin
from .ui import SketchHopperUIMixin


class SketchHopperScene(SketchHopperSystemsMixin, SketchHopperUIMixin, SketchHopperRenderingMixin):
    world_width = 540.0
    world_height = 960.0
    player_width = 58.0
    player_height = 58.0
    gravity = -1900.0
    move_speed = 315.0
    jump_velocity = 1010.0
    spring_jump_velocity = 1420.0
    platform_width = 92.0
    platform_height = 18.0
    path_max_shift = 126.0
    extra_platform_chance = 0.7
    second_extra_platform_chance = 0.24
    overlap_x_padding = 18.0
    overlap_y_padding = 12.0
    projectile_speed = 820.0
    projectile_cooldown = 0.22
    monster_width = 62.0
    monster_height = 36.0
    cloud_max_parallax = 0.56
    spring_feedback_duration = 0.18
    jetpack_width = 30.0
    jetpack_height = 32.0
    jetpack_velocity = 1380.0
    jetpack_duration = 1.10
    black_hole_size = 74.0
    black_hole_pull_radius = 170.0
    black_hole_pull_strength = 420.0
    min_visible_monsters = 1
    min_visible_pickups = 1
    spring_min_height = 420.0
    moving_platform_min_height = 900.0
    broken_platform_min_height = 1500.0
    pickup_min_height = 760.0
    pickup_top_up_min_camera_y = 520.0
    monster_min_height = 2200.0
    monster_top_up_min_camera_y = 2600.0
    black_hole_min_height = 5200.0
    pickup_spawn_chance_base = 0.012
    pickup_spawn_chance_difficulty = 0.018
    pickup_min_gap_y = 880.0

    def __init__(
        self,
        on_exit: Callable[[], Scene],
        *,
        config: SketchHopperConfig | None = None,
        score_repository: ScoreRepository | None = None,
        audio: AudioEngine | None = None,
        seed: int | None = None,
    ) -> None:
        self.on_exit = on_exit
        self.config = config or load_sketch_hopper_config()
        self.score_repository = score_repository
        self.audio = audio
        self.random = random.Random(seed)
        self._apply_config()
        self.best_score = self._load_best_score()
        self.player_name = self._load_player_name()
        self.sound_enabled = self._load_sound_enabled()
        self.touch_controls_enabled = self._load_touch_controls_enabled()
        self.latest_rank: int | None = None
        self.player_facing_right = True
        self.paused = False
        self.pause_page = "settings"
        self.confirm_reset_defaults = False
        self.balance_index = 0
        self.feedback_text = ""
        self.feedback_timer = 0.0
        self.flash_timer = 0.0
        self.flash_color: Color = (1.0, 1.0, 1.0, 0.0)
        self.shake_amount = 0.0
        self.theme_index = 0
        self.theme_blend_index = 0
        self.theme_transition_timer = 0.0
        self.animation_time = 0.0
        self.player_squash_timer = 0.0
        self.player_stretch_timer = 0.0
        self._set_sound_enabled(self.sound_enabled)
        self.reset()

    def _apply_config(self) -> None:
        for field_name in self.config.__dataclass_fields__:
            setattr(self, field_name, getattr(self.config, field_name))

    @property
    def dynamic_world(self) -> World:
        return self._dynamic_world

    @property
    def projectiles(self) -> ComponentListProxy[Projectile]:
        return self._projectiles

    @projectiles.setter
    def projectiles(self, values: list[Projectile]) -> None:
        self._projectiles.replace(values)

    @property
    def monsters(self) -> ComponentListProxy[Monster]:
        return self._monsters

    @monsters.setter
    def monsters(self, values: list[Monster]) -> None:
        self._monsters.replace(values)

    @property
    def pickups(self) -> ComponentListProxy[Pickup]:
        return self._pickups

    @pickups.setter
    def pickups(self, values: list[Pickup]) -> None:
        self._pickups.replace(values)

    @property
    def black_holes(self) -> ComponentListProxy[BlackHole]:
        return self._black_holes

    @black_holes.setter
    def black_holes(self, values: list[BlackHole]) -> None:
        self._black_holes.replace(values)

    @property
    def clouds(self) -> ComponentListProxy[Cloud]:
        return self._clouds

    @clouds.setter
    def clouds(self, values: list[Cloud]) -> None:
        self._clouds.replace(values)

    @property
    def impact_effects(self) -> ComponentListProxy[ImpactEffect]:
        return self._impact_effects

    @impact_effects.setter
    def impact_effects(self, values: list[ImpactEffect]) -> None:
        self._impact_effects.replace(values)

    def _reset_dynamic_world(self) -> None:
        self._dynamic_world = World()
        self._projectiles = ComponentListProxy(self._dynamic_world, Projectile)
        self._monsters = ComponentListProxy(self._dynamic_world, Monster)
        self._pickups = ComponentListProxy(self._dynamic_world, Pickup)
        self._black_holes = ComponentListProxy(self._dynamic_world, BlackHole)
        self._clouds = ComponentListProxy(self._dynamic_world, Cloud)
        self._impact_effects = ComponentListProxy(self._dynamic_world, ImpactEffect)

    def reset(self) -> None:
        self.player = Player(
            x=self.world_width * 0.5 - self.player_width * 0.5,
            y=self.player_start_y,
            width=self.player_width,
            height=self.player_height,
            velocity_y=self.jump_velocity,
        )
        self.camera_y = 0.0
        self.score = 0
        self.game_over = False
        self.platforms: list[Platform] = []
        self._reset_dynamic_world()
        self.highest_platform_y = 0.0
        self.highest_monster_y = 0.0
        self.highest_ufo_y = 0.0
        self.highest_cloud_y = -90.0
        self.highest_black_hole_y = 0.0
        self.highest_pickup_y = -2000.0
        self.route_x = self.world_width * 0.5 - self.platform_width * 0.5
        self.shot_cooldown = 0.0
        self.jetpack_timer = 0.0
        self.rocket_timer = 0.0
        self.propeller_timer = 0.0
        self.shield_timer = 0.0
        self.boots_charges_left = 0
        self.score_saved = False
        self.latest_rank = None
        self.paused = False
        self.pause_page = "settings"
        self.confirm_reset_defaults = False
        self.feedback_text = ""
        self.feedback_timer = 0.0
        self.flash_timer = 0.0
        self.shake_amount = 0.0
        self.theme_index = self._theme_index_for_height(0.0)
        self.theme_blend_index = self.theme_index
        self.theme_transition_timer = 0.0
        self.animation_time = 0.0
        self.player_squash_timer = 0.0
        self.player_stretch_timer = 0.0
        self._build_initial_clouds()
        self._build_initial_platforms()

    def update(self, dt: float, inputs: InputState) -> Scene | None:
        self.animation_time += dt
        self._tick_feedback(dt)
        if self._pause_tapped(inputs):
            self.paused = not self.paused
            if self.paused:
                self.pause_page = "settings"
            return None
        if inputs.was_pressed(glfw.KEY_P) and not self.game_over:
            self.paused = not self.paused
            if self.paused:
                self.pause_page = "settings"
            return None
        if inputs.was_pressed(glfw.KEY_ESCAPE):
            return self.on_exit()
        if inputs.was_pressed(glfw.KEY_R):
            self.reset()
            return None
        if self.game_over:
            return self._update_game_over_touch(inputs)
        if self.paused:
            return self._update_pause_menu(inputs)

        was_game_over = self.game_over
        move_axis = self._control_move_axis(inputs)
        self.shot_cooldown = max(0.0, self.shot_cooldown - dt)
        if (inputs.was_pressed(glfw.KEY_SPACE) or self._shoot_tapped(inputs)) and self.shot_cooldown <= 0.0:
            self._shoot()
        self._tick_platforms(dt)
        self._tick_monsters(dt)
        self._tick_black_holes(dt)
        self._tick_projectiles(dt)
        self._tick_clouds(dt)
        self._tick_player(dt, move_axis)
        self._handle_pickups()
        self._apply_black_holes(dt)
        self._handle_monster_collisions()
        self._tick_camera()
        self._spawn_clouds()
        self._spawn_platforms()
        self._spawn_black_holes()
        self._spawn_monsters()
        self._spawn_ufos()
        self._spawn_pickups()
        self._trim_clouds()
        self._trim_platforms()
        self._trim_pickups()
        self._trim_black_holes()
        self._trim_monsters()
        self._trim_projectiles()
        self.score = max(self.score, int(self.camera_y))
        self.best_score = max(self.best_score, self.score)
        self._update_theme_progression()

        if self.player.y + self.player.height < self.camera_y - self.game_over_fall_margin:
            self.game_over = True
        if self.game_over and not was_game_over:
            self._finalize_score()
        return None

    def render(self, draw: DrawList) -> None:
        _, sky_low, sky_high, _ = self._current_theme()
        draw.gradient_quad(
            0,
            0,
            draw.width,
            draw.height,
            bottom_left=sky_low,
            bottom_right=sky_low,
            top_right=sky_high,
            top_left=sky_high,
            world=False,
        )
        self._render_clouds(draw)
        draw.set_camera(self.camera_y + self._camera_shake_offset())
        self._render_platforms(draw)
        self._render_pickups(draw)
        self._render_black_holes(draw)
        self._render_monsters(draw)
        self._render_projectiles(draw)
        self._render_impacts(draw)
        self._render_player(draw)
        self._render_hud(draw)
        self._render_feedback(draw)
        if self.touch_controls_enabled:
            self._render_touch_controls(draw)
            self._render_pause_button(draw)
        if self.paused:
            self._render_pause_overlay(draw)
        if self.game_over:
            self._render_game_over(draw)

    @staticmethod
    def music_track() -> str | None:
        return "sketch_hopper"

    def window_title(self) -> str:
        return f"Small Old Games - Sketch Hopper - Score {self.score}"
