#!/bin/bash
set -e

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$SCRIPT_DIR/.."
TARGET_VERSION=$1

echo "==========================================="
echo "🚀 Monoco Release Check"
echo "==========================================="

# 1. Verify Versions
echo ""
echo "🔍 [1/4] Verifying Versions..."
# Use uv run to ensure python environment, or just python3
uv run python "$SCRIPT_DIR/verify_versions.py" "$TARGET_VERSION"

# 2. Run CLI Tests
echo ""
echo "🧪 [2/4] Running CLI Tests (Python)..."
cd "$ROOT_DIR"
uv run pytest

# 3. Extension Check
echo ""
echo "🧩 [3/4] Checking VS Code Extension..."
cd "$ROOT_DIR/extensions/vscode"
# Ensure dependencies are installed (optional, can skip if known good, but safe for release)
# Use 'npm ci' if package-lock exists for clean install, or 'npm install'
npm install
npm run compile
npm run lint
echo "   ✅ Extension compiled and linted."

# 4. Kanban Check
echo ""
echo "📋 [4/4] Checking Kanban WebUI..."
cd "$ROOT_DIR/Kanban"
# Kanban root build triggers workspaces
npm install
npm run build
echo "   ✅ Kanban WebUI built."

echo ""
echo "✨ All checks passed! Ready for release."
