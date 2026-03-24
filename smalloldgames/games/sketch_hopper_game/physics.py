from __future__ import annotations

import math

from smalloldgames.engine.collision import aabb_overlaps_raw, covered_cells
from smalloldgames.engine.physics import bounce_x, wrap_x

from .shared import BlackHole, Cloud, ImpactEffect, Monster, Projectile


class PhysicsSystem:
    def _tick_platforms(self, dt: float) -> None:
        for platform in self.platforms:
            platform.spring_timer = max(0.0, platform.spring_timer - dt)
            if platform.state_timer > 0.0:
                platform.state_timer = max(0.0, platform.state_timer - dt)
                if platform.kind == "vanish" and platform.state_timer == 0.0:
                    platform.broken = True
            if platform.kind != "moving" or platform.broken:
                continue
            platform.x += platform.velocity_x * dt
            platform.x, platform.velocity_x = bounce_x(
                platform.x, platform.velocity_x, platform.width, 0.0, self.world_width,
            )

    def _tick_monsters(self, dt: float) -> None:
        for _, monster in self.dynamic_world.components(Monster).items():
            monster.x += monster.velocity_x * dt
            monster.x, monster.velocity_x = bounce_x(
                monster.x, monster.velocity_x, monster.width, 0.0, self.world_width,
            )
            if monster.bob_amplitude > 0.0:
                monster.bob_phase += monster.bob_speed * dt
                monster.y = monster.base_y + math.sin(monster.bob_phase) * monster.bob_amplitude
            if monster.kind == "ufo":
                monster.shot_timer = max(0.0, monster.shot_timer - dt)
                if (
                    monster.shot_timer == 0.0
                    and monster.y >= self.ufo_shot_min_height
                    and monster.y > self.player.y + 90.0
                    and abs((monster.x + monster.width * 0.5) - (self.player.x + self.player.width * 0.5)) < 120.0
                ):
                    self._spawn_enemy_projectile(monster)
                    monster.shot_timer = self.random.uniform(self.ufo_shot_interval_min, self.ufo_shot_interval_max)

    def _tick_projectiles(self, dt: float) -> None:
        dead_projectiles: list[int] = []
        dead_monsters: set[int] = set()
        monster_entities = list(self.dynamic_world.components(Monster).items())
        cell_size = self._monster_spatial_cell_size()
        monster_index = self._build_monster_spatial_index(monster_entities, cell_size)
        for entity_id, projectile in self.dynamic_world.components(Projectile).items():
            projectile.y += projectile.velocity_y * dt
            if projectile.hostile:
                if aabb_overlaps_raw(
                    projectile.x,
                    projectile.y,
                    projectile.width,
                    projectile.height,
                    self.player.x,
                    self.player.y,
                    self.player.width,
                    self.player.height,
                ):
                    if self._consume_shield("SHOT BLOCK"):
                        self._play_sound("shield")
                    else:
                        self._play_sound("enemy_shot")
                        self.game_over = True
                    dead_projectiles.append(entity_id)
                continue

            hit = self._find_projectile_target(projectile, monster_index, dead_monsters, cell_size)
            if hit is not None:
                defeated_id, defeated = hit
                dead_monsters.add(defeated_id)
                dead_projectiles.append(entity_id)
                self.score += defeated.score_value
                self._play_sound("ufo_hit" if defeated.kind == "ufo" else "hit")
                self._trigger_feedback(
                    "UFO DOWN" if defeated.kind == "ufo" else "HIT", (0.98, 0.83, 0.28, 0.90), shake=4.5
                )
                self._spawn_impact(
                    defeated.x + defeated.width * 0.5,
                    defeated.y + defeated.height * 0.5,
                    (0.99, 0.82, 0.28, 0.92),
                )
                continue
        for entity_id in dead_projectiles:
            self.dynamic_world.remove_entity(entity_id)
        for entity_id in dead_monsters:
            self.dynamic_world.remove_entity(entity_id)

    def _monster_spatial_cell_size(self) -> float:
        return max(self.monster_width, self.monster_height, self.ufo_width, self.ufo_height)

    def _build_monster_spatial_index(
        self, monster_entities: list[tuple[int, Monster]], cell_size: float
    ) -> dict[tuple[int, int], list[tuple[int, int, Monster]]]:
        # Bucket monsters so projectile checks only touch nearby cells.
        index: dict[tuple[int, int], list[tuple[int, int, Monster]]] = {}
        for order, (entity_id, monster) in enumerate(monster_entities):
            for cell in covered_cells(monster.x, monster.y, monster.width, monster.height, cell_size):
                index.setdefault(cell, []).append((order, entity_id, monster))
        return index

    def _find_projectile_target(
        self,
        projectile: Projectile,
        monster_index: dict[tuple[int, int], list[tuple[int, int, Monster]]],
        dead_monsters: set[int],
        cell_size: float,
    ) -> tuple[int, Monster] | None:
        best_target: tuple[int, int, Monster] | None = None
        seen_monsters: set[int] = set()
        for cell in covered_cells(
            projectile.x, projectile.y, projectile.width, projectile.height, cell_size
        ):
            for order, entity_id, monster in monster_index.get(cell, []):
                if entity_id in dead_monsters or entity_id in seen_monsters:
                    continue
                seen_monsters.add(entity_id)
                if not aabb_overlaps_raw(
                    projectile.x,
                    projectile.y,
                    projectile.width,
                    projectile.height,
                    monster.x,
                    monster.y,
                    monster.width,
                    monster.height,
                ):
                    continue
                if best_target is None or order < best_target[0]:
                    best_target = (order, entity_id, monster)
        if best_target is None:
            return None
        return best_target[1], best_target[2]

    def _tick_clouds(self, dt: float) -> None:
        for _, cloud in self.dynamic_world.components(Cloud).items():
            cloud.x += cloud.drift_x * dt
            if cloud.x > self.world_width + 24.0:
                cloud.x = -cloud.width - 24.0
            elif cloud.x + cloud.width < -24.0:
                cloud.x = self.world_width + 24.0

    def _tick_black_holes(self, dt: float) -> None:
        for _, hole in self.dynamic_world.components(BlackHole).items():
            hole.pulse_phase += hole.pulse_speed * dt

    def _tick_player(self, dt: float, move_axis: float) -> None:
        boost_velocity = 0.0
        if self.rocket_timer > 0.0:
            self.rocket_timer = max(0.0, self.rocket_timer - dt)
            boost_velocity = self.rocket_velocity
        elif self.jetpack_timer > 0.0:
            self.jetpack_timer = max(0.0, self.jetpack_timer - dt)
            boost_velocity = self.jetpack_velocity
        elif self.propeller_timer > 0.0:
            self.propeller_timer = max(0.0, self.propeller_timer - dt)
            boost_velocity = self.propeller_velocity

        if boost_velocity > 0.0:
            self.player.velocity_x = move_axis * self.move_speed * self.jetpack_move_speed_multiplier
            if move_axis != 0.0:
                self.player_facing_right = move_axis > 0.0
            self.player.x = wrap_x(self.player.x + self.player.velocity_x * dt, self.world_width)
            self.player.velocity_y = boost_velocity
            self.player.y += self.player.velocity_y * dt
            return
        previous_bottom = self.player.y
        self.player.velocity_x = move_axis * self.move_speed
        if move_axis != 0.0:
            self.player_facing_right = move_axis > 0.0
        self.player.x = wrap_x(self.player.x + self.player.velocity_x * dt, self.world_width)
        self.player.velocity_y += self.gravity * dt
        self.player.y += self.player.velocity_y * dt

        if self.player.velocity_y > 0.0:
            return

        for platform in reversed(self.platforms):
            if platform.broken:
                continue
            top = platform.y + platform.height
            if previous_bottom < top or self.player.y > top:
                continue
            if self.player.x + self.player.width < platform.x:
                continue
            if self.player.x > platform.x + platform.width:
                continue
            if platform.kind == "broken":
                platform.broken = True
                platform.state_timer = 0.12
                self._trigger_feedback("BROKEN", (0.79, 0.44, 0.18, 0.92), shake=4.0)
                self._spawn_impact(
                    platform.x + platform.width * 0.5, platform.y + platform.height * 0.5, (0.79, 0.44, 0.18, 0.92)
                )
                return
            if platform.kind == "fake":
                platform.broken = True
                platform.state_timer = 0.12
                self._play_sound("break")
                self._trigger_feedback("FAKE!", (0.95, 0.54, 0.20, 0.92), shake=5.5)
                self._spawn_impact(
                    platform.x + platform.width * 0.5, platform.y + platform.height * 0.5, (0.95, 0.54, 0.20, 0.92)
                )
                return
            self.player.y = top
            if platform.kind == "spring":
                platform.spring_timer = self.spring_feedback_duration
                self.player.velocity_y = self.spring_jump_velocity
                self._play_sound("spring")
                self._trigger_feedback("SPRING", (0.98, 0.90, 0.34, 0.92), shake=5.0)
                self.player_stretch_timer = 0.18
            elif platform.kind == "trampoline":
                platform.spring_timer = self.spring_feedback_duration
                self.player.velocity_y = self.trampoline_jump_velocity
                self._play_sound("trampoline")
                self._trigger_feedback("TRAMPOLINE", (0.96, 0.74, 0.28, 0.92), shake=6.0)
                self.player_stretch_timer = 0.22
            else:
                if self.boots_charges_left > 0:
                    self.boots_charges_left -= 1
                    self.player.velocity_y = self.boots_jump_velocity
                    self._play_sound("boots")
                    self._trigger_feedback(f"BOOTS {self.boots_charges_left}", (0.98, 0.84, 0.34, 0.92), shake=4.0)
                    self.player_stretch_timer = 0.16
                else:
                    self.player.velocity_y = self.jump_velocity
                    self._play_sound("jump")
                if platform.kind == "vanish":
                    platform.state_timer = 0.08
                    self._trigger_feedback("VANISH", (0.80, 0.86, 1.0, 0.88), shake=3.0)
                self.player_squash_timer = 0.14
            return

    def _tick_camera(self) -> None:
        self.camera.follow_y(self.player.y)

    def _tick_feedback(self, dt: float) -> None:
        self.feedback_timer = max(0.0, self.feedback_timer - dt)
        if self.feedback_timer == 0.0:
            self.feedback_text = ""
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.camera.tick(dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.player_squash_timer = max(0.0, self.player_squash_timer - dt)
        self.player_stretch_timer = max(0.0, self.player_stretch_timer - dt)
        self.theme_transition_timer = max(0.0, self.theme_transition_timer - dt)
        dead_entities: list[int] = []
        for entity_id, effect in self.dynamic_world.components(ImpactEffect).items():
            effect.timer = max(0.0, effect.timer - dt)
            if effect.timer == 0.0:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)
