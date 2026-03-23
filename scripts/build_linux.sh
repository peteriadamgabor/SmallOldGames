#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

ARCH="$(uname -m)"
BUNDLE_NAME="SmallOldGames"
ARCHIVE_NAME="SmallOldGames-linux-${ARCH}.tar.gz"

uv sync --extra build
uv run pyinstaller --noconfirm SmallOldGames.spec

# PyInstaller onefile mode outputs dist/SmallOldGames (executable).
# Stage into a directory for the archive.
STAGE_DIR="dist/${BUNDLE_NAME}-stage"
rm -rf "$STAGE_DIR"
mkdir -p "${STAGE_DIR}/${BUNDLE_NAME}/branding"
mv "dist/${BUNDLE_NAME}" "${STAGE_DIR}/${BUNDLE_NAME}/${BUNDLE_NAME}"
cp assets/branding/SmallOldGames.desktop "${STAGE_DIR}/${BUNDLE_NAME}/SmallOldGames.desktop"
cp assets/branding/smalloldgames.svg "${STAGE_DIR}/${BUNDLE_NAME}/branding/smalloldgames.svg"
cp assets/branding/sketch_hopper.svg "${STAGE_DIR}/${BUNDLE_NAME}/branding/sketch_hopper.svg"

tar -czf "dist/${ARCHIVE_NAME}" -C "$STAGE_DIR" "${BUNDLE_NAME}"
rm -rf "$STAGE_DIR"

echo
echo "Build complete."
echo "Archive: dist/${ARCHIVE_NAME}"
