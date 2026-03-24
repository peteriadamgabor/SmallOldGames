from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from smalloldgames.engine.persistence import PersistenceMixin


class FakeGame(PersistenceMixin):
    _game_name = "test_game"

    def __init__(self, *, repo=None, audio=None):
        self.score_repository = repo
        self.audio = audio
        self.score = 0
        self.best_score = 0
        self.score_saved = False
        self.sound_enabled = True
        self.touch_controls_enabled = True


class PersistenceLoadTests(unittest.TestCase):
    def test_load_best_score_no_repo(self) -> None:
        game = FakeGame()
        self.assertEqual(game._load_best_score(), 0)

    def test_load_best_score_with_repo(self) -> None:
        repo = MagicMock()
        repo.best_score.return_value = 42
        game = FakeGame(repo=repo)
        self.assertEqual(game._load_best_score(), 42)
        repo.best_score.assert_called_with("test_game")

    def test_load_player_name_no_repo(self) -> None:
        game = FakeGame()
        self.assertEqual(game._load_player_name(), "PLAYER")

    def test_load_player_name_with_repo(self) -> None:
        repo = MagicMock()
        repo.get_player_name.return_value = "ACE"
        game = FakeGame(repo=repo)
        self.assertEqual(game._load_player_name(), "ACE")

    def test_load_sound_enabled_no_repo(self) -> None:
        game = FakeGame()
        self.assertTrue(game._load_sound_enabled())

    def test_load_touch_controls_enabled_no_repo(self) -> None:
        game = FakeGame()
        self.assertTrue(game._load_touch_controls_enabled())


class PersistenceSetTests(unittest.TestCase):
    def test_set_sound_enabled(self) -> None:
        repo = MagicMock()
        audio = MagicMock()
        game = FakeGame(repo=repo, audio=audio)
        game._set_sound_enabled(False)
        self.assertFalse(game.sound_enabled)
        audio.set_enabled.assert_called_with(False)
        repo.set_sound_enabled.assert_called_with(False)

    def test_set_touch_controls_enabled(self) -> None:
        repo = MagicMock()
        game = FakeGame(repo=repo)
        game._set_touch_controls_enabled(False)
        self.assertFalse(game.touch_controls_enabled)
        repo.set_touch_controls_enabled.assert_called_with(False)


class FinalizeScoreTests(unittest.TestCase):
    def test_finalize_records_score(self) -> None:
        repo = MagicMock()
        repo.best_score.return_value = 100
        game = FakeGame(repo=repo)
        game.score = 100
        game._finalize_score()
        repo.record_score.assert_called_once_with("test_game", 100)
        self.assertTrue(game.score_saved)
        self.assertEqual(game.best_score, 100)

    def test_finalize_idempotent(self) -> None:
        repo = MagicMock()
        repo.best_score.return_value = 50
        game = FakeGame(repo=repo)
        game.score = 50
        game._finalize_score()
        game._finalize_score()
        self.assertEqual(repo.record_score.call_count, 1)

    def test_finalize_no_repo(self) -> None:
        game = FakeGame()
        game.score = 100
        game._finalize_score()
        self.assertFalse(game.score_saved)


class PlaySoundTests(unittest.TestCase):
    def test_play_sound_with_audio(self) -> None:
        audio = MagicMock()
        game = FakeGame(audio=audio)
        game._play_sound("jump")
        audio.play.assert_called_with("jump")

    def test_play_sound_no_audio(self) -> None:
        game = FakeGame()
        game._play_sound("jump")  # Should not raise


if __name__ == "__main__":
    unittest.main()
