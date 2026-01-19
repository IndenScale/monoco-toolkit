#!/bin/bash
# check_agents.sh - Diagnostic script for Monoco Agent Integrations
# Usage: ./check_agents.sh [output_file]

OUTPUT_FILE="$1"
# ISO 8601 format
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

# Helper function to check a command
check_command() {
    local cmd="$1"
    if command -v "$cmd" &> /dev/null; then
        local path=$(command -v "$cmd")
        echo "    available: true"
        echo "    path: \"$path\""
    else
        echo "    available: false"
        echo "    error: \"Binary not found in PATH\""
    fi
}

# Generate YAML content
generate_yaml() {
    echo "last_checked: \"$TIMESTAMP\""
    echo "providers:"

    echo "  gemini:"
    check_command "gemini"

    echo "  claude:"
    check_command "claude"

    echo "  qwen:"
    check_command "qwen"
}

if [ -n "$OUTPUT_FILE" ]; then
    # Ensure directory exists
    mkdir -p "$(dirname "$OUTPUT_FILE")"
    generate_yaml > "$OUTPUT_FILE"
else
    generate_yaml
fi
