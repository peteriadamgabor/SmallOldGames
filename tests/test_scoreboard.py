from __future__ import annotations

import gc
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import warnings

from smalloldgames.data.storage import ScoreRepository


class ScoreRepositoryTests(unittest.TestCase):
    def test_repository_returns_best_and_top_scores(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = ScoreRepository(Path(temp_dir) / "scores.sqlite3")
            repository.record_score("sketch_hopper", 180, player_name="AAA")
            repository.record_score("sketch_hopper", 420, player_name="BBB")
            repository.record_score("sketch_hopper", 260, player_name="CCC")

            self.assertEqual(repository.best_score("sketch_hopper"), 420)
            self.assertEqual([entry.score for entry in repository.top_scores("sketch_hopper")], [420, 260, 180])
            self.assertEqual([entry.player_name for entry in repository.top_scores("sketch_hopper")], ["BBB", "CCC", "AAA"])
            repository.close()

    def test_record_score_returns_rank(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = ScoreRepository(Path(temp_dir) / "scores.sqlite3")
            repository.record_score("sketch_hopper", 500)
            repository.record_score("sketch_hopper", 280)

            self.assertEqual(repository.record_score("sketch_hopper", 350), 2)
            repository.close()

    def test_player_name_and_stats_are_persistent(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = ScoreRepository(Path(temp_dir) / "scores.sqlite3")
            repository.set_player_name("pixel hero 77")
            repository.record_score("sketch_hopper", 100)
            repository.record_score("sketch_hopper", 300)

            self.assertEqual(repository.get_player_name(), "PIXEL HERO")
            stats = repository.stats("sketch_hopper")
            self.assertEqual(stats.total_runs, 2)
            self.assertEqual(stats.average_score, 200)
            self.assertEqual(stats.best_score, 300)
            repository.close()

    def test_sound_and_touch_settings_persist(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = ScoreRepository(Path(temp_dir) / "scores.sqlite3")
            repository.set_sound_enabled(False)
            repository.set_touch_controls_enabled(False)

            self.assertFalse(repository.get_sound_enabled())
            self.assertFalse(repository.get_touch_controls_enabled())
            repository.close()

    def test_repository_closes_connections_cleanly(self) -> None:
        with TemporaryDirectory() as temp_dir:
            repository = ScoreRepository(Path(temp_dir) / "scores.sqlite3")
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always", ResourceWarning)
                repository.best_score("sketch_hopper")
                gc.collect()
            self.assertEqual([warning for warning in caught if issubclass(warning.category, ResourceWarning)], [])
            repository.close()


if __name__ == "__main__":
    unittest.main()
