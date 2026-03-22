from __future__ import annotations

from pathlib import Path
import sys


def _runtime_root() -> Path:
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root is not None:
        return Path(bundle_root)
    return Path(__file__).resolve().parent.parent.parent


PROJECT_ROOT = _runtime_root()
PROJECT_ASSETS_DIR = PROJECT_ROOT / "assets"
SPRITES_DIR = PROJECT_ASSETS_DIR / "sprites"
SHADERS_DIR = PROJECT_ASSETS_DIR / "shaders"
CONFIG_DIR = PROJECT_ASSETS_DIR / "config"
