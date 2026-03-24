"""Shared persistence helpers for game scenes.

Expects the host class to have:
- ``score_repository``: ``ScoreRepository | None``
- ``audio``: ``AudioEngine | None``
- ``_game_name``: ``str`` — e.g. ``"snake"``, ``"space_invaders"``
- ``score``, ``best_score``, ``score_saved``: mutable game state
- ``sound_enabled``, ``touch_controls_enabled``: setting flags
"""

from __future__ import annotations


class PersistenceMixin:
    """Eliminates copy-pasted load/save helpers across game scenes."""

    # --- Loaders ---

    def _load_best_score(self) -> int:
        if self.score_repository is None:
            return 0
        return self.score_repository.best_score(self._game_name)

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

    # --- Setters ---

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

    # --- Score finalization ---

    def _finalize_score(self) -> None:
        """Record the current score and update best.  Override for extras."""
        if self.score_saved or self.score_repository is None:
            return
        self.score_repository.record_score(self._game_name, self.score)
        self.score_saved = True
        self.best_score = self._load_best_score()

    # --- Sound shorthand ---

    def _play_sound(self, effect_name: str) -> None:
        if self.audio is not None:
            self.audio.play(effect_name)
