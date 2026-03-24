from __future__ import annotations

import math

from smalloldgames.engine.particles import EmitterConfig, ParticleEmitter
from smalloldgames.engine.persistence import PersistenceMixin
from smalloldgames.rendering.primitives import DrawList

from .cleanup import CleanupSystem
from .collision import CollisionSystem
from .physics import PhysicsSystem
from .shared import THEMES, BlackHole, Cloud, Color, ImpactEffect, Monster, Pickup
from .spawn import SpawnSystem


class SketchHopperSystemsMixin(SpawnSystem, PhysicsSystem, CollisionSystem, CleanupSystem, PersistenceMixin):
    # --- ECS helpers (used by spawn, physics, collision, cleanup) ---

    def _cloud_components(self) -> list[Cloud]:
        return list(self.dynamic_world.components(Cloud).values())

    def _impact_components(self) -> list[ImpactEffect]:
        return list(self.dynamic_world.components(ImpactEffect).values())

    def _monster_components(self) -> list[Monster]:
        return list(self.dynamic_world.components(Monster).values())

    def _pickup_components(self) -> list[Pickup]:
        return list(self.dynamic_world.components(Pickup).values())

    def _black_hole_components(self) -> list[BlackHole]:
        return list(self.dynamic_world.components(BlackHole).values())

    def _spawn_projectile_entity(self, projectile) -> None:
        self.dynamic_world.create(projectile)

    def _spawn_monster_entity(self, monster: Monster) -> None:
        self.dynamic_world.create(monster)

    def _spawn_pickup_entity(self, pickup: Pickup) -> None:
        self.dynamic_world.create(pickup)

    def _spawn_black_hole_entity(self, hole: BlackHole) -> None:
        self.dynamic_world.create(hole)

    def _spawn_cloud_entity(self, cloud: Cloud) -> None:
        self.dynamic_world.create(cloud)

    def _spawn_impact_entity(self, effect: ImpactEffect) -> None:
        self.dynamic_world.create(effect)

    # --- Difficulty ---

    def _difficulty_at_height(self, height: float) -> float:
        return min(max(height / self.difficulty_ramp_height, 0.0), 1.0)

    # --- Score (extends PersistenceMixin) ---

    def _finalize_score(self) -> None:
        if self.score_saved:
            return
        self.score_saved = True
        self.best_score = max(self.best_score, self.score)
        self._play_sound("game_over")
        if self.score_repository is None or self.score <= 0:
            return
        self.latest_rank = self.score_repository.record_score(
            self._game_name, self.score, player_name=self.player_name,
        )
        self.best_score = self.score_repository.best_score(self._game_name)

    # --- Feedback & effects ---

    def _trigger_feedback(self, text: str, color: Color, *, shake: float = 0.0) -> None:
        self.feedback_text = text
        self.feedback_timer = self.feedback_message_duration
        self.flash_timer = self.effect_flash_duration
        self.flash_color = color
        if shake > 0.0:
            self.camera.add_shake(shake)

    def _spawn_impact(self, x: float, y: float, color: Color, *, text: str = "") -> None:
        self._spawn_impact_entity(
            ImpactEffect(
                x=x,
                y=y,
                timer=0.35,
                duration=0.35,
                color=color,
                text=text,
            )
        )
        self._emit_particles(x, y, color, count=6)

    def _camera_shake_offset(self) -> float:
        return self.camera.offset_y() - self.camera.y

    def _consume_shield(self, text: str) -> bool:
        if self.shield_timer <= 0.0:
            return False
        self.shield_timer = 0.0
        self._trigger_feedback(text, (0.48, 0.82, 1.0, 0.92), shake=4.0)
        self._spawn_impact(
            self.player.x + self.player.width * 0.5, self.player.y + self.player.height * 0.5, (0.48, 0.82, 1.0, 0.92)
        )
        return True

    # --- Particles ---

    def _emit_particles(
        self, x: float, y: float, color: Color, *, count: int = 8, speed: float = 80.0, gravity: float = -200.0,
    ) -> None:
        emitter = ParticleEmitter(
            x=x,
            y=y,
            active=False,
            config=EmitterConfig(
                rate=0.0,
                life_min=0.2,
                life_max=0.5,
                speed_min=speed * 0.5,
                speed_max=speed,
                angle_min=0.0,
                angle_max=math.tau,
                size_min=2.0,
                size_max=4.0,
                color_start=color,
                color_end=(color[0], color[1], color[2], 0.0),
                gravity=gravity,
                max_particles=count,
            ),
        )
        emitter.burst(count)
        self._particle_emitters.append(emitter)

    def _tick_particles(self, dt: float) -> None:
        alive: list[ParticleEmitter] = []
        for emitter in self._particle_emitters:
            emitter.tick(dt)
            if emitter.alive:
                alive.append(emitter)
        self._particle_emitters = alive

    def _render_particles(self, draw: DrawList) -> None:
        for emitter in self._particle_emitters:
            emitter.render(draw, world=True)

    # --- Theme ---

    def _theme_index_for_height(self, height: float) -> int:
        if height >= self.theme_height_3:
            return 3
        if height >= self.theme_height_2:
            return 2
        if height >= self.theme_height_1:
            return 1
        return 0

    def _theme_stage_progress(self) -> float:
        return float(self.theme_index)

    def _update_theme_progression(self) -> None:
        next_theme = self._theme_index_for_height(self.camera_y)
        if next_theme != self.theme_index:
            self.theme_blend_index = self.theme_index
            self.theme_index = next_theme
            self.theme_transition_timer = 0.65
            self._trigger_feedback(THEMES[self.theme_index][0], THEMES[self.theme_index][3], shake=3.0)

    def _current_theme(self) -> tuple[str, Color, Color, Color]:
        current = THEMES[self.theme_index]
        if self.theme_transition_timer <= 0.0:
            return current
        previous = THEMES[self.theme_blend_index]
        mix = 1.0 - self.theme_transition_timer / 0.65
        return (
            current[0],
            self._mix_color(previous[1], current[1], mix),
            self._mix_color(previous[2], current[2], mix),
            self._mix_color(previous[3], current[3], mix),
        )

    @staticmethod
    def _mix_color(a: Color, b: Color, t: float) -> Color:
        return (
            a[0] + (b[0] - a[0]) * t,
            a[1] + (b[1] - a[1]) * t,
            a[2] + (b[2] - a[2]) * t,
            a[3] + (b[3] - a[3]) * t,
        )
