#!/bin/bash
# ---
# type: agent
# provider: claude-code
# event: before-tool
# matcher:
#   - Bash
# priority: 10
# description: "JIT Browser Guide and Availability Check"
# ---

# Read JSON input
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | jq -r '.input.command')
SESSION_ID=$(echo "$INPUT" | jq -r '.metadata.session_id')

# Only intercept agent-browser commands
if [[ "$COMMAND" == agent-browser* ]]; then
    # 1. Availability Check
    if ! command -v agent-browser &> /dev/null; then
        jq -n '{
            decision: "deny",
            reason: "agent-browser not installed",
            message: "🛑 agent-browser is missing. Please install it first: npm install -g agent-browser"
        }'
        exit 0
    fi

    # 2. Smart Help Injection (JIT)
    STATE_DIR="/tmp/monoco_browser_hooks"
    mkdir -p "$STATE_DIR"
    COUNTER_FILE="$STATE_DIR/counter_$SESSION_ID"
    
    count=0
    [ -f "$COUNTER_FILE" ] && count=$(cat "$COUNTER_FILE")
    count=$((count + 1))
    echo "$count" > "$COUNTER_FILE"
    
    # Show help on 1st, 16th... calls BEFORE execution
    if [ "$count" -eq 1 ] || [ $(( (count - 1) % 15 )) -eq 0 ]; then
        HELP=$(agent-browser --help 2>/dev/null | head -n 40)
        jq -n --arg help "$HELP" '{
            decision: "allow",
            message: "(Monoco JIT Guide)\n\($help)"
        }'
        exit 0
    fi
fi

# Allow by default
echo '{"decision": "allow"}'
