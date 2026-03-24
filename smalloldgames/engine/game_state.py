"""Shared game-flow helpers for pause / game-over state management.

Expects the host class to have:
- ``paused``, ``game_over``: ``bool``
- ``exit_scene_factory``: ``Callable[[], Scene]``
- ``reset()``: method to restart the game
"""

from __future__ import annotations

from .input import GameAction, InputState
from .scene import SceneResult, Transition

_SENTINEL = object()


class GameFlowMixin:
    """Handles the common BACK / PAUSE / RESTART / game-over / paused flow.

    Call ``_handle_game_flow(dt, inputs)`` at the top of ``update()``.
    If it returns anything other than ``_SENTINEL``, return that value
    immediately (``None`` means "handled, skip game logic").
    """

    def _handle_game_flow(self, inputs: InputState) -> SceneResult | object:
        """Return a ``SceneResult`` (including ``None``) to short-circuit,
        or ``_SENTINEL`` to continue with normal game logic."""
        if inputs.action_pressed(GameAction.BACK):
            return Transition(self.exit_scene_factory())

        if inputs.action_pressed(GameAction.PAUSE) and not self.game_over:
            self.paused = not self.paused
            self._on_pause_toggled()
            return None

        if inputs.action_pressed(GameAction.RESTART):
            self.reset()
            return None

        if self.game_over:
            return self._on_game_over_input(inputs)

        if self.paused:
            return self._on_pause_input(inputs)

        return _SENTINEL

    # --- Overridable hooks ---

    def _on_pause_toggled(self) -> None:
        """Called after pause state changes. Override for extra setup."""

    def _on_pause_input(self, inputs: InputState) -> SceneResult:
        """Handle input while paused. Default: CONFIRM or tap resumes."""
        if inputs.action_pressed(GameAction.CONFIRM) or (
            inputs.pointer_pressed and inputs.pointer_in_rect(100, 300, 340, 100)
        ):
            self.paused = False
        return None

    def _on_game_over_input(self, inputs: InputState) -> SceneResult:
        """Handle input while game-over. Default: CONFIRM/RESTART or tap resets."""
        if (
            inputs.action_pressed(GameAction.CONFIRM)
            or inputs.action_pressed(GameAction.RESTART)
            or (inputs.pointer_pressed and inputs.pointer_in_rect(100, 300, 340, 100))
        ):
            self.reset()
        return None


# Re-export for use in update() checks.
FLOW_CONTINUE = _SENTINEL
