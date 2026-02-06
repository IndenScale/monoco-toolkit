#!/bin/bash
set -e

echo "=== Monoco Installer ==="

# Check Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is required but not found."
    exit 1
fi

# Detect directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Virtual Environment Setup
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [ ! -d ".venv" ]; then
        echo "Creating virtual environment (.venv)..."
        python3 -m venv .venv
    fi
    echo "Activating .venv..."
    source .venv/bin/activate
else
    echo "Using active virtual environment: $VIRTUAL_ENV"
fi

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip -q

# Install Package
echo "Installing Monoco..."
pip install -e .

# Verify Installation
if command -v monoco &> /dev/null; then
    echo ""
    echo "✅ Installation Successful!"
    echo ""
    echo "To start using Monoco:"
    echo "1. Activate the environment: source .venv/bin/activate"
    echo "2. Initialize workspace:     monoco init"
    echo "3. Start the daemon:         monoco serve"
else
    echo "❌ Installation failed. 'monoco' command not found."
    exit 1
fi
