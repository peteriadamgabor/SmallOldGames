# Contributing to Small Old Games

First off, thank you for considering contributing to Small Old Games! It's people like you that make this a fun project for everyone.

## Table of Contents

1.  [Getting Started](#getting-started)
2.  [How Can I Contribute?](#how-can-i-contribute)
3.  [Style Guidelines](#style-guidelines)
4.  [Pull Request Process](#pull-request-process)
5.  [Technical Architecture](#technical-architecture)

## Getting Started

To get started with development, you'll need:
- **Python 3.13+**
- **uv** (for dependency management)
- A **Vulkan-capable GPU** and drivers

### Setup
1.  Clone the repository.
2.  Run `uv sync` to install dependencies.
3.  Run `uv run smalloldgames` to verify the installation.
4.  Optionally run `uv run python -m smalloldgames.benchmark --benchmark-output /tmp/benchmark.json` to verify the benchmark path.

## How Can I Contribute?

### Reporting Bugs
Before creating bug reports, please check the existing issues. When reporting a bug, include:
- A clear and descriptive title.
- Steps to reproduce the bug.
- Your OS and hardware (especially GPU/Vulkan version).
- Expected and actual behavior.

### Suggesting Enhancements
We're always looking for new retro mobile game ideas! Please open an issue to discuss new features or games before starting implementation.

### Code Contributions
- Small bug fixes or documentation improvements are always welcome.
- For larger features, please open an issue first.
- Ensure all code is tested (see [Testing](#testing)).

## Style Guidelines

### Python Style
- We follow standard Python style (PEP 8).
- Use clear, descriptive variable and function names.
- Type hints are encouraged where they add clarity.

### Testing
- **Mandatory**: All new features and bug fixes must include unit tests.
- We use the standard `unittest` framework.
- Place tests in the `tests/` directory.
- Run tests before submitting: `uv run python -m unittest discover -s tests -v`
- For benchmark changes, verify the headless benchmark CLI still writes a JSON result file and prints a summary to stdout.

### Commit Messages
- Use clear and concise commit messages.
- Prefer messages that explain "why" rather than just "what".

## Pull Request Process

1.  Create a new branch for your feature or fix.
2.  Ensure your code passes the CI checks:
    - Bytecode compile: `uv run python -m compileall main.py smalloldgames tests`
    - Run all tests: `uv run python -m unittest discover -s tests -v`
3.  Submit a Pull Request (PR) against the `main` branch.
4.  The PR will be reviewed and merged once it passes all checks and review.

## Technical Architecture

Small Old Games uses a custom Vulkan-backed 2D renderer and an Entity Component System (ECS) architecture.

### Directory Structure
- `smalloldgames/engine/`: Core loops, ECS, audio, and input.
- `smalloldgames/rendering/`: Vulkan backend and drawing primitives.
- `smalloldgames/games/`: Specific game logic (e.g., Sketch Hopper).
- `smalloldgames/menus/`: Launcher and UI scenes.
- `assets/`: Shaders, sprites, and configuration.
- `smalloldgames/benchmark.py`: Headless and interactive benchmark entrypoints.

### Shaders
If you modify shaders in `assets/shaders/`, you must recompile them using `glslangValidator`:
```bash
glslangValidator -V assets/shaders/color.vert -o assets/shaders/color.vert.spv
glslangValidator -V assets/shaders/color.frag -o assets/shaders/color.frag.spv
```

### Persistence
The project stores local runtime data (scores, config overrides, benchmark reports) in `~/.smalloldgames/`. Do not commit these files to the repository.
