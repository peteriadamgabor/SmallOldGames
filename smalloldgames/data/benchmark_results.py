from __future__ import annotations

import json
from pathlib import Path

from .storage import default_database_path


def default_benchmark_results_dir() -> Path:
    return default_database_path().parent / "benchmarks"


def default_benchmark_results_path() -> Path:
    return default_benchmark_results_dir() / "benchmark_latest.json"


def save_benchmark_result(report: dict, *, path: str | Path | None = None) -> tuple[Path, Path]:
    latest_path = Path(path) if path is not None else default_benchmark_results_path()
    latest_path.parent.mkdir(parents=True, exist_ok=True)

    finished_at = str(report.get("finished_at", "unknown")).replace(":", "").replace("-", "")
    archive_name = f"benchmark_{finished_at.replace('.', '_')}.json"
    archive_path = latest_path.parent / archive_name

    payload = json.dumps(report, indent=2, sort_keys=True)
    latest_path.write_text(payload + "\n", encoding="utf-8")
    archive_path.write_text(payload + "\n", encoding="utf-8")
    return latest_path, archive_path
