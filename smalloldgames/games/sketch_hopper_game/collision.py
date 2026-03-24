from __future__ import annotations

import math

from smalloldgames.engine.collision import aabb_overlaps_raw
from smalloldgames.engine.physics import wrap_x

from .shared import BlackHole, Monster, Pickup, Projectile


class CollisionSystem:
    def _handle_pickups(self) -> None:
        consumed_entities: list[int] = []
        for entity_id, pickup in self.dynamic_world.components(Pickup).items():
            if aabb_overlaps_raw(
                self.player.x,
                self.player.y,
                self.player.width,
                self.player.height,
                pickup.x,
                pickup.y,
                pickup.width,
                pickup.height,
            ):
                if pickup.kind == "jetpack":
                    self.jetpack_timer = self.jetpack_duration
                    self.rocket_timer = 0.0
                    self.propeller_timer = 0.0
                    self.player.velocity_y = self.jetpack_velocity
                    self._play_sound("jetpack")
                    self._trigger_feedback("JETPACK", (0.33, 0.82, 1.0, 0.92), shake=5.0)
                    self.player_stretch_timer = 0.24
                elif pickup.kind == "rocket":
                    self.rocket_timer = self.rocket_duration
                    self.jetpack_timer = 0.0
                    self.propeller_timer = 0.0
                    self.player.velocity_y = self.rocket_velocity
                    self._play_sound("rocket")
                    self._trigger_feedback("ROCKET", (0.98, 0.62, 0.28, 0.92), shake=7.0)
                    self.player_stretch_timer = 0.28
                elif pickup.kind == "boots":
                    self.boots_charges_left = self.boots_charges
                    self._play_sound("boots")
                    self._trigger_feedback(f"BOOTS {self.boots_charges_left}", (0.98, 0.84, 0.34, 0.92), shake=3.5)
                elif pickup.kind == "shield":
                    self.shield_timer = self.shield_duration
                    self._play_sound("shield")
                    self._trigger_feedback("SHIELD", (0.48, 0.82, 1.0, 0.92), shake=2.5)
                elif pickup.kind == "propeller":
                    self.propeller_timer = self.propeller_duration
                    self.jetpack_timer = 0.0
                    self.rocket_timer = 0.0
                    self.player.velocity_y = self.propeller_velocity
                    self._play_sound("propeller")
                    self._trigger_feedback("PROPELLER", (0.98, 0.84, 0.28, 0.92), shake=4.0)
                    self.player_stretch_timer = 0.18
                self._spawn_impact(
                    pickup.x + pickup.width * 0.5, pickup.y + pickup.height * 0.5, (0.92, 0.94, 0.98, 0.88)
                )
                consumed_entities.append(entity_id)
        for entity_id in consumed_entities:
            self.dynamic_world.remove_entity(entity_id)

    def _apply_black_holes(self, dt: float) -> None:
        player_cx = self.player.x + self.player.width * 0.5
        player_cy = self.player.y + self.player.height * 0.5
        for _, hole in self.dynamic_world.components(BlackHole).items():
            hole_cx = hole.x + hole.width * 0.5
            hole_cy = hole.y + hole.height * 0.5
            dx = hole_cx - player_cx
            dy = hole_cy - player_cy
            distance = math.hypot(dx, dy)
            if distance <= hole.width * 0.28:
                if self._consume_shield("WARP SAVED"):
                    if distance > 0.0:
                        away_x = -dx / distance
                        away_y = -dy / distance
                    else:
                        away_x = 0.0
                        away_y = 1.0
                    escape_distance = (
                        max(self.player.width, self.player.height) * 0.5 + max(hole.width, hole.height) * 0.5 + 12.0
                    )
                    player_cx = hole_cx + away_x * escape_distance
                    player_cy = hole_cy + away_y * escape_distance
                    self.player.x = wrap_x(player_cx - self.player.width * 0.5, self.world_width)
                    self.player.y = player_cy - self.player.height * 0.5
                    continue
                self.game_over = True
                return
            if distance <= 0.0 or distance >= self.black_hole_pull_radius:
                continue
            pull = (1.0 - distance / self.black_hole_pull_radius) * self.black_hole_pull_strength
            self.player.x = wrap_x(self.player.x + (dx / distance) * pull * dt, self.world_width)
            self.player.y += (dy / distance) * pull * dt * 0.75
            player_cx = self.player.x + self.player.width * 0.5
            player_cy = self.player.y + self.player.height * 0.5

    def _handle_monster_collisions(self) -> None:
        for entity_id, monster in self.dynamic_world.components(Monster).items():
            if aabb_overlaps_raw(
                self.player.x,
                self.player.y,
                self.player.width,
                self.player.height,
                monster.x,
                monster.y,
                monster.width,
                monster.height,
            ):
                if self._consume_shield("SHIELD BLOCK"):
                    self.dynamic_world.remove_entity(entity_id)
                    self.score += monster.score_value
                    self._play_sound("shield")
                    return
                self.game_over = True
                return

    def _player_shot_velocity_y(self) -> float:
        return self.projectile_speed + max(0.0, self.player.velocity_y)

    def _shoot(self) -> None:
        self._spawn_projectile_entity(
            Projectile(
                x=self.player.x + self.player.width * 0.5 - 4.0,
                y=self.player.y + self.player.height,
                width=8.0,
                height=18.0,
                velocity_y=self._player_shot_velocity_y(),
            )
        )
        self.shot_cooldown = self.projectile_cooldown
        self._play_sound("shoot")

    def _spawn_enemy_projectile(self, monster: Monster) -> None:
        self._spawn_projectile_entity(
            Projectile(
                x=monster.x + monster.width * 0.5 - 5.0,
                y=monster.y - 10.0,
                width=10.0,
                height=14.0,
                velocity_y=-self.enemy_projectile_speed,
                hostile=True,
            )
        )
        self._play_sound("enemy_shot")
