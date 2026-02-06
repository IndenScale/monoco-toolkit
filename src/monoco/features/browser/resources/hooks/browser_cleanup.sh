#!/bin/bash
# ---
# type: agent
# provider: claude-code
# event: session-end
# priority: 99
# description: "Cleanup session-specific browser state"
# ---

# Read JSON input
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.metadata.session_id')

STATE_DIR="/tmp/monoco_browser_hooks"
COUNTER_FILE="$STATE_DIR/counter_$SESSION_ID"

if [ -f "$COUNTER_FILE" ]; then
    rm "$COUNTER_FILE"
fi

# Try to remove directory if empty
[ -d "$STATE_DIR" ] && [ -z "$(ls -A "$STATE_DIR" 2>/dev/null)" ] && rm -rf "$STATE_DIR"

echo '{"decision": "allow"}'
