#!/bin/bash
set -e

# Set local cache directories to avoid PermissionError in restricted environments
export XDG_DATA_HOME="$(pwd)/build/xdg_data"
export XDG_CACHE_HOME="$(pwd)/build/xdg_cache"
export XDG_CONFIG_HOME="$(pwd)/build/xdg_config"
export PYINSTALLER_CONFIG_DIR="$(pwd)/build/pyinstaller_config"

# Create directories
mkdir -p "$XDG_DATA_HOME" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME" "$PYINSTALLER_CONFIG_DIR"

SRC_DIR="monoco"
DIST_FILE="dist/monoco"
HASH_FILE="build/monoco.hash"

# Check for shasum or md5
if command -v shasum >/dev/null 2>&1; then
    HASH_CMD="shasum -a 256"
else
    HASH_CMD="md5"
fi

echo "Checking for changes..."

# Calculate hash of source files (content only)
# We sort file list to ensure deterministic order
# We include pyproject.toml as well since dependencies might change
# Use find to list files, sort them, cat content, and hash it
SRC_HASH=$(find "$SRC_DIR" -name "*.py" -type f -print0 | sort -z | xargs -0 cat | $HASH_CMD | awk '{print $1}')
CONF_HASH=$(cat pyproject.toml | $HASH_CMD | awk '{print $1}')
COMBINED_HASH=$(echo "${SRC_HASH}${CONF_HASH}" | $HASH_CMD | awk '{print $1}')

if [ -f "$DIST_FILE" ] && [ -f "$HASH_FILE" ]; then
    LAST_HASH=$(cat "$HASH_FILE")
    if [ "$COMBINED_HASH" == "$LAST_HASH" ]; then
        echo "No changes detected in source or configuration. Skipping build."
        exit 0
    fi
fi

echo "Changes detected or binary missing. Building Monoco CLI..."
echo "Using local cache at $(pwd)/build"

# Run PyInstaller via uv
# We use --clean to ensure fresh build and avoid stale cache issues
uv run --with pyinstaller pyinstaller \
    --name monoco \
    --onefile \
    --clean \
    --distpath ./dist \
    --workpath ./build \
    --specpath ./build \
    monoco/main.py

echo "Build complete. Binary is at Toolkit/dist/monoco"
echo "$COMBINED_HASH" > "$HASH_FILE"
