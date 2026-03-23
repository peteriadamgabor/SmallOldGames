from __future__ import annotations

from dataclasses import replace

import glfw

from smalloldgames.engine import GameAction, InputState, SceneResult, TouchRegion, Transition

from .config import (
    load_sketch_hopper_config,
    reset_sketch_hopper_config,
    save_sketch_hopper_config,
)
from .shared import BALANCE_FIELDS


class SketchHopperUIMixin:
    def _control_move_axis(self, inputs: InputState) -> float:
        return inputs.action_axis(GameAction.MOVE_LEFT, GameAction.MOVE_RIGHT)

    def _shoot_tapped(self, inputs: InputState) -> bool:
        return inputs.action_pressed(GameAction.FIRE)

    def _pause_tapped(self, inputs: InputState) -> bool:
        return inputs.action_pressed(GameAction.PAUSE)

    def _update_pause_menu(self, inputs: InputState) -> SceneResult:
        if self.pause_page == "balance":
            return self._update_balance_editor(inputs)
        if inputs.action_pressed(GameAction.CONFIRM, GameAction.PAUSE):
            self.paused = False
            return None
        if inputs.action_pressed(GameAction.BALANCE):
            self.pause_page = "balance"
            return None
        if inputs.action_pressed(GameAction.SOUND_TOGGLE):
            self._set_sound_enabled(not self.sound_enabled)
            return None
        if inputs.action_pressed(GameAction.TOUCH_TOGGLE):
            self._set_touch_controls_enabled(not self.touch_controls_enabled)
            return None
        if inputs.pointer_pressed:
            if inputs.pointer_in_rect(*self._pause_resume_rect()):
                self.paused = False
                return None
            if inputs.pointer_in_rect(*self._pause_sound_rect()):
                self._set_sound_enabled(not self.sound_enabled)
                return None
            if inputs.pointer_in_rect(*self._pause_touch_rect()):
                self._set_touch_controls_enabled(not self.touch_controls_enabled)
                return None
            if inputs.pointer_in_rect(*self._pause_settings_tab_rect()):
                self.pause_page = "settings"
                return None
            if inputs.pointer_in_rect(*self._pause_balance_tab_rect()):
                self.pause_page = "balance"
                return None
            if inputs.pointer_in_rect(*self._pause_balance_rect()):
                self.pause_page = "balance"
                return None
            if inputs.pointer_in_rect(*self._pause_exit_rect()):
                return Transition(self.on_exit())
        return None

    def _update_balance_editor(self, inputs: InputState) -> SceneResult:
        if inputs.was_pressed(glfw.KEY_ESCAPE) or inputs.action_pressed(GameAction.BALANCE):
            self.pause_page = "settings"
            self.confirm_reset_defaults = False
            return None
        if inputs.action_pressed(GameAction.NAV_UP):
            self.balance_index = (self.balance_index - 1) % len(BALANCE_FIELDS)
            return None
        if inputs.action_pressed(GameAction.NAV_DOWN):
            self.balance_index = (self.balance_index + 1) % len(BALANCE_FIELDS)
            return None
        if inputs.action_pressed(GameAction.NAV_LEFT):
            self._adjust_balance(-1)
            return None
        if inputs.action_pressed(GameAction.NAV_RIGHT):
            self._adjust_balance(1)
            return None
        if inputs.action_pressed(GameAction.SAVE_CONFIG):
            save_sketch_hopper_config(self.config)
            self._trigger_feedback("BALANCE SAVED", (0.54, 0.86, 0.53, 0.92))
            self.confirm_reset_defaults = False
            return None
        if inputs.action_pressed(GameAction.LOAD_CONFIG):
            self.config = load_sketch_hopper_config()
            self._apply_config()
            self._trigger_feedback("BALANCE RELOADED", (0.58, 0.80, 1.0, 0.92))
            self.confirm_reset_defaults = False
            return None
        if inputs.was_pressed(glfw.KEY_BACKSPACE):
            self._trigger_or_apply_balance_reset()
            return None
        if inputs.pointer_pressed:
            if inputs.pointer_in_rect(*self._pause_settings_tab_rect()):
                self.pause_page = "settings"
                self.confirm_reset_defaults = False
                return None
            if inputs.pointer_in_rect(*self._pause_balance_tab_rect()):
                self.pause_page = "balance"
                return None
            for index, rect in enumerate(self._balance_row_rects()):
                if inputs.pointer_in_rect(*rect):
                    self.balance_index = index
                    return None
                if inputs.pointer_in_rect(*self._balance_minus_rect(index)):
                    self.balance_index = index
                    self._adjust_balance(-1)
                    return None
                if inputs.pointer_in_rect(*self._balance_plus_rect(index)):
                    self.balance_index = index
                    self._adjust_balance(1)
                    return None
            if inputs.pointer_in_rect(*self._balance_save_rect()):
                save_sketch_hopper_config(self.config)
                self._trigger_feedback("BALANCE SAVED", (0.54, 0.86, 0.53, 0.92))
                self.confirm_reset_defaults = False
                return None
            if inputs.pointer_in_rect(*self._balance_reload_rect()):
                self.config = load_sketch_hopper_config()
                self._apply_config()
                self._trigger_feedback("BALANCE RELOADED", (0.58, 0.80, 1.0, 0.92))
                self.confirm_reset_defaults = False
                return None
            if inputs.pointer_in_rect(*self._balance_reset_rect()):
                self._trigger_or_apply_balance_reset()
                return None
            if inputs.pointer_in_rect(*self._balance_back_rect()):
                self.pause_page = "settings"
                self.confirm_reset_defaults = False
                return None
        return None

    def _adjust_balance(self, direction: int) -> None:
        _, field_name, step = BALANCE_FIELDS[self.balance_index]
        current = getattr(self.config, field_name)
        if isinstance(current, int) and not isinstance(current, bool):
            next_value = max(0, current + int(direction * step))
        else:
            next_value = max(0.0, round(float(current) + direction * step, 4))
        self.config = replace(self.config, **{field_name: next_value})
        self._apply_config()
        self.confirm_reset_defaults = False

    def _trigger_or_apply_balance_reset(self) -> None:
        if not self.confirm_reset_defaults:
            self.confirm_reset_defaults = True
            self._trigger_feedback("PRESS AGAIN TO RESET", (0.96, 0.78, 0.34, 0.92))
            return
        reset_sketch_hopper_config()
        self.config = load_sketch_hopper_config()
        self._apply_config()
        self.confirm_reset_defaults = False
        self._trigger_feedback("BALANCE RESET", (0.96, 0.78, 0.34, 0.92))

    def _update_game_over_touch(self, inputs: InputState) -> SceneResult:
        if not self.touch_controls_enabled or not inputs.pointer_pressed:
            return None
        if inputs.pointer_in_rect(*self._game_over_retry_rect()):
            self.reset()
            return None
        if inputs.pointer_in_rect(*self._game_over_exit_rect()):
            return Transition(self.on_exit())
        return None

    @staticmethod
    def _intersects(ax: float, ay: float, aw: float, ah: float, bx: float, by: float, bw: float, bh: float) -> bool:
        return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by

    def _left_touch_rect(self) -> tuple[float, float, float, float]:
        return (20.0, 18.0, 118.0, 84.0)

    def _right_touch_rect(self) -> tuple[float, float, float, float]:
        return (148.0, 18.0, 118.0, 84.0)

    def _shoot_touch_rect(self) -> tuple[float, float, float, float]:
        return (398.0, 18.0, 122.0, 84.0)

    def _pause_button_rect(self) -> tuple[float, float, float, float]:
        return (468.0, 896.0, 52.0, 44.0)

    def touch_regions(self) -> tuple[TouchRegion, ...]:
        if not self.touch_controls_enabled or self.paused or self.game_over:
            return ()
        return (
            TouchRegion(*self._left_touch_rect(), frozenset({GameAction.MOVE_LEFT})),
            TouchRegion(*self._right_touch_rect(), frozenset({GameAction.MOVE_RIGHT})),
            TouchRegion(*self._shoot_touch_rect(), frozenset({GameAction.FIRE})),
            TouchRegion(*self._pause_button_rect(), frozenset({GameAction.PAUSE})),
        )

    def _pause_settings_tab_rect(self) -> tuple[float, float, float, float]:
        return (118.0, 634.0, 136.0, 34.0)

    def _pause_balance_tab_rect(self) -> tuple[float, float, float, float]:
        return (286.0, 634.0, 136.0, 34.0)

    def _pause_resume_rect(self) -> tuple[float, float, float, float]:
        return (126.0, 510.0, 288.0, 58.0)

    def _pause_sound_rect(self) -> tuple[float, float, float, float]:
        return (126.0, 438.0, 288.0, 58.0)

    def _pause_touch_rect(self) -> tuple[float, float, float, float]:
        return (126.0, 366.0, 288.0, 58.0)

    def _pause_balance_rect(self) -> tuple[float, float, float, float]:
        return (126.0, 294.0, 288.0, 58.0)

    def _pause_exit_rect(self) -> tuple[float, float, float, float]:
        return (126.0, 222.0, 288.0, 58.0)

    def _game_over_retry_rect(self) -> tuple[float, float, float, float]:
        return (102.0, 264.0, 142.0, 46.0)

    def _game_over_exit_rect(self) -> tuple[float, float, float, float]:
        return (288.0, 264.0, 152.0, 46.0)

    def _balance_row_rect(self, index: int) -> tuple[float, float, float, float]:
        return (74.0, 580.0 - index * 34.0, 286.0, 28.0)

    def _balance_row_rects(self) -> list[tuple[float, float, float, float]]:
        return [self._balance_row_rect(index) for index in range(len(BALANCE_FIELDS))]

    def _balance_minus_rect(self, index: int) -> tuple[float, float, float, float]:
        _, y, _, height = self._balance_row_rect(index)
        return (372.0, y, 42.0, height)

    def _balance_plus_rect(self, index: int) -> tuple[float, float, float, float]:
        _, y, _, height = self._balance_row_rect(index)
        return (422.0, y, 42.0, height)

    def _balance_save_rect(self) -> tuple[float, float, float, float]:
        return (70.0, 222.0, 96.0, 38.0)

    def _balance_reload_rect(self) -> tuple[float, float, float, float]:
        return (182.0, 222.0, 96.0, 38.0)

    def _balance_reset_rect(self) -> tuple[float, float, float, float]:
        return (294.0, 222.0, 112.0, 38.0)

    def _balance_back_rect(self) -> tuple[float, float, float, float]:
        return (422.0, 222.0, 60.0, 38.0)

    @staticmethod
    def _format_balance_value(value: object) -> str:
        if isinstance(value, int):
            return str(value)
        return f"{float(value):.3f}".rstrip("0").rstrip(".")
