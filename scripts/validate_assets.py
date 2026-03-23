"""Validate that all asset files referenced in code exist on disk."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure the project root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from smalloldgames.assets.catalog import CONFIG_DIR, SHADERS_DIR, SPRITES_DIR


def main() -> int:
    errors: list[str] = []

    # Verify sprite files referenced in the atlas catalog
    from smalloldgames.assets.atlas import ALL_SPRITE_PATHS

    for name, path in ALL_SPRITE_PATHS.items():
        if not path.exists():
            errors.append(f"Missing sprite: {name} -> {path}")

    # Verify shader files (source + compiled SPIR-V)
    expected_shaders = [
        "color.vert",
        "color.vert.spv",
        "color.frag",
        "color.frag.spv",
    ]
    for shader in expected_shaders:
        path = SHADERS_DIR / shader
        if not path.exists():
            errors.append(f"Missing shader: {path}")

    # Verify config files
    expected_configs = [
        "sketch_hopper.toml",
    ]
    for config in expected_configs:
        path = CONFIG_DIR / config
        if not path.exists():
            errors.append(f"Missing config: {path}")

    # Check for orphaned sprite files (exist on disk but not in atlas)
    referenced_files = {p.name for p in ALL_SPRITE_PATHS.values()}
    for xpm_file in SPRITES_DIR.glob("*.xpm"):
        if xpm_file.name not in referenced_files:
            errors.append(f"Orphaned sprite (not in atlas): {xpm_file.name}")

    if errors:
        print(f"Asset validation failed with {len(errors)} error(s):")
        for error in errors:
            print(f"  - {error}")
        return 1

    print(
        f"All assets valid: {len(ALL_SPRITE_PATHS)} sprites, "
        f"{len(expected_shaders)} shaders, {len(expected_configs)} configs."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
