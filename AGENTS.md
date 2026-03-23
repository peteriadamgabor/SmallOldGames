# Repository Guidelines

## Project Structure & Module Organization

`smalloldgames/` contains the application code. Keep engine-level systems in `smalloldgames/engine/`, renderer code in `smalloldgames/rendering/`, shared asset loaders in `smalloldgames/assets/`, storage code in `smalloldgames/data/`, menus in `smalloldgames/menus/`, and game-specific logic under `smalloldgames/games/` and `smalloldgames/games/sketch_hopper_game/`. Runtime assets live in `assets/` (`sprites/`, `shaders/`, `branding/`, `config/`). Tests live in `tests/`. Packaging helpers are in `scripts/`, and the PyInstaller entry spec is `SmallOldGames.spec`.

## Build, Test, and Development Commands

Use `uv` for local setup and execution:

- `uv sync` installs the Python 3.13 project dependencies into `.venv`.
- `uv run smalloldgames` launches the desktop app through the packaged entry point.
- `uv run python -m unittest discover -s tests -v` runs the full test suite used by CI.
- `uv run python -m compileall main.py smalloldgames tests` matches the CI bytecode compile check.
- `bash scripts/build_linux.sh` builds the Linux PyInstaller bundle and `.tar.gz` archive.
- `powershell -ExecutionPolicy Bypass -File scripts/build_windows.ps1` builds the Windows onedir package and `.zip`.

## Coding Style & Naming Conventions

Follow the existing Python style: 4-space indentation, type hints on public functions, and `from __future__ import annotations` where already used. Use `snake_case` for modules, functions, and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants such as window sizing values. Keep files focused by subsystem and prefer explicit imports from the owning package. When changing balance or tuning, update `assets/config/sketch_hopper.toml` instead of scattering magic values.

## Testing Guidelines

Tests use the standard library `unittest` framework. Name files `tests/test_<area>.py`, group cases by subsystem, and add regression tests for gameplay, storage, or engine lifecycle changes. Keep tests deterministic and avoid depending on a live window, audio device, or Vulkan runtime unless the behavior truly requires it.

## Commit & Pull Request Guidelines

Recent commits use short, imperative summaries such as `Fix runtime cleanup and gameplay regressions` or `Add Windows packaging support`. Keep that style. Pull requests should include a clear scope summary, linked issue or release context when relevant, commands run locally, and screenshots or short clips for UI, rendering, or packaging changes. Note Linux/Windows impact explicitly because CI validates both platforms.
