from __future__ import annotations

from smalloldgames.engine import GameAction, InputState, SceneContext, SceneResult, Transition
from smalloldgames.rendering.primitives import DrawList

from .common import (
    GOOD,
    TEXT_LIGHT,
    TEXT_MUTED,
    draw_menu_background,
)
from .components import BASE_PANEL, draw_button, draw_panel


class SettingsScene:
    def __init__(
        self,
        on_back,
        *,
        ctx: SceneContext | None = None,
        on_sound_changed=None,
    ) -> None:
        self.on_back = on_back
        self.score_repository = ctx.score_repository if ctx else None
        self.on_sound_changed = on_sound_changed
        self.sound_enabled = self._load_sound_enabled()
        self.touch_controls_enabled = self._load_touch_controls_enabled()

    def update(self, _: float, inputs: InputState) -> SceneResult:
        if inputs.pointer_pressed:
            if inputs.pointer_in_rect(42, 542, 456, 120):
                self._set_sound_enabled(not self.sound_enabled)
                return None
            if inputs.pointer_in_rect(42, 402, 456, 120):
                self._set_touch_controls_enabled(not self.touch_controls_enabled)
                return None
            if inputs.pointer_in_rect(42, 120, 456, 72):
                return Transition(self.on_back())

        if inputs.action_pressed(GameAction.BACK):
            return Transition(self.on_back())
        if inputs.action_pressed(GameAction.SOUND_TOGGLE):
            self._set_sound_enabled(not self.sound_enabled)
        if inputs.action_pressed(GameAction.TOUCH_TOGGLE):
            self._set_touch_controls_enabled(not self.touch_controls_enabled)
        return None

    def render(self, draw: DrawList) -> None:
        draw_menu_background(draw)
        draw.text(draw.width * 0.5, 874, "GLOBAL SETTINGS", scale=5, color=TEXT_LIGHT, centered=True)
        draw.text(draw.width * 0.5, 838, "PERSISTENT ACROSS ALL GAMES", scale=2, color=TEXT_MUTED, centered=True)

        self._draw_setting_card(
            draw,
            y=542,
            title="SOUND EFFECTS",
            value="ENABLED" if self.sound_enabled else "DISABLED",
            active=self.sound_enabled,
            help_text="PRESS S OR TAP TO TOGGLE",
        )

        self._draw_setting_card(
            draw,
            y=402,
            title="TOUCH CONTROLS",
            value="ENABLED" if self.touch_controls_enabled else "DISABLED",
            active=self.touch_controls_enabled,
            help_text="PRESS T OR TAP TO TOGGLE",
        )

        draw_button(draw, x=42, y=120, width=456, height=72, label="BACK TO LAUNCHER", style=BASE_PANEL)

    @staticmethod
    def music_track() -> str | None:
        return "launcher"

    def window_title(self) -> str:
        return "Small Old Games - Settings"

    def on_enter(self) -> None:
        pass

    def on_exit(self) -> None:
        pass

    def _draw_setting_card(
        self,
        draw: DrawList,
        *,
        y: float,
        title: str,
        value: str,
        active: bool,
        help_text: str,
    ) -> None:
        draw_panel(draw, x=42, y=y, width=456, height=120, style=BASE_PANEL)
        draw.text(66, y + 84, title, scale=3, color=TEXT_LIGHT, world=False)
        draw.text(66, y + 48, value, scale=4, color=GOOD if active else TEXT_MUTED, world=False)
        draw.text(66, y + 20, help_text, scale=2, color=TEXT_MUTED, world=False)

    def _load_sound_enabled(self) -> bool:
        if self.score_repository is None:
            return True
        return self.score_repository.get_sound_enabled()

    def _set_sound_enabled(self, enabled: bool) -> None:
        self.sound_enabled = enabled
        if self.score_repository is not None:
            self.score_repository.set_sound_enabled(enabled)
        if self.on_sound_changed:
            self.on_sound_changed(enabled)

    def _load_touch_controls_enabled(self) -> bool:
        if self.score_repository is None:
            return True
        return self.score_repository.get_touch_controls_enabled()

    def _set_touch_controls_enabled(self, enabled: bool) -> None:
        self.touch_controls_enabled = enabled
        if self.score_repository is not None:
            self.score_repository.set_touch_controls_enabled(enabled)
