#!/bin/bash
# Ralph Loop Length Tracker
# Records content length from tool responses
# Used in conjunction with ralph-trigger.sh

---
type: agent
provider: claude-code
event: PostToolUse
matcher: "*"
priority: 1
description: "Track content length for Ralph Loop context monitoring"
---

INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

# Skip if disabled
if [ -n "$MONOCO_SKIP_RALPH" ]; then
    exit 0
fi

# Only track length for content-returning tools
case "$TOOL_NAME" in
    Read|Glob|Grep|WebFetch|WebSearch)
        ;;
    *)
        exit 0
        ;;
esac

COUNTER_DIR="${TMPDIR:-/tmp}/monoco-ralph"
mkdir -p "$COUNTER_DIR"
LENGTH_FILE="$COUNTER_DIR/${SESSION_ID}.length"

# Extract and measure response content
TOOL_RESPONSE=$(echo "$INPUT" | jq -r '.tool_response // empty')
if [ -n "$TOOL_RESPONSE" ]; then
    RESPONSE_LENGTH=${#TOOL_RESPONSE}
    CURRENT_LENGTH=$(cat "$LENGTH_FILE" 2>/dev/null || echo 0)
    NEW_LENGTH=$((CURRENT_LENGTH + RESPONSE_LENGTH))
    echo "$NEW_LENGTH" > "$LENGTH_FILE"
fi

exit 0
