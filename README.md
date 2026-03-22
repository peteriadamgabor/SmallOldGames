# Small Old Games

Retro mobile game remakes in Python with a Vulkan renderer.

The first implemented game is `Sketch Hopper`, an endless vertical jumper inspired by early phone games. The long-term goal is a small collection of old mobile-style remakes running from one launcher.

## Current Features

- Launcher with game selection and local leaderboard entry point
- Resizable desktop window with portrait-content scaling
- Vulkan-backed 2D renderer
- Playable `Sketch Hopper`
- Procedural platform generation
- Moving, broken, fake, vanish, spring, and trampoline platforms
- Monsters, UFOs, projectiles, hazards, and pickups
- Local SQLite scoreboard
- Balance config file for gameplay tuning
- Automated unit tests for core gameplay and engine behavior

## Current Target

The project is currently a desktop application.

Supported development targets:

- Linux desktop
- Windows desktop

Not finished yet:

- Android packaging and touch-native deployment
- Multiple completed games in the launcher
- Full production art/audio polish

## Requirements

You need:

- Python `3.13+`
- `uv`
- A Vulkan-capable GPU and working driver/runtime
- A real graphical desktop session

Optional but useful:

- `glslangValidator` for rebuilding shader binaries

Important:

- This project will not run from a headless shell or CI runner without graphics.
- If Vulkan is not working on your machine, the game will not start.

## Setup

### Linux

Install:

- Python 3.13+
- `uv`
- Vulkan runtime/loader
- Your GPU's Vulkan driver
- GLFW runtime dependencies
- `glslangValidator` if you want to rebuild shaders

Example packages:

Arch Linux / Manjaro:

```bash
sudo pacman -S python uv vulkan-icd-loader vulkan-tools glslang glfw-x11
```

Ubuntu / Debian:

```bash
sudo apt install python3 python3-venv curl libglfw3 libvulkan1 vulkan-tools glslang-tools
```

You may also need your vendor-specific Vulkan driver package.

### Windows

Install:

- Python `3.13+`
- `uv`
- A recent GPU driver with Vulkan support
- Vulkan Runtime

Optional:

- Vulkan SDK if you want `glslangValidator.exe` and `vulkaninfo.exe`

Practical Windows notes:

- Update your GPU driver first.
- If you use NVIDIA / AMD / Intel drivers from the vendor, Vulkan runtime is usually installed with the driver.
- If you want shader rebuild tools, install the Vulkan SDK and make sure `glslangValidator.exe` is on `PATH`.
- Run the game from `Windows Terminal`, PowerShell, or Command Prompt, not from a headless remote shell.

## Verify Vulkan

Before running the project, confirm Vulkan works.

Linux:

```bash
vulkaninfo
```

Windows, if Vulkan SDK tools are installed:

```powershell
vulkaninfo
```

If that command is not available on Windows, the game may still run as long as your Vulkan driver/runtime is installed correctly. If startup fails with a Vulkan device error, fix the GPU driver/runtime first.

## Project Setup

Clone the repository and install Python dependencies:

```bash
git clone <your-repo-url>
cd SmallOldGames
uv sync
```

This creates the local virtual environment and installs the Python dependencies from [pyproject.toml](/mnt/Development/Python/SmallOldGames/pyproject.toml).

## Running

Recommended:

```bash
uv run smalloldgames
```

Alternative entry points:

```bash
uv run python main.py
```

```bash
uv run python -m smalloldgames.engine.app
```

Windows PowerShell example:

```powershell
uv run smalloldgames
```

## Controls

### Launcher

- `Up` / `W`: move selection up
- `Down` / `S`: move selection down
- `Enter` / `Space`: open selected item
- Mouse: click cards and buttons

### Sketch Hopper

- `Left` / `A`: move left
- `Right` / `D`: move right
- `Space`: shoot
- `P`: pause
- `R`: restart run
- `Esc`: return to launcher
- `Q`: quit application
- Mouse/touch-style UI: menu buttons, pause button, on-screen controls

## Quick Start

Shortest path from zero to first launch:

1. Make sure your machine has working Vulkan support.
2. Open a terminal inside your desktop session.
3. Go to the project directory.
4. Run `uv sync`.
5. Run `uv run smalloldgames`.

If everything is working, you should see:

- A portrait game window
- The `Small Old Games` launcher
- A `Sketch Hopper` game card
- The game starting when you open it

## Save Data And Local Files

The project stores local runtime data outside the repository:

- scoreboard database: `~/.smalloldgames/scoreboard.sqlite3`
- local balance override: `~/.smalloldgames/sketch_hopper.toml`

That means your checked-in project files stay clean while scores and local tuning remain persistent.

## Project Layout

```text
SmallOldGames/
├── assets/
│   ├── config/
│   │   └── sketch_hopper.toml
│   ├── shaders/
│   └── sprites/
├── smalloldgames/
│   ├── assets/
│   ├── data/
│   ├── engine/
│   ├── games/
│   │   ├── sketch_hopper.py
│   │   └── sketch_hopper_game/
│   ├── menus/
│   └── rendering/
├── tests/
│   ├── test_sketch_hopper.py
│   ├── test_sketch_hopper_config.py
│   └── ...
├── main.py
├── pyproject.toml
└── README.md
```

## Architecture Overview

### Engine

- [app.py](/mnt/Development/Python/SmallOldGames/smalloldgames/engine/app.py): window creation, main loop, scene switching
- [audio.py](/mnt/Development/Python/SmallOldGames/smalloldgames/engine/audio.py): synthesized effects/music playback
- [input.py](/mnt/Development/Python/SmallOldGames/smalloldgames/engine/input.py): keyboard and pointer state
- [game_registry.py](/mnt/Development/Python/SmallOldGames/smalloldgames/engine/game_registry.py): launcher-visible game registration
- [ecs.py](/mnt/Development/Python/SmallOldGames/smalloldgames/engine/ecs.py): lightweight ECS utilities

### Menus

- [home.py](/mnt/Development/Python/SmallOldGames/smalloldgames/menus/home.py): launcher scene
- [leaderboard.py](/mnt/Development/Python/SmallOldGames/smalloldgames/menus/leaderboard.py): scoreboard scene
- [components.py](/mnt/Development/Python/SmallOldGames/smalloldgames/menus/components.py): shared menu drawing helpers

### Sketch Hopper

- [sketch_hopper.py](/mnt/Development/Python/SmallOldGames/smalloldgames/games/sketch_hopper.py): public game entry exports
- [scene.py](/mnt/Development/Python/SmallOldGames/smalloldgames/games/sketch_hopper_game/scene.py): main game scene
- [systems.py](/mnt/Development/Python/SmallOldGames/smalloldgames/games/sketch_hopper_game/systems.py): gameplay systems
- [rendering.py](/mnt/Development/Python/SmallOldGames/smalloldgames/games/sketch_hopper_game/rendering.py): game rendering helpers
- [ui.py](/mnt/Development/Python/SmallOldGames/smalloldgames/games/sketch_hopper_game/ui.py): pause/settings/balance UI
- [config.py](/mnt/Development/Python/SmallOldGames/smalloldgames/games/sketch_hopper_game/config.py): config schema and load/save helpers
- [assets.py](/mnt/Development/Python/SmallOldGames/smalloldgames/games/sketch_hopper_game/assets.py): game-specific sprite atlas

### Rendering

- [primitives.py](/mnt/Development/Python/SmallOldGames/smalloldgames/rendering/primitives.py): immediate-mode draw list
- [vulkan_renderer.py](/mnt/Development/Python/SmallOldGames/smalloldgames/rendering/vulkan_renderer.py): Vulkan backend

### Persistence

- [storage.py](/mnt/Development/Python/SmallOldGames/smalloldgames/data/storage.py): SQLite scoreboard and settings

## Configuration

The shipped gameplay config is:

- [sketch_hopper.toml](/mnt/Development/Python/SmallOldGames/assets/config/sketch_hopper.toml)

This file controls things like:

- minimum spawn heights
- spawn chances
- movement speeds
- pickup gaps
- monster/UFO pacing

The game can also save a local override config to `~/.smalloldgames/sketch_hopper.toml`.

## Development Commands

Install dependencies:

```bash
uv sync
```

Run the game:

```bash
uv run smalloldgames
```

Run tests:

```bash
uv run python -m unittest discover -s tests -v
```

Bytecode/syntax check:

```bash
uv run python -m compileall main.py smalloldgames tests
```

Rebuild shaders:

Linux/macOS:

```bash
glslangValidator -V assets/shaders/color.vert -o assets/shaders/color.vert.spv
glslangValidator -V assets/shaders/color.frag -o assets/shaders/color.frag.spv
```

Windows PowerShell:

```powershell
glslangValidator -V assets/shaders/color.vert -o assets/shaders/color.vert.spv
glslangValidator -V assets/shaders/color.frag -o assets/shaders/color.frag.spv
```

## Troubleshooting

### `GLFW could not initialize`

Typical causes:

- no graphical desktop session
- broken remote display forwarding
- running from a headless shell

What to do:

- launch from your desktop terminal
- confirm you are logged into a graphical session
- on Linux, check `echo $DISPLAY`

### `No Vulkan device with graphics and presentation support was found`

Typical causes:

- Vulkan runtime is missing
- GPU driver is missing or broken
- you are inside a VM/container without proper GPU access

What to do:

- verify Vulkan support first
- update/reinstall the GPU driver
- confirm the machine exposes a Vulkan-capable device

### Sound does not play

The game keeps running if sound backends are unavailable.

Notes:

- Windows uses `winsound`
- Linux/macOS use external players if available
- if none are available, audio will fail silently

### Shader compile tool not found

That only matters if you edit shader sources.

Use:

- Linux: install `glslang-tools` or equivalent
- Windows: install the Vulkan SDK or otherwise provide `glslangValidator.exe`

## Git Ignore

A project `.gitignore` is included so local virtualenvs, Python cache files, IDE settings, coverage output, and local databases are not committed accidentally.
