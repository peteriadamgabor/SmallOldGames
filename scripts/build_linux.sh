#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ARCH="$(uname -m)"
BUNDLE_NAME="SmallOldGames"
ARCHIVE_NAME="SmallOldGames-linux-${ARCH}.tar.gz"

uv sync --extra build
uv run pyinstaller --noconfirm SmallOldGames.spec

mkdir -p "dist/${BUNDLE_NAME}/branding"
cp assets/branding/SmallOldGames.desktop "dist/${BUNDLE_NAME}/SmallOldGames.desktop"
cp assets/branding/smalloldgames.svg "dist/${BUNDLE_NAME}/branding/smalloldgames.svg"
cp assets/branding/sketch_hopper.svg "dist/${BUNDLE_NAME}/branding/sketch_hopper.svg"

tar -czf "dist/${ARCHIVE_NAME}" -C dist "${BUNDLE_NAME}"

echo
echo "Build complete."
echo "Bundle: dist/${BUNDLE_NAME}/"
echo "Archive: dist/${ARCHIVE_NAME}"
