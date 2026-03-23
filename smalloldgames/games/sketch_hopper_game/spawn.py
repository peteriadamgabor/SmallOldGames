from __future__ import annotations

import math

from .shared import BlackHole, Cloud, Monster, Pickup, Platform


class SpawnSystem:
    def _build_initial_platforms(self) -> None:
        y = self.initial_platform_start_y
        route_x = self.route_x
        while y <= self.initial_platform_end_y:
            if y > self.initial_platform_start_y:
                route_x = self._clamp_platform_x(
                    route_x + self.random.uniform(-self.initial_route_shift, self.initial_route_shift)
                )
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

    def _spawn_platforms(self) -> None:
        target_height = self.camera_y + self.world_height + self.platform_spawn_ahead
        stage_bonus = self._theme_stage_progress() * self.theme_platform_gap_bonus
        while self.highest_platform_y < target_height:
            self.highest_platform_y += self.random.uniform(
                self.platform_spawn_gap_min + stage_bonus * 0.4,
                self.platform_spawn_gap_max + stage_bonus,
            )
            difficulty = self._difficulty_at_height(self.highest_platform_y)
            main_x = self._clamp_platform_x(
                self.route_x + self.random.uniform(-self.path_max_shift, self.path_max_shift)
            )
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
            self._spawn_extra_platforms(
                base_y=self.highest_platform_y, main_x=main_x, difficulty=difficulty, allow_broken=True
            )

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
            y = (
                self.camera_y
                + self.world_height * self.monster_top_up_start_ratio
                + attempts * self.monster_top_up_step_y
            )
            self.highest_monster_y = max(self.highest_monster_y, y)
            self._append_monster(y, kind="monster")
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
            self.highest_black_hole_y += self.random.uniform(
                self.black_hole_spawn_gap_min, self.black_hole_spawn_gap_max
            )
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
        if (
            height >= self.spring_min_height
            and roll < self.anchor_spring_chance_base + self.anchor_spring_chance_difficulty * difficulty
        ):
            return "spring"
        if (
            height >= self.moving_platform_min_height
            and roll < self.anchor_moving_chance_base + self.anchor_moving_chance_difficulty * difficulty
        ):
            return "moving"
        return "stable"

    def _choose_extra_kind(self, height: float, difficulty: float) -> str:
        roll = self.random.random()
        if (
            height >= self.broken_platform_min_height
            and roll < self.extra_broken_chance_base + self.extra_broken_chance_difficulty * difficulty
        ):
            return "broken"
        if (
            height >= self.fake_platform_min_height
            and roll < self.extra_fake_chance_base + self.extra_fake_chance_difficulty * difficulty
        ):
            return "fake"
        if (
            height >= self.vanish_platform_min_height
            and roll < self.extra_vanish_chance_base + self.extra_vanish_chance_difficulty * difficulty
        ):
            return "vanish"
        if (
            height >= self.trampoline_min_height
            and roll < self.extra_trampoline_chance_base + self.extra_trampoline_chance_difficulty * difficulty
        ):
            return "trampoline"
        if (
            height >= self.moving_platform_min_height
            and roll < self.extra_moving_chance_base + self.extra_moving_chance_difficulty * difficulty
        ):
            return "moving"
        if (
            height >= self.spring_min_height
            and roll < self.extra_spring_chance_base + self.extra_spring_chance_difficulty * difficulty
        ):
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
        bob_amplitude = (
            self.random.uniform(self.monster_bob_amplitude_min, self.monster_bob_amplitude_max) if bobbing else 0.0
        )
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
                shot_timer=self.random.uniform(self.ufo_shot_interval_min, self.ufo_shot_interval_max)
                if kind == "ufo"
                else 0.0,
            )
        )

    def _maybe_add_pickup(self, platform: Platform, difficulty: float) -> None:
        if platform.kind not in {"stable", "moving"}:
            return
        pickup_kind = self._choose_pickup_kind(platform.y, difficulty)
        if pickup_kind is None:
            return
        pickup_width, _pickup_height = self._pickup_dimensions(pickup_kind)
        pickup_x = platform.x + platform.width * 0.5 - pickup_width * 0.5
        pickup_y = platform.y + platform.height + self.pickup_spawn_offset_y
        if not self._pickup_has_gap(pickup_x, pickup_y):
            return
        if any(
            abs(existing.x - pickup_x) < self.pickup_overlap_x and abs(existing.y - pickup_y) < self.pickup_overlap_y
            for existing in self._pickup_components()
        ):
            return
        self._append_pickup(pickup_kind, pickup_x, pickup_y)

    def _spawn_pickups(self) -> None:
        if self.camera_y < self.pickup_top_up_min_camera_y:
            return

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
            and platform.y
            >= max(
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
                and abs(existing.y - (platform.y + platform.height + self.pickup_spawn_offset_y))
                < self.pickup_overlap_y
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
            and self.random.random()
            < self.propeller_spawn_chance_base + self.propeller_spawn_chance_difficulty * difficulty
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
        return not any(
            abs(existing.x - pickup_x) < self.pickup_overlap_x and abs(existing.y - pickup_y) < self.pickup_min_gap_y
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
            overlaps_x = (
                x < platform.x + platform.width + self.overlap_x_padding
                and x + self.platform_width + self.overlap_x_padding > platform.x
            )
            overlaps_y = (
                y < platform.y + platform.height + self.overlap_y_padding
                and y + self.platform_height + self.overlap_y_padding > platform.y
            )
            if overlaps_x and overlaps_y:
                return False
        return True
