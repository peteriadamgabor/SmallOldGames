from __future__ import annotations

import math

from smalloldgames.engine import Lifetime, Position, Size, Velocity

from .shared import BlackHole, Cloud, Color, ImpactEffect, Monster, Pickup, Platform, Projectile, THEMES


class SketchHopperSystemsMixin:
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

    def _ensure_projectile_components(self) -> None:
        positions = self.dynamic_world.components(Position)
        velocities = self.dynamic_world.components(Velocity)
        sizes = self.dynamic_world.components(Size)
        for entity_id, projectile in self.dynamic_world.components(Projectile).items():
            if entity_id not in positions:
                self.dynamic_world.add_component(entity_id, Position(projectile.x, projectile.y))
            if entity_id not in velocities:
                self.dynamic_world.add_component(entity_id, Velocity(vy=projectile.velocity_y))
            if entity_id not in sizes:
                self.dynamic_world.add_component(entity_id, Size(projectile.width, projectile.height))

    def _ensure_monster_components(self) -> None:
        positions = self.dynamic_world.components(Position)
        velocities = self.dynamic_world.components(Velocity)
        sizes = self.dynamic_world.components(Size)
        for entity_id, monster in self.dynamic_world.components(Monster).items():
            if entity_id not in positions:
                self.dynamic_world.add_component(entity_id, Position(monster.x, monster.y))
            if entity_id not in velocities:
                self.dynamic_world.add_component(entity_id, Velocity(vx=monster.velocity_x))
            if entity_id not in sizes:
                self.dynamic_world.add_component(entity_id, Size(monster.width, monster.height))

    def _ensure_pickup_components(self) -> None:
        positions = self.dynamic_world.components(Position)
        sizes = self.dynamic_world.components(Size)
        for entity_id, pickup in self.dynamic_world.components(Pickup).items():
            if entity_id not in positions:
                self.dynamic_world.add_component(entity_id, Position(pickup.x, pickup.y))
            if entity_id not in sizes:
                self.dynamic_world.add_component(entity_id, Size(pickup.width, pickup.height))

    def _ensure_black_hole_components(self) -> None:
        positions = self.dynamic_world.components(Position)
        sizes = self.dynamic_world.components(Size)
        for entity_id, hole in self.dynamic_world.components(BlackHole).items():
            if entity_id not in positions:
                self.dynamic_world.add_component(entity_id, Position(hole.x, hole.y))
            if entity_id not in sizes:
                self.dynamic_world.add_component(entity_id, Size(hole.width, hole.height))

    def _ensure_cloud_components(self) -> None:
        positions = self.dynamic_world.components(Position)
        velocities = self.dynamic_world.components(Velocity)
        for entity_id, cloud in self.dynamic_world.components(Cloud).items():
            if entity_id not in positions:
                self.dynamic_world.add_component(entity_id, Position(cloud.x, cloud.y))
            if entity_id not in velocities:
                self.dynamic_world.add_component(entity_id, Velocity(vx=cloud.drift_x))

    def _ensure_impact_components(self) -> None:
        positions = self.dynamic_world.components(Position)
        lifetimes = self.dynamic_world.components(Lifetime)
        for entity_id, effect in self.dynamic_world.components(ImpactEffect).items():
            if entity_id not in positions:
                self.dynamic_world.add_component(entity_id, Position(effect.x, effect.y))
            if entity_id not in lifetimes:
                self.dynamic_world.add_component(entity_id, Lifetime(effect.timer))

    def _spawn_projectile_entity(self, projectile: Projectile) -> None:
        self.dynamic_world.create(
            projectile,
            Position(projectile.x, projectile.y),
            Size(projectile.width, projectile.height),
            Velocity(vy=projectile.velocity_y),
        )

    def _spawn_monster_entity(self, monster: Monster) -> None:
        self.dynamic_world.create(
            monster,
            Position(monster.x, monster.y),
            Size(monster.width, monster.height),
            Velocity(vx=monster.velocity_x),
        )

    def _spawn_pickup_entity(self, pickup: Pickup) -> None:
        self.dynamic_world.create(
            pickup,
            Position(pickup.x, pickup.y),
            Size(pickup.width, pickup.height),
        )

    def _spawn_black_hole_entity(self, hole: BlackHole) -> None:
        self.dynamic_world.create(
            hole,
            Position(hole.x, hole.y),
            Size(hole.width, hole.height),
        )

    def _spawn_cloud_entity(self, cloud: Cloud) -> None:
        self.dynamic_world.create(
            cloud,
            Position(cloud.x, cloud.y),
            Velocity(vx=cloud.drift_x),
        )

    def _spawn_impact_entity(self, effect: ImpactEffect) -> None:
        self.dynamic_world.create(
            effect,
            Position(effect.x, effect.y),
            Lifetime(effect.timer),
        )

    def _build_initial_platforms(self) -> None:
        y = self.initial_platform_start_y
        route_x = self.route_x
        while y <= self.initial_platform_end_y:
            if y > self.initial_platform_start_y:
                route_x = self._clamp_platform_x(route_x + self.random.uniform(-self.initial_route_shift, self.initial_route_shift))
            self.platforms.append(
                Platform(
                    x=route_x,
                    y=y,
                    width=self.platform_width,
                    height=self.platform_height,
                    kind="stable",
                    anchor=True,
                )
            )
            difficulty = self._difficulty_at_height(y)
            self._maybe_add_pickup(self.platforms[-1], difficulty)
            self._spawn_extra_platforms(base_y=y, main_x=route_x, difficulty=difficulty, allow_broken=False)
            self.highest_platform_y = y
            y += self.random.uniform(self.initial_platform_gap_min, self.initial_platform_gap_max)
        self.platforms[0].x = self.world_width * 0.5 - self.platform_width * 0.5
        self.route_x = self.platforms[-1].x
    def _build_initial_clouds(self) -> None:
        target_height = self.world_height + 340.0
        while self.highest_cloud_y < target_height:
            self._append_cloud_band()
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
            if platform.x <= 0.0:
                platform.x = 0.0
                platform.velocity_x *= -1.0
            if platform.x + platform.width >= self.world_width:
                platform.x = self.world_width - platform.width
                platform.velocity_x *= -1.0
    def _tick_monsters(self, dt: float) -> None:
        self._ensure_monster_components()
        for _, monster, position, velocity, size in self.dynamic_world.query(Monster, Position, Velocity, Size):
            position.x += velocity.vx * dt
            if position.x <= 0.0:
                position.x = 0.0
                velocity.vx *= -1.0
            if position.x + size.width >= self.world_width:
                position.x = self.world_width - size.width
                velocity.vx *= -1.0
            if monster.bob_amplitude > 0.0:
                monster.bob_phase += monster.bob_speed * dt
                position.y = monster.base_y + math.sin(monster.bob_phase) * monster.bob_amplitude
            if monster.kind == "ufo":
                monster.shot_timer = max(0.0, monster.shot_timer - dt)
                if (
                    monster.shot_timer == 0.0
                    and position.y >= self.ufo_shot_min_height
                    and position.y > self.player.y + 90.0
                    and abs((position.x + size.width * 0.5) - (self.player.x + self.player.width * 0.5)) < 120.0
                ):
                    monster.x = position.x
                    monster.y = position.y
                    monster.width = size.width
                    monster.height = size.height
                    monster.velocity_x = velocity.vx
                    self._spawn_enemy_projectile(monster)
                    monster.shot_timer = self.random.uniform(self.ufo_shot_interval_min, self.ufo_shot_interval_max)
            monster.x = position.x
            monster.y = position.y
            monster.width = size.width
            monster.height = size.height
            monster.velocity_x = velocity.vx
    def _tick_projectiles(self, dt: float) -> None:
        self._ensure_projectile_components()
        surviving_monsters = list(self.monsters)
        dead_projectiles: list[int] = []
        for entity_id, projectile, position, velocity in self.dynamic_world.query(Projectile, Position, Velocity):
            position.y += velocity.vy * dt
            projectile.x = position.x
            projectile.y = position.y
            projectile.velocity_y = velocity.vy
            if projectile.hostile:
                if self._intersects(
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

            hit_index = next(
                (
                    index
                    for index, monster in enumerate(surviving_monsters)
                    if self._intersects(
                        projectile.x,
                        projectile.y,
                        projectile.width,
                        projectile.height,
                        monster.x,
                        monster.y,
                        monster.width,
                        monster.height,
                    )
                ),
                None,
            )
            if hit_index is not None:
                defeated = surviving_monsters.pop(hit_index)
                dead_projectiles.append(entity_id)
                self.score += defeated.score_value
                self._play_sound("ufo_hit" if defeated.kind == "ufo" else "hit")
                self._trigger_feedback("UFO DOWN" if defeated.kind == "ufo" else "HIT", (0.98, 0.83, 0.28, 0.90), shake=4.5)
                self._spawn_impact(
                    defeated.x + defeated.width * 0.5,
                    defeated.y + defeated.height * 0.5,
                    (0.99, 0.82, 0.28, 0.92),
                )
                continue
        for entity_id in dead_projectiles:
            self.dynamic_world.remove_entity(entity_id)
        self.monsters = surviving_monsters
    def _tick_clouds(self, dt: float) -> None:
        self._ensure_cloud_components()
        for _, cloud, position, velocity in self.dynamic_world.query(Cloud, Position, Velocity):
            position.x += velocity.vx * dt
            if position.x > self.world_width + 24.0:
                position.x = -cloud.width - 24.0
            elif position.x + cloud.width < -24.0:
                position.x = self.world_width + 24.0
            cloud.x = position.x
            cloud.y = position.y
    def _tick_black_holes(self, dt: float) -> None:
        self._ensure_black_hole_components()
        for _, hole, position, size in self.dynamic_world.query(BlackHole, Position, Size):
            hole.pulse_phase += hole.pulse_speed * dt
            hole.x = position.x
            hole.y = position.y
            hole.width = size.width
            hole.height = size.height
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
            self.player.x = (self.player.x + self.player.velocity_x * dt) % self.world_width
            self.player.velocity_y = boost_velocity
            self.player.y += self.player.velocity_y * dt
            return
        previous_bottom = self.player.y
        self.player.velocity_x = move_axis * self.move_speed
        if move_axis != 0.0:
            self.player_facing_right = move_axis > 0.0
        self.player.x = (self.player.x + self.player.velocity_x * dt) % self.world_width
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
                self._spawn_impact(platform.x + platform.width * 0.5, platform.y + platform.height * 0.5, (0.79, 0.44, 0.18, 0.92))
                return
            if platform.kind == "fake":
                platform.broken = True
                platform.state_timer = 0.12
                self._play_sound("break")
                self._trigger_feedback("FAKE!", (0.95, 0.54, 0.20, 0.92), shake=5.5)
                self._spawn_impact(platform.x + platform.width * 0.5, platform.y + platform.height * 0.5, (0.95, 0.54, 0.20, 0.92))
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
        self.camera_y = max(self.camera_y, self.player.y - self.world_height * self.camera_follow_offset)
    def _spawn_platforms(self) -> None:
        target_height = self.camera_y + self.world_height + self.platform_spawn_ahead
        stage_bonus = self._theme_stage_progress() * self.theme_platform_gap_bonus
        while self.highest_platform_y < target_height:
            self.highest_platform_y += self.random.uniform(
                self.platform_spawn_gap_min + stage_bonus * 0.4,
                self.platform_spawn_gap_max + stage_bonus,
            )
            difficulty = self._difficulty_at_height(self.highest_platform_y)
            main_x = self._clamp_platform_x(self.route_x + self.random.uniform(-self.path_max_shift, self.path_max_shift))
            main_kind = self._choose_anchor_kind(self.highest_platform_y, difficulty)
            main_velocity = 0.0
            if main_kind == "moving":
                main_velocity = self.random.choice((-1.0, 1.0)) * self.random.uniform(
                    self.anchor_moving_speed_min,
                    self.anchor_moving_speed_max,
                )
            self.platforms.append(
                Platform(
                    x=main_x,
                    y=self.highest_platform_y,
                    width=self.platform_width,
                    height=self.platform_height,
                    kind=main_kind,
                    velocity_x=main_velocity,
                    anchor=True,
                )
            )
            self._maybe_add_pickup(self.platforms[-1], difficulty)
            self.route_x = main_x
            self._spawn_extra_platforms(base_y=self.highest_platform_y, main_x=main_x, difficulty=difficulty, allow_broken=True)
    def _spawn_clouds(self) -> None:
        target_height = self.camera_y * self.cloud_max_parallax + self.world_height + 240.0
        while self.highest_cloud_y < target_height:
            self._append_cloud_band()
    def _spawn_monsters(self) -> None:
        target_height = self.camera_y + self.world_height + 220.0
        stage_bonus = self._theme_stage_progress() * self.theme_monster_spawn_bonus
        while self.highest_monster_y < target_height:
            self.highest_monster_y += self.random.uniform(self.monster_spawn_gap_min, self.monster_spawn_gap_max)
            if self.highest_monster_y < self.monster_min_height:
                continue
            if self.random.random() > min(0.96, self.monster_spawn_chance + stage_bonus):
                continue
            self._append_monster(self.highest_monster_y, kind="monster")

        self._ensure_monster_components()
        visible_monsters = [
            monster
            for monster in self._monster_components()
            if self.camera_y + self.monster_visible_min_offset
            <= monster.y
            <= self.camera_y + self.world_height + self.monster_visible_max_offset
        ]
        if self.camera_y < self.monster_top_up_min_camera_y:
            return

        attempts = 0
        while len(visible_monsters) < self.min_visible_monsters and attempts < self.monster_top_up_attempts:
            attempts += 1
            y = self.camera_y + self.world_height * self.monster_top_up_start_ratio + attempts * self.monster_top_up_step_y
            self.highest_monster_y = max(self.highest_monster_y, y)
            self._append_monster(y, kind="monster")
            self._ensure_monster_components()
            visible_monsters = [
                monster
                for monster in self._monster_components()
                if self.camera_y + self.monster_visible_min_offset
                <= monster.y
                <= self.camera_y + self.world_height + self.monster_visible_max_offset
            ]
    def _spawn_black_holes(self) -> None:
        target_height = self.camera_y + self.world_height + 260.0
        stage_bonus = self._theme_stage_progress() * self.theme_black_hole_spawn_bonus
        while self.highest_black_hole_y < target_height:
            self.highest_black_hole_y += self.random.uniform(self.black_hole_spawn_gap_min, self.black_hole_spawn_gap_max)
            if self.highest_black_hole_y < self.black_hole_min_height:
                continue
            if self.random.random() > min(0.94, self.black_hole_spawn_chance + stage_bonus):
                continue
            side_left = self.random.random() < 0.5
            x = self.random.uniform(18.0, 94.0) if side_left else self.random.uniform(372.0, 448.0)
            self._spawn_black_hole_entity(
                BlackHole(
                    x=x,
                    y=self.highest_black_hole_y,
                    width=self.black_hole_size,
                    height=self.black_hole_size,
                    pulse_phase=self.random.uniform(0.0, math.tau),
                    pulse_speed=self.random.uniform(1.6, 2.5),
                )
            )
    def _spawn_ufos(self) -> None:
        target_height = self.camera_y + self.world_height + 320.0
        while self.highest_ufo_y < target_height:
            self.highest_ufo_y += self.random.uniform(self.ufo_spawn_gap_min, self.ufo_spawn_gap_max)
            if self.highest_ufo_y < self.ufo_min_height:
                continue
            if self.random.random() > self.ufo_spawn_chance:
                continue
            self._append_monster(self.highest_ufo_y, kind="ufo")
    def _choose_anchor_kind(self, height: float, difficulty: float) -> str:
        roll = self.random.random()
        if height >= self.spring_min_height and roll < self.anchor_spring_chance_base + self.anchor_spring_chance_difficulty * difficulty:
            return "spring"
        if height >= self.moving_platform_min_height and roll < self.anchor_moving_chance_base + self.anchor_moving_chance_difficulty * difficulty:
            return "moving"
        return "stable"
    def _choose_extra_kind(self, height: float, difficulty: float) -> str:
        roll = self.random.random()
        if height >= self.broken_platform_min_height and roll < self.extra_broken_chance_base + self.extra_broken_chance_difficulty * difficulty:
            return "broken"
        if height >= self.fake_platform_min_height and roll < self.extra_fake_chance_base + self.extra_fake_chance_difficulty * difficulty:
            return "fake"
        if height >= self.vanish_platform_min_height and roll < self.extra_vanish_chance_base + self.extra_vanish_chance_difficulty * difficulty:
            return "vanish"
        if height >= self.trampoline_min_height and roll < self.extra_trampoline_chance_base + self.extra_trampoline_chance_difficulty * difficulty:
            return "trampoline"
        if height >= self.moving_platform_min_height and roll < self.extra_moving_chance_base + self.extra_moving_chance_difficulty * difficulty:
            return "moving"
        if height >= self.spring_min_height and roll < self.extra_spring_chance_base + self.extra_spring_chance_difficulty * difficulty:
            return "spring"
        return "stable"
    def _clamp_platform_x(self, value: float) -> float:
        return max(0.0, min(self.world_width - self.platform_width, value))
    def _find_monster_x(self, y: float, width: float) -> float:
        for _ in range(8):
            x = self.random.uniform(0.0, self.world_width - width)
            near_platform = any(
                abs((platform.x + platform.width * 0.5) - (x + width * 0.5)) < self.monster_avoid_platform_x
                and abs(platform.y - y) < self.monster_avoid_platform_y
                for platform in self.platforms
            )
            if not near_platform:
                return x
        return self.random.uniform(0.0, self.world_width - width)
    def _spawn_extra_platforms(self, *, base_y: float, main_x: float, difficulty: float, allow_broken: bool) -> None:
        if self.random.random() < self.extra_platform_chance:
            self._try_add_extra_platform(base_y=base_y, main_x=main_x, difficulty=difficulty, allow_broken=allow_broken)
        if self.random.random() < self.second_extra_platform_chance:
            self._try_add_extra_platform(base_y=base_y, main_x=main_x, difficulty=difficulty, allow_broken=allow_broken)
    def _append_cloud_band(self) -> None:
        self.highest_cloud_y += self.random.uniform(92.0, 154.0)
        base_y = self.highest_cloud_y
        count = 1
        if self.random.random() < 0.7:
            count += 1
        if self.random.random() < 0.25:
            count += 1

        attempts = 0
        band_clouds: list[Cloud] = []
        while len(band_clouds) < count and attempts < 10:
            attempts += 1
            width = self.random.uniform(96.0, 156.0)
            height = width * self.random.uniform(0.38, 0.52)
            x = self.random.uniform(-16.0, self.world_width - width + 16.0)
            y = base_y + self.random.uniform(-18.0, 18.0)
            if any(abs(existing.x - x) < (existing.width * 0.55 + width * 0.55) for existing in band_clouds):
                continue
            band_clouds.append(
                Cloud(
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    parallax=self.random.uniform(0.26, self.cloud_max_parallax),
                    drift_x=self.random.choice((-1.0, 1.0)) * self.random.uniform(4.0, 11.0),
                )
            )
        for cloud in band_clouds:
            self._spawn_cloud_entity(cloud)
    def _append_monster(self, y: float, *, kind: str) -> None:
        bobbing = kind == "monster" and self.random.random() < self.monster_bob_chance
        base_y = y + self.random.uniform(-self.monster_bob_y_jitter, self.monster_bob_y_jitter)
        bob_amplitude = self.random.uniform(self.monster_bob_amplitude_min, self.monster_bob_amplitude_max) if bobbing else 0.0
        bob_phase = self.random.uniform(0.0, math.tau) if bobbing else 0.0
        bob_speed = self.random.uniform(self.monster_bob_speed_min, self.monster_bob_speed_max) if bobbing else 0.0
        width = self.ufo_width if kind == "ufo" else self.monster_width
        height = self.ufo_height if kind == "ufo" else self.monster_height
        speed_min = self.ufo_speed_min if kind == "ufo" else self.monster_speed_min
        speed_max = self.ufo_speed_max if kind == "ufo" else self.monster_speed_max
        x = self._find_monster_x(y, width)
        self._spawn_monster_entity(
            Monster(
                x=x,
                y=base_y + math.sin(bob_phase) * bob_amplitude,
                width=width,
                height=height,
                velocity_x=self.random.choice((-1.0, 1.0)) * self.random.uniform(speed_min, speed_max),
                base_y=base_y,
                bob_phase=bob_phase,
                bob_speed=bob_speed,
                bob_amplitude=bob_amplitude,
                kind=kind,
                score_value=120 if kind == "ufo" else 85,
                shot_timer=self.random.uniform(self.ufo_shot_interval_min, self.ufo_shot_interval_max) if kind == "ufo" else 0.0,
            )
        )
    def _maybe_add_pickup(self, platform: Platform, difficulty: float) -> None:
        if platform.kind not in {"stable", "moving"}:
            return
        pickup_kind = self._choose_pickup_kind(platform.y, difficulty)
        if pickup_kind is None:
            return
        pickup_width, pickup_height = self._pickup_dimensions(pickup_kind)
        pickup_x = platform.x + platform.width * 0.5 - pickup_width * 0.5
        pickup_y = platform.y + platform.height + self.pickup_spawn_offset_y
        if not self._pickup_has_gap(pickup_x, pickup_y):
            return
        self._ensure_pickup_components()
        if any(
            abs(existing.x - pickup_x) < self.pickup_overlap_x
            and abs(existing.y - pickup_y) < self.pickup_overlap_y
            for existing in self._pickup_components()
        ):
            return
        self._append_pickup(pickup_kind, pickup_x, pickup_y)
    def _spawn_pickups(self) -> None:
        if self.camera_y < self.pickup_top_up_min_camera_y:
            return

        self._ensure_pickup_components()
        visible_pickups = [
            pickup
            for pickup in self._pickup_components()
            if self.camera_y + self.pickup_top_up_visible_min_offset
            <= pickup.y
            <= self.camera_y + self.world_height + self.pickup_top_up_visible_max_offset
        ]
        if len(visible_pickups) >= self.min_visible_pickups:
            return

        candidate_platforms = [
            platform
            for platform in self.platforms
            if platform.kind in {"stable", "moving"}
            and platform.y >= max(
                self.pickup_min_height,
                self.camera_y + self.pickup_top_up_min_camera_buffer,
                self.player.y + self.pickup_top_up_min_player_buffer,
            )
            and platform.y
            <= self.camera_y
            + self.world_height
            + min(
                self.pickup_top_up_max_camera_buffer,
                self.pickup_top_up_visible_max_offset - self.pickup_spawn_offset_y - self.platform_height,
            )
            and not any(
                abs(existing.x - (platform.x + platform.width * 0.5 - self.jetpack_width * 0.5)) < self.pickup_overlap_x
                and abs(existing.y - (platform.y + platform.height + self.pickup_spawn_offset_y)) < self.pickup_overlap_y
                for existing in self._pickup_components()
            )
        ]
        candidate_platforms.sort(key=lambda platform: platform.y)
        for platform in candidate_platforms[: self.min_visible_pickups - len(visible_pickups)]:
            pickup_kind = self._choose_top_up_pickup_kind(platform.y)
            if pickup_kind is None:
                continue
            pickup_width, _ = self._pickup_dimensions(pickup_kind)
            pickup_x = platform.x + platform.width * 0.5 - pickup_width * 0.5
            pickup_y = platform.y + platform.height + self.pickup_spawn_offset_y
            if not self._pickup_has_gap(pickup_x, pickup_y):
                continue
            self._append_pickup(pickup_kind, pickup_x, pickup_y)
            break
    def _append_pickup(self, kind: str, x: float, y: float) -> None:
        width, height = self._pickup_dimensions(kind)
        self._spawn_pickup_entity(
            Pickup(
                x=x,
                y=y,
                width=width,
                height=height,
                kind=kind,
                phase=self.random.uniform(0.0, math.tau),
            )
        )
        self.highest_pickup_y = max(self.highest_pickup_y, y)
    def _choose_pickup_kind(self, height: float, difficulty: float) -> str | None:
        if (
            height >= self.shield_min_height
            and self.random.random() < self.shield_spawn_chance_base + self.shield_spawn_chance_difficulty * difficulty
        ):
            return "shield"
        if (
            height >= self.rocket_min_height
            and self.random.random() < self.rocket_spawn_chance_base + self.rocket_spawn_chance_difficulty * difficulty
        ):
            return "rocket"
        if (
            height >= self.propeller_min_height
            and self.random.random() < self.propeller_spawn_chance_base + self.propeller_spawn_chance_difficulty * difficulty
        ):
            return "propeller"
        if (
            height >= self.boots_min_height
            and self.random.random() < self.boots_spawn_chance_base + self.boots_spawn_chance_difficulty * difficulty
        ):
            return "boots"
        if height < self.pickup_min_height:
            return None
        if self.random.random() > self.pickup_spawn_chance_base + self.pickup_spawn_chance_difficulty * difficulty:
            return None
        return "jetpack"
    def _pickup_dimensions(self, kind: str) -> tuple[float, float]:
        if kind == "boots":
            return (self.boots_width, self.boots_height)
        if kind == "rocket":
            return (self.rocket_width, self.rocket_height)
        if kind == "shield":
            return (self.shield_width, self.shield_height)
        if kind == "propeller":
            return (self.propeller_width, self.propeller_height)
        return (self.jetpack_width, self.jetpack_height)
    def _pickup_has_gap(self, pickup_x: float, pickup_y: float) -> bool:
        self._ensure_pickup_components()
        return not any(
            abs(existing.x - pickup_x) < self.pickup_overlap_x
            and abs(existing.y - pickup_y) < self.pickup_min_gap_y
            for existing in self._pickup_components()
        )
    def _choose_top_up_pickup_kind(self, height: float) -> str | None:
        if height < self.pickup_min_height:
            return None
        if height >= self.shield_min_height and self.random.random() < 0.22:
            return "shield"
        if height >= self.rocket_min_height and self.random.random() < 0.12:
            return "rocket"
        if height >= self.propeller_min_height and self.random.random() < 0.32:
            return "propeller"
        if height >= self.boots_min_height and self.random.random() < 0.28:
            return "boots"
        return "jetpack"
    def _try_add_extra_platform(self, *, base_y: float, main_x: float, difficulty: float, allow_broken: bool) -> None:
        for _ in range(8):
            candidate_x = self._clamp_platform_x(self.random.uniform(0.0, self.world_width - self.platform_width))
            if abs(candidate_x - main_x) < self.platform_width * 0.8:
                direction = 1.0 if candidate_x < main_x else -1.0
                candidate_x = self._clamp_platform_x(main_x + direction * self.random.uniform(92.0, 170.0))
            candidate_y = base_y + self.random.uniform(-34.0, 34.0)
            if abs(candidate_y - base_y) < 16.0:
                candidate_y = base_y + (18.0 if candidate_y >= base_y else -18.0)
            kind = self._choose_extra_kind(candidate_y, difficulty)
            if not allow_broken and kind == "broken":
                kind = "stable"
            if not self._can_place_platform(candidate_x, candidate_y):
                continue
            velocity_x = 0.0
            if kind == "moving":
                velocity_x = self.random.choice((-1.0, 1.0)) * self.random.uniform(
                    self.extra_moving_speed_min,
                    self.extra_moving_speed_max,
                )
            self.platforms.append(
                Platform(
                    x=candidate_x,
                    y=candidate_y,
                    width=self.platform_width,
                    height=self.platform_height,
                    kind=kind,
                    velocity_x=velocity_x,
                )
            )
            self._maybe_add_pickup(self.platforms[-1], difficulty)
            return
    def _can_place_platform(self, x: float, y: float) -> bool:
        for platform in self.platforms:
            overlaps_x = x < platform.x + platform.width + self.overlap_x_padding and x + self.platform_width + self.overlap_x_padding > platform.x
            overlaps_y = y < platform.y + platform.height + self.overlap_y_padding and y + self.platform_height + self.overlap_y_padding > platform.y
            if overlaps_x and overlaps_y:
                return False
        return True
    def _trim_platforms(self) -> None:
        floor = self.camera_y - 200.0
        self.platforms = [
            platform
            for platform in self.platforms
            if platform.y + platform.height >= floor and (not platform.broken or platform.state_timer > 0.0)
        ]
    def _trim_clouds(self) -> None:
        self._ensure_cloud_components()
        dead_entities: list[int] = []
        for entity_id, cloud, position in self.dynamic_world.query(Cloud, Position):
            cloud.x = position.x
            cloud.y = position.y
            if cloud.y + cloud.height < cloud.parallax * self.camera_y - 160.0:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)
    def _trim_pickups(self) -> None:
        floor = self.camera_y - 120.0
        ceiling = self.camera_y + self.world_height + 120.0
        self._ensure_pickup_components()
        dead_entities: list[int] = []
        for entity_id, pickup, position, size in self.dynamic_world.query(Pickup, Position, Size):
            pickup.x = position.x
            pickup.y = position.y
            pickup.width = size.width
            pickup.height = size.height
            if position.y + size.height < floor or position.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)
    def _trim_black_holes(self) -> None:
        floor = self.camera_y - 220.0
        ceiling = self.camera_y + self.world_height + 220.0
        self._ensure_black_hole_components()
        dead_entities: list[int] = []
        for entity_id, hole, position, size in self.dynamic_world.query(BlackHole, Position, Size):
            hole.x = position.x
            hole.y = position.y
            hole.width = size.width
            hole.height = size.height
            if position.y + size.height < floor or position.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)
    def _trim_monsters(self) -> None:
        floor = self.camera_y - 220.0
        ceiling = self.camera_y + self.world_height + 260.0
        self._ensure_monster_components()
        dead_entities: list[int] = []
        for entity_id, monster, position, size in self.dynamic_world.query(Monster, Position, Size):
            monster.x = position.x
            monster.y = position.y
            monster.width = size.width
            monster.height = size.height
            if position.y + size.height < floor or position.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)
    def _trim_projectiles(self) -> None:
        floor = self.camera_y - 40.0
        ceiling = self.camera_y + self.world_height + 80.0
        self._ensure_projectile_components()
        dead_entities: list[int] = []
        for entity_id, projectile, position, size in self.dynamic_world.query(Projectile, Position, Size):
            projectile.x = position.x
            projectile.y = position.y
            projectile.width = size.width
            projectile.height = size.height
            if position.y + size.height < floor or position.y > ceiling:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)

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
    def _load_best_score(self) -> int:
        if self.score_repository is None:
            return 0
        return self.score_repository.best_score("sketch_hopper")
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
    def _set_sound_enabled(self, enabled: bool) -> None:
        self.sound_enabled = enabled
        if self.audio is not None:
            self.audio.set_enabled(enabled)
        if self.score_repository is not None:
            self.score_repository.set_sound_enabled(enabled)
    def _set_touch_controls_enabled(self, enabled: bool) -> None:
        self.touch_controls_enabled = enabled
        if self.score_repository is not None:
            self.score_repository.set_touch_controls_enabled(enabled)
    def _finalize_score(self) -> None:
        if self.score_saved:
            return
        self.score_saved = True
        self.best_score = max(self.best_score, self.score)
        self._play_sound("game_over")
        if self.score_repository is None or self.score <= 0:
            return
        self.latest_rank = self.score_repository.record_score("sketch_hopper", self.score, player_name=self.player_name)
        self.best_score = self.score_repository.best_score("sketch_hopper")
    def _handle_pickups(self) -> None:
        self._ensure_pickup_components()
        consumed_entities: list[int] = []
        for entity_id, pickup, position, size in self.dynamic_world.query(Pickup, Position, Size):
            pickup.x = position.x
            pickup.y = position.y
            pickup.width = size.width
            pickup.height = size.height
            if self._intersects(
                self.player.x,
                self.player.y,
                self.player.width,
                self.player.height,
                position.x,
                position.y,
                size.width,
                size.height,
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
                self._spawn_impact(position.x + size.width * 0.5, position.y + size.height * 0.5, (0.92, 0.94, 0.98, 0.88))
                consumed_entities.append(entity_id)
        for entity_id in consumed_entities:
            self.dynamic_world.remove_entity(entity_id)
    def _apply_black_holes(self, dt: float) -> None:
        player_cx = self.player.x + self.player.width * 0.5
        player_cy = self.player.y + self.player.height * 0.5
        self._ensure_black_hole_components()
        for _, hole, position, size in self.dynamic_world.query(BlackHole, Position, Size):
            hole.x = position.x
            hole.y = position.y
            hole.width = size.width
            hole.height = size.height
            hole_cx = position.x + size.width * 0.5
            hole_cy = position.y + size.height * 0.5
            dx = hole_cx - player_cx
            dy = hole_cy - player_cy
            distance = math.hypot(dx, dy)
            if distance <= size.width * 0.28:
                if self._consume_shield("WARP SAVED"):
                    if distance > 0.0:
                        away_x = -dx / distance
                        away_y = -dy / distance
                    else:
                        away_x = 0.0
                        away_y = 1.0
                    escape_distance = max(self.player.width, self.player.height) * 0.5 + max(size.width, size.height) * 0.5 + 12.0
                    player_cx = hole_cx + away_x * escape_distance
                    player_cy = hole_cy + away_y * escape_distance
                    self.player.x = (player_cx - self.player.width * 0.5) % self.world_width
                    self.player.y = player_cy - self.player.height * 0.5
                    continue
                self.game_over = True
                return
            if distance <= 0.0 or distance >= self.black_hole_pull_radius:
                continue
            pull = (1.0 - distance / self.black_hole_pull_radius) * self.black_hole_pull_strength
            self.player.x = (self.player.x + (dx / distance) * pull * dt) % self.world_width
            self.player.y += (dy / distance) * pull * dt * 0.75
            player_cx = self.player.x + self.player.width * 0.5
            player_cy = self.player.y + self.player.height * 0.5
    def _play_sound(self, effect_name: str) -> None:
        if self.audio is not None:
            self.audio.play(effect_name)
    def _handle_monster_collisions(self) -> None:
        self._ensure_monster_components()
        for entity_id, monster, position, velocity, size in self.dynamic_world.query(Monster, Position, Velocity, Size):
            monster.x = position.x
            monster.y = position.y
            monster.width = size.width
            monster.height = size.height
            monster.velocity_x = velocity.vx
            if self._intersects(
                self.player.x,
                self.player.y,
                self.player.width,
                self.player.height,
                position.x,
                position.y,
                size.width,
                size.height,
            ):
                if self._consume_shield("SHIELD BLOCK"):
                    self.dynamic_world.remove_entity(entity_id)
                    self.score += monster.score_value
                    self._play_sound("shield")
                    return
                self.game_over = True
                return
    def _difficulty_at_height(self, height: float) -> float:
        return min(max(height / self.difficulty_ramp_height, 0.0), 1.0)
    def _tick_feedback(self, dt: float) -> None:
        self.feedback_timer = max(0.0, self.feedback_timer - dt)
        if self.feedback_timer == 0.0:
            self.feedback_text = ""
        self.flash_timer = max(0.0, self.flash_timer - dt)
        self.shake_amount = max(0.0, self.shake_amount - self.shake_decay * dt)
        self.shield_timer = max(0.0, self.shield_timer - dt)
        self.player_squash_timer = max(0.0, self.player_squash_timer - dt)
        self.player_stretch_timer = max(0.0, self.player_stretch_timer - dt)
        self.theme_transition_timer = max(0.0, self.theme_transition_timer - dt)
        self._ensure_impact_components()
        dead_entities: list[int] = []
        for entity_id, effect, lifetime in self.dynamic_world.query(ImpactEffect, Lifetime):
            lifetime.remaining = max(0.0, lifetime.remaining - dt)
            effect.timer = lifetime.remaining
            if lifetime.remaining == 0.0:
                dead_entities.append(entity_id)
        for entity_id in dead_entities:
            self.dynamic_world.remove_entity(entity_id)
    def _trigger_feedback(self, text: str, color: Color, *, shake: float = 0.0) -> None:
        self.feedback_text = text
        self.feedback_timer = self.feedback_message_duration
        self.flash_timer = self.effect_flash_duration
        self.flash_color = color
        self.shake_amount = max(self.shake_amount, shake)
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
    def _camera_shake_offset(self) -> float:
        if self.shake_amount <= 0.0:
            return 0.0
        return math.sin(self.feedback_timer * 36.0 + self.score * 0.01) * self.shake_amount
    def _consume_shield(self, text: str) -> bool:
        if self.shield_timer <= 0.0:
            return False
        self.shield_timer = 0.0
        self._trigger_feedback(text, (0.48, 0.82, 1.0, 0.92), shake=4.0)
        self._spawn_impact(self.player.x + self.player.width * 0.5, self.player.y + self.player.height * 0.5, (0.48, 0.82, 1.0, 0.92))
        return True
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
