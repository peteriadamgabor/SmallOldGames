from __future__ import annotations

import math

from smalloldgames.rendering.primitives import DrawList

from .shared import (
    BALANCE_FIELDS,
    BLACK_HOLE_SPRITE,
    BOOTS_SPRITE,
    CLOUD_SPRITE,
    ENEMY_SHOT_SPRITE,
    HOPPER_SPRITE,
    JETPACK_SPRITE,
    MONSTER_SPRITE,
    PLATFORM_BROKEN_SPRITE,
    PLATFORM_MOVING_SPRITE,
    PLATFORM_STABLE_SPRITE,
    PROJECTILE_SPRITE,
    PROPELLER_SPRITE,
    ROCKET_SPRITE,
    SHIELD_SPRITE,
    SPRING_SPRITE,
    TEXT_ACCENT,
    TEXT_DARK,
    TEXT_PANEL,
    UFO_SPRITE,
    BlackHole,
    Cloud,
    ImpactEffect,
    Monster,
    Pickup,
)


class SketchHopperRenderingMixin:
    def _render_feedback(self, draw: DrawList) -> None:
        if self.flash_timer > 0.0:
            alpha = (self.flash_timer / self.effect_flash_duration) * self.effect_flash_alpha
            draw.quad(
                0,
                0,
                draw.width,
                draw.height,
                (self.flash_color[0], self.flash_color[1], self.flash_color[2], alpha),
                world=False,
            )
        if self.feedback_timer > 0.0 and self.feedback_text:
            draw.quad(draw.width * 0.5 - 90.0, 838.0, 180.0, 30.0, (0.08, 0.11, 0.18, 0.56), world=False)
            draw.text(
                draw.width * 0.5,
                848.0,
                self.feedback_text,
                scale=2,
                color=(0.97, 0.98, 0.97, 1.0),
                world=False,
                centered=True,
            )

    def _render_platforms(self, draw: DrawList) -> None:
        for platform in self.platforms:
            sprite = PLATFORM_STABLE_SPRITE
            if platform.broken or platform.kind == "broken":
                sprite = PLATFORM_BROKEN_SPRITE
            elif platform.kind == "moving":
                sprite = PLATFORM_MOVING_SPRITE
            draw.sprite(
                platform.x,
                platform.y - 1.0,
                sprite,
                width=platform.width,
                height=platform.height + 6.0,
                world=True,
            )
            if platform.kind in {"spring", "trampoline"}:
                pulse = min(platform.spring_timer / self.spring_feedback_duration, 1.0)
                if pulse > 0.0:
                    draw.quad(
                        platform.x - 10.0,
                        platform.y + platform.height - 2.0,
                        platform.width + 20.0,
                        10.0 + 18.0 * pulse,
                        (0.98, 0.92, 0.38, 0.16 + 0.16 * pulse),
                        world=True,
                    )
                spring_width = 32.0 + 6.0 * pulse
                spring_height = 26.0 + 10.0 * pulse
                if platform.kind == "trampoline":
                    draw.quad(
                        platform.x + 10.0,
                        platform.y + platform.height - 1.0,
                        platform.width - 20.0,
                        10.0 + 4.0 * pulse,
                        (0.97, 0.53, 0.24, 0.96),
                        world=True,
                    )
                    draw.quad(
                        platform.x + 16.0,
                        platform.y + platform.height + 8.0,
                        platform.width - 32.0,
                        3.0,
                        (0.99, 0.94, 0.62, 0.86),
                        world=True,
                    )
                    continue
                draw.sprite(
                    platform.x + platform.width * 0.5 - spring_width * 0.5,
                    platform.y + platform.height - 2.0,
                    SPRING_SPRITE,
                    width=spring_width,
                    height=spring_height,
                    world=True,
                )
            if platform.kind == "broken":
                draw.triangle(
                    (platform.x + platform.width * 0.25, platform.y + 2),
                    (platform.x + platform.width * 0.52, platform.y + platform.height - 2),
                    (platform.x + platform.width * 0.56, platform.y + 2),
                    (0.25, 0.13, 0.05, 1.0),
                    world=True,
                )
            if platform.kind == "fake" and not platform.broken:
                draw.quad(
                    platform.x + 4.0,
                    platform.y + 3.0,
                    platform.width - 8.0,
                    platform.height - 1.0,
                    (0.96, 0.74, 0.24, 0.32),
                    world=True,
                )
                draw.text(
                    platform.x + platform.width * 0.5,
                    platform.y + 2.0,
                    "?",
                    scale=2,
                    color=(0.34, 0.18, 0.04, 1.0),
                    world=True,
                    centered=True,
                )
            if platform.kind == "vanish" and not platform.broken:
                alpha = 0.45 if platform.state_timer > 0.0 else 0.20
                draw.quad(
                    platform.x,
                    platform.y - 1.0,
                    platform.width,
                    platform.height + 6.0,
                    (0.76, 0.89, 1.0, alpha),
                    world=True,
                )

    def _render_pickups(self, draw: DrawList) -> None:
        for _, pickup in self.dynamic_world.components(Pickup).items():
            aura = (0.28, 0.77, 1.0, 0.10)
            sprite = JETPACK_SPRITE
            if pickup.kind == "boots":
                aura = (0.98, 0.84, 0.34, 0.12)
                sprite = BOOTS_SPRITE
            elif pickup.kind == "rocket":
                aura = (0.98, 0.58, 0.28, 0.12)
                sprite = ROCKET_SPRITE
            elif pickup.kind == "shield":
                aura = (0.48, 0.82, 1.0, 0.12)
                sprite = SHIELD_SPRITE
            elif pickup.kind == "propeller":
                aura = (1.0, 0.82, 0.36, 0.12)
                sprite = PROPELLER_SPRITE
            float_y = pickup.y + math.sin(self.animation_time * 2.6 + pickup.phase) * 4.0
            draw.quad(
                pickup.x - 6.0,
                float_y - 4.0,
                pickup.width + 12.0,
                pickup.height + 10.0,
                aura,
                world=True,
            )
            draw.sprite(
                pickup.x,
                float_y,
                sprite,
                width=pickup.width,
                height=pickup.height,
                world=True,
            )

    def _render_black_holes(self, draw: DrawList) -> None:
        for _, hole in self.dynamic_world.components(BlackHole).items():
            pulse = 1.0 + 0.08 * math.sin(hole.pulse_phase)
            aura = 12.0 + 8.0 * (0.5 + 0.5 * math.sin(hole.pulse_phase))
            draw.quad(
                hole.x - aura * 0.5,
                hole.y - aura * 0.5,
                hole.width + aura,
                hole.height + aura,
                (0.40, 0.18, 0.78, 0.10),
                world=True,
            )
            draw.sprite(
                hole.x - hole.width * (pulse - 1.0) * 0.5,
                hole.y - hole.height * (pulse - 1.0) * 0.5,
                BLACK_HOLE_SPRITE,
                width=hole.width * pulse,
                height=hole.height * pulse,
                world=True,
            )

    def _render_clouds(self, draw: DrawList) -> None:
        for _, cloud in self.dynamic_world.components(Cloud).items():
            screen_y = cloud.y - self.camera_y * cloud.parallax
            if screen_y > draw.height + 120.0 or screen_y + cloud.height < -80.0:
                continue
            draw.sprite(
                cloud.x,
                screen_y,
                CLOUD_SPRITE,
                width=cloud.width,
                height=cloud.height,
                world=False,
            )

    def _render_monsters(self, draw: DrawList) -> None:
        for _, monster in self.dynamic_world.components(Monster).items():
            sprite = UFO_SPRITE if monster.kind == "ufo" else MONSTER_SPRITE
            y = monster.y
            if monster.kind == "ufo":
                y += math.sin(self.animation_time * 3.2 + monster.x * 0.02) * 5.0
            draw.sprite(
                monster.x,
                y,
                sprite,
                width=monster.width,
                height=monster.height,
                world=True,
                flip_x=monster.velocity_x < 0.0,
            )

    def _render_projectiles(self, draw: DrawList) -> None:
        for projectile in self.projectiles:
            sprite = ENEMY_SHOT_SPRITE if projectile.hostile else PROJECTILE_SPRITE
            draw.sprite(
                projectile.x,
                projectile.y,
                sprite,
                width=projectile.width,
                height=projectile.height,
                world=True,
            )

    def _render_player(self, draw: DrawList) -> None:
        stretch = 1.0 + (self.player_stretch_timer / 0.24) * 0.18 if self.player_stretch_timer > 0.0 else 1.0
        squash = 1.0 + (self.player_squash_timer / 0.14) * 0.12 if self.player_squash_timer > 0.0 else 1.0
        width_scale = squash / stretch
        height_scale = stretch / squash
        render_width = self.player.width * width_scale
        render_height = self.player.height * height_scale
        render_x = self.player.x + (self.player.width - render_width) * 0.5
        render_y = self.player.y + (self.player.height - render_height) * 0.5
        if self.rocket_timer > 0.0 or self.jetpack_timer > 0.0 or self.propeller_timer > 0.0:
            boost_ratio = (
                self.rocket_timer / self.rocket_duration
                if self.rocket_timer > 0.0
                else self.jetpack_timer / self.jetpack_duration
                if self.jetpack_timer > 0.0
                else self.propeller_timer / self.propeller_duration
            )
            flame_height = 24.0 + 8.0 * boost_ratio
            draw.triangle(
                (self.player.x + 18.0, self.player.y + 2.0),
                (self.player.x + 28.0, self.player.y - flame_height),
                (self.player.x + 34.0, self.player.y + 2.0),
                (0.98, 0.68, 0.20, 0.90 if self.rocket_timer > 0.0 or self.jetpack_timer > 0.0 else 0.0),
                world=True,
            )
            draw.triangle(
                (self.player.x + 28.0, self.player.y + 4.0),
                (self.player.x + 36.0, self.player.y - flame_height * 0.65),
                (self.player.x + 42.0, self.player.y + 4.0),
                (0.94, 0.32, 0.18, 0.82 if self.rocket_timer > 0.0 or self.jetpack_timer > 0.0 else 0.0),
                world=True,
            )
            if self.rocket_timer > 0.0:
                draw.quad(
                    self.player.x + 19.0,
                    self.player.y - flame_height - 10.0,
                    14.0,
                    6.0,
                    (0.99, 0.92, 0.56, 0.88),
                    world=True,
                )
            if self.propeller_timer > 0.0:
                blade_wobble = 6.0 * math.sin(self.propeller_timer * 18.0)
                draw.quad(
                    self.player.x + 6.0 - blade_wobble,
                    self.player.y + self.player.height + 8.0,
                    self.player.width + blade_wobble * 2.0 - 12.0,
                    4.0,
                    (0.97, 0.94, 0.64, 0.95),
                    world=True,
                )
        draw.sprite(
            render_x,
            render_y,
            HOPPER_SPRITE,
            width=render_width,
            height=render_height,
            world=True,
            flip_x=not self.player_facing_right,
        )
        if self.shield_timer > 0.0:
            glow = 6.0 + 2.0 * math.sin(self.shield_timer * 8.0)
            draw.quad(
                self.player.x - glow,
                self.player.y - glow,
                self.player.width + glow * 2.0,
                self.player.height + glow * 2.0,
                (0.46, 0.80, 1.0, 0.10 + 0.04 * math.sin(self.shield_timer * 6.0)),
                world=True,
            )

    def _render_hud(self, draw: DrawList) -> None:
        theme_name, _, _, accent = self._current_theme()
        draw.quad(14, 892, 170, 52, TEXT_PANEL, world=False)
        draw.text(26, 922, f"SCORE {self.score:05d}", scale=2, color=TEXT_DARK, world=False)
        draw.text(26, 902, f"BEST  {self.best_score:05d}", scale=2, color=TEXT_ACCENT, world=False)
        draw.quad(194, 892, 250, 52, (0.96, 0.97, 0.96, 0.78), world=False)
        if self.touch_controls_enabled:
            draw.text(208, 922, "TOUCH HUD ACTIVE", scale=1.5, color=TEXT_DARK, world=False)
        else:
            draw.text(208, 922, "MOVE: A D OR ARROWS", scale=1.5, color=TEXT_DARK, world=False)
        if self.rocket_timer > 0.0:
            draw.text(
                208,
                902,
                f"ROCKET {int(self.rocket_timer * 10):02d}",
                scale=1.5,
                color=(0.97, 0.58, 0.24, 1.0),
                world=False,
            )
        elif self.jetpack_timer > 0.0:
            draw.text(
                208, 902, f"JETPACK {int(self.jetpack_timer * 10):02d}", scale=1.5, color=TEXT_ACCENT, world=False
            )
        elif self.propeller_timer > 0.0:
            draw.text(208, 902, f"PROPELLER {int(self.propeller_timer * 10):02d}", scale=1.5, color=accent, world=False)
        elif self.shield_timer > 0.0:
            draw.text(
                208, 902, f"SHIELD {int(self.shield_timer):02d}", scale=1.5, color=(0.42, 0.78, 1.0, 1.0), world=False
            )
        elif self.boots_charges_left > 0:
            draw.text(
                208, 902, f"BOOTS {self.boots_charges_left}", scale=1.5, color=(0.98, 0.84, 0.34, 1.0), world=False
            )
        else:
            draw.text(208, 902, "SPACE SHOOT  R / P", scale=1.5, color=TEXT_ACCENT, world=False)
        draw.quad(450, 892, 76, 52, (0.08, 0.11, 0.18, 0.52), world=False)
        draw.text(488, 919, theme_name, scale=1.5, color=(0.94, 0.96, 0.98, 1.0), world=False, centered=True)
        draw.text(488, 903, f"STAGE {self.theme_index + 1}", scale=1.5, color=accent, world=False, centered=True)

    def _render_impacts(self, draw: DrawList) -> None:
        for _, effect in self.dynamic_world.components(ImpactEffect).items():
            t = effect.timer / effect.duration
            radius = 10.0 + (1.0 - t) * 18.0
            alpha = effect.color[3] * t
            draw.quad(
                effect.x - radius * 0.5,
                effect.y - 3.0,
                radius,
                6.0,
                (effect.color[0], effect.color[1], effect.color[2], alpha),
                world=True,
            )
            draw.quad(
                effect.x - 3.0,
                effect.y - radius * 0.5,
                6.0,
                radius,
                (effect.color[0], effect.color[1], effect.color[2], alpha),
                world=True,
            )
            if effect.text:
                draw.text(
                    effect.x,
                    effect.y + 10.0 + (1.0 - t) * 10.0,
                    effect.text,
                    scale=1.5,
                    color=(effect.color[0], effect.color[1], effect.color[2], alpha),
                    world=True,
                    centered=True,
                )

    def _render_game_over(self, draw: DrawList) -> None:
        draw.quad(52, 330, 436, 250, (0.10, 0.12, 0.16, 0.78), world=False)
        draw.text(draw.width * 0.5, 510, "RUN OVER", scale=5, color=(0.97, 0.98, 0.97, 1.0), centered=True)
        draw.text(draw.width * 0.5, 458, f"FINAL SCORE {self.score}", scale=3, color=TEXT_ACCENT, centered=True)
        draw.text(
            draw.width * 0.5, 424, f"PLAYER {self.player_name}", scale=2, color=(0.89, 0.92, 0.93, 1.0), centered=True
        )
        draw.text(
            draw.width * 0.5, 394, self._game_over_rank_text(), scale=2, color=(0.97, 0.85, 0.29, 1.0), centered=True
        )
        draw.text(
            draw.width * 0.5,
            364,
            f"ALL TIME BEST {self.best_score}",
            scale=2,
            color=(0.89, 0.92, 0.93, 1.0),
            centered=True,
        )
        draw.text(
            draw.width * 0.5, 340, "PRESS R TO TRY AGAIN", scale=1.5, color=(0.89, 0.92, 0.93, 1.0), centered=True
        )
        draw.text(
            draw.width * 0.5, 320, "PRESS ESC FOR LAUNCHER", scale=1.5, color=(0.73, 0.79, 0.86, 1.0), centered=True
        )
        if self.touch_controls_enabled:
            retry_x, retry_y, retry_w, retry_h = self._game_over_retry_rect()
            exit_x, exit_y, exit_w, exit_h = self._game_over_exit_rect()
            draw.quad(retry_x, retry_y, retry_w, retry_h, (0.15, 0.48, 0.23, 0.82), world=False)
            draw.quad(exit_x, exit_y, exit_w, exit_h, (0.18, 0.21, 0.28, 0.82), world=False)
            draw.text(
                retry_x + retry_w * 0.5, retry_y + 18, "RETRY", scale=2, color=(0.96, 0.98, 0.96, 1.0), centered=True
            )
            draw.text(
                exit_x + exit_w * 0.5, exit_y + 18, "LAUNCHER", scale=1.5, color=(0.86, 0.90, 0.94, 1.0), centered=True
            )

    def _game_over_rank_text(self) -> str:
        if self.latest_rank is None:
            return "NO SCORE RECORDED"
        return f"LOCAL RANK {self.latest_rank}"

    def _render_touch_controls(self, draw: DrawList) -> None:
        left_x, left_y, left_w, left_h = self._left_touch_rect()
        right_x, right_y, right_w, right_h = self._right_touch_rect()
        shoot_x, shoot_y, shoot_w, shoot_h = self._shoot_touch_rect()
        draw.quad(left_x, left_y, left_w, left_h, (0.08, 0.11, 0.16, 0.28), world=False)
        draw.quad(right_x, right_y, right_w, right_h, (0.08, 0.11, 0.16, 0.28), world=False)
        draw.quad(shoot_x, shoot_y, shoot_w, shoot_h, (0.20, 0.16, 0.08, 0.34), world=False)
        draw.text(left_x + left_w * 0.5, left_y + 34, "LEFT", scale=2, color=(0.91, 0.94, 0.95, 1.0), centered=True)
        draw.text(right_x + right_w * 0.5, right_y + 34, "RIGHT", scale=2, color=(0.91, 0.94, 0.95, 1.0), centered=True)
        draw.text(shoot_x + shoot_w * 0.5, shoot_y + 34, "SHOOT", scale=2, color=(1.0, 0.89, 0.46, 1.0), centered=True)

    def _render_pause_button(self, draw: DrawList) -> None:
        x, y, width, height = self._pause_button_rect()
        draw.quad(x, y, width, height, (0.10, 0.12, 0.18, 0.50), world=False)
        draw.quad(x + 16, y + 10, 7, 28, (0.94, 0.97, 0.95, 1.0), world=False)
        draw.quad(x + 33, y + 10, 7, 28, (0.94, 0.97, 0.95, 1.0), world=False)

    def _render_pause_overlay(self, draw: DrawList) -> None:
        if self.pause_page == "balance":
            self._render_balance_overlay(draw)
            return
        draw.quad(58, 248, 424, 428, (0.08, 0.10, 0.15, 0.84), world=False)
        self._render_pause_tabs(draw)
        draw.text(draw.width * 0.5, 618, "PAUSED", scale=5, color=(0.96, 0.98, 0.96, 1.0), centered=True)
        draw.text(draw.width * 0.5, 580, "SETTINGS", scale=1.5, color=(0.80, 0.85, 0.90, 1.0), centered=True)
        for rect, label, accent in (
            (self._pause_resume_rect(), "RESUME", (0.25, 0.63, 0.31, 0.82)),
            (self._pause_sound_rect(), f"SOUND {'ON' if self.sound_enabled else 'OFF'}", (0.23, 0.28, 0.42, 0.82)),
            (
                self._pause_touch_rect(),
                f"TOUCH {'ON' if self.touch_controls_enabled else 'OFF'}",
                (0.23, 0.28, 0.42, 0.82),
            ),
            (self._pause_balance_rect(), "BALANCE", (0.36, 0.30, 0.14, 0.82)),
            (self._pause_exit_rect(), "LAUNCHER", (0.20, 0.18, 0.22, 0.82)),
        ):
            x, y, width, height = rect
            draw.quad(x, y, width, height, accent, world=False)
            draw.text(
                x + width * 0.5,
                y + 18,
                label,
                scale=2 if label == "RESUME" else 1.5,
                color=(0.95, 0.97, 0.95, 1.0),
                centered=True,
            )
        draw.text(
            draw.width * 0.5,
            284,
            "P OR ENTER RESUMES   S SOUND   T TOUCH   B BALANCE",
            scale=1.5,
            color=(0.73, 0.79, 0.86, 1.0),
            centered=True,
        )

    def _render_balance_overlay(self, draw: DrawList) -> None:
        draw.quad(42, 170, 456, 560, (0.07, 0.09, 0.14, 0.88), world=False)
        self._render_pause_tabs(draw)
        draw.text(draw.width * 0.5, 676, "BALANCE", scale=5, color=(0.96, 0.98, 0.96, 1.0), centered=True)
        draw.text(
            draw.width * 0.5,
            642,
            "LIVE SPAWN AND PROGRESSION TUNING",
            scale=1.5,
            color=(0.82, 0.86, 0.92, 1.0),
            centered=True,
        )
        for index, (label, field_name, _) in enumerate(BALANCE_FIELDS):
            x, y, width, height = self._balance_row_rect(index)
            active = index == self.balance_index
            draw.quad(x, y, width, height, (0.15, 0.18, 0.26, 0.82 if active else 0.52), world=False)
            draw.text(x + 14, y + 15, label, scale=1.5, color=(0.96, 0.97, 0.97, 1.0), world=False)
            draw.text(
                x + 208,
                y + 15,
                self._format_balance_value(getattr(self.config, field_name)),
                scale=1.5,
                color=(0.96, 0.84, 0.38, 1.0),
                world=False,
            )
            minus = self._balance_minus_rect(index)
            plus = self._balance_plus_rect(index)
            draw.quad(*minus, (0.24, 0.28, 0.40, 0.84), world=False)
            draw.quad(*plus, (0.24, 0.28, 0.40, 0.84), world=False)
            draw.text(
                minus[0] + minus[2] * 0.5,
                minus[1] + 12.0,
                "-",
                scale=2,
                color=(0.96, 0.97, 0.97, 1.0),
                world=False,
                centered=True,
            )
            draw.text(
                plus[0] + plus[2] * 0.5,
                plus[1] + 12.0,
                "+",
                scale=2,
                color=(0.96, 0.97, 0.97, 1.0),
                world=False,
                centered=True,
            )
        for rect, label, accent in (
            (self._balance_save_rect(), "SAVE", (0.22, 0.48, 0.28, 0.86)),
            (self._balance_reload_rect(), "RELOAD", (0.22, 0.35, 0.48, 0.86)),
            (
                self._balance_reset_rect(),
                "CONFIRM RESET" if self.confirm_reset_defaults else "DEFAULTS",
                (0.52, 0.35, 0.14, 0.86),
            ),
            (self._balance_back_rect(), "BACK", (0.20, 0.18, 0.24, 0.86)),
        ):
            draw.quad(*rect, accent, world=False)
            draw.text(
                rect[0] + rect[2] * 0.5,
                rect[1] + 14.0,
                label,
                scale=1.5,
                color=(0.96, 0.97, 0.97, 1.0),
                world=False,
                centered=True,
            )
        draw.text(
            draw.width * 0.5,
            194,
            "UP DOWN SELECT   LEFT RIGHT CHANGE   F5 SAVE   F9 RELOAD   BACKSPACE DEFAULTS   ESC BACK",
            scale=1.5,
            color=(0.73, 0.79, 0.86, 1.0),
            centered=True,
        )

    def _render_pause_tabs(self, draw: DrawList) -> None:
        settings_rect = self._pause_settings_tab_rect()
        balance_rect = self._pause_balance_tab_rect()
        for rect, label, active in (
            (settings_rect, "SETTINGS", self.pause_page == "settings"),
            (balance_rect, "BALANCE", self.pause_page == "balance"),
        ):
            color = (0.28, 0.34, 0.46, 0.92) if active else (0.14, 0.17, 0.24, 0.82)
            draw.quad(*rect, color, world=False)
            draw.text(
                rect[0] + rect[2] * 0.5,
                rect[1] + 12.0,
                label,
                scale=1.5,
                color=(0.96, 0.97, 0.98, 1.0),
                world=False,
                centered=True,
            )
