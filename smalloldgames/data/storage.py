from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import sqlite3


@dataclass(frozen=True, slots=True)
class ScoreEntry:
    player_name: str
    score: int
    played_at: str

    @property
    def short_date(self) -> str:
        if len(self.played_at) >= 10:
            return self.played_at[5:10]
        return "-- --"


def default_database_path() -> Path:
    return Path.home() / ".smalloldgames" / "scoreboard.sqlite3"


class ScoreRepository:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = Path(database_path) if database_path is not None else default_database_path()
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self._initialize()
        except (OSError, sqlite3.Error) as error:
            raise RuntimeError(f"Could not open scoreboard database: {error}") from error

    def record_score(self, game: str, score: int, *, player_name: str | None = None) -> int:
        if score < 0:
            raise ValueError("Score must be non-negative.")

        safe_name = self._normalize_player_name(player_name or self.get_player_name())
        played_at = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO scores (game, player_name, score, played_at) VALUES (?, ?, ?, ?)",
                (game, safe_name, score, played_at),
            )
            rank = connection.execute(
                "SELECT COUNT(*) + 1 FROM scores WHERE game = ? AND score > ?",
                (game, score),
            ).fetchone()[0]
        return int(rank)

    def best_score(self, game: str) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COALESCE(MAX(score), 0) FROM scores WHERE game = ?", (game,)).fetchone()
        return int(row[0])

    def top_scores(self, game: str, *, limit: int = 5) -> list[ScoreEntry]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT COALESCE(player_name, 'PLAYER'), score, played_at
                FROM scores
                WHERE game = ?
                ORDER BY score DESC, played_at ASC, id ASC
                LIMIT ?
                """,
                (game, limit),
            ).fetchall()
        return [
            ScoreEntry(player_name=self._normalize_player_name(player_name), score=int(score), played_at=played_at)
            for player_name, score, played_at in rows
        ]

    def stats(self, game: str) -> ScoreStats:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*), COALESCE(AVG(score), 0), COALESCE(MAX(score), 0)
                FROM scores
                WHERE game = ?
                """,
                (game,),
            ).fetchone()
        return ScoreStats(total_runs=int(row[0]), average_score=int(round(row[1])), best_score=int(row[2]))

    def get_player_name(self) -> str:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = 'player_name'").fetchone()
        if row is None:
            return "PLAYER"
        return self._normalize_player_name(row[0])

    def set_player_name(self, player_name: str) -> str:
        safe_name = self._normalize_player_name(player_name)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value) VALUES ('player_name', ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (safe_name,),
            )
        return safe_name

    def get_sound_enabled(self) -> bool:
        return self._get_bool_setting("sound_enabled", True)

    def set_sound_enabled(self, enabled: bool) -> bool:
        self._set_bool_setting("sound_enabled", enabled)
        return enabled

    def get_touch_controls_enabled(self) -> bool:
        return self._get_bool_setting("touch_controls_enabled", True)

    def set_touch_controls_enabled(self, enabled: bool) -> bool:
        self._set_bool_setting("touch_controls_enabled", enabled)
        return enabled

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game TEXT NOT NULL,
                    player_name TEXT NOT NULL DEFAULT 'PLAYER',
                    score INTEGER NOT NULL CHECK (score >= 0),
                    played_at TEXT NOT NULL
                )
                """
            )
            columns = {row[1] for row in connection.execute("PRAGMA table_info(scores)").fetchall()}
            if "player_name" not in columns:
                connection.execute("ALTER TABLE scores ADD COLUMN player_name TEXT NOT NULL DEFAULT 'PLAYER'")
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_scores_game_score ON scores (game, score DESC, played_at ASC)"
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
                """
            )
            connection.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('player_name', 'PLAYER')"
            )
            connection.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('sound_enabled', '1')"
            )
            connection.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES ('touch_controls_enabled', '1')"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    @staticmethod
    def _normalize_player_name(player_name: str) -> str:
        cleaned = "".join(character for character in player_name.upper() if character.isalnum() or character == " ")
        cleaned = " ".join(cleaned.split())
        cleaned = cleaned[:10].strip()
        return cleaned or "PLAYER"

    def _get_bool_setting(self, key: str, default: bool) -> bool:
        with self._connect() as connection:
            row = connection.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
        if row is None:
            return default
        return row[0] == "1"

    def _set_bool_setting(self, key: str, value: bool) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO settings (key, value) VALUES (?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value
                """,
                (key, "1" if value else "0"),
            )


@dataclass(frozen=True, slots=True)
class ScoreStats:
    total_runs: int
    average_score: int
    best_score: int
