#!/bin/bash
# Ralph Loop Trigger Hook
# Triggers at tool call thresholds (150/175/200) OR content length threshold (400k chars)
# Skip with: export MONOCO_SKIP_RALPH=1

---
type: agent
provider: claude-code
event: PreToolUse
matcher: "*"
priority: 1
description: "Trigger Ralph Loop at context thresholds (150/175/200 tool calls or 400k chars)"
---

# Read input
INPUT=$(cat)
SESSION_ID=$(echo "$INPUT" | jq -r '.session_id')
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name')

# Skip if disabled
if [ -n "$MONOCO_SKIP_RALPH" ]; then
    exit 0
fi

# Only count specific tool types for call counting
case "$TOOL_NAME" in
    Bash|Write|Edit|Read|Glob|Grep|Task|WebFetch|WebSearch)
        ;;
    *)
        exit 0
        ;;
esac

# Counter directory
COUNTER_DIR="${TMPDIR:-/tmp}/monoco-ralph"
mkdir -p "$COUNTER_DIR"
COUNTER_FILE="$COUNTER_DIR/${SESSION_ID}.count"
LENGTH_FILE="$COUNTER_DIR/${SESSION_ID}.length"

# Read current stats
COUNT=$(cat "$COUNTER_FILE" 2>/dev/null || echo 0)
TOTAL_LENGTH=$(cat "$LENGTH_FILE" 2>/dev/null || echo 0)

# Increment call count
COUNT=$((COUNT + 1))
echo "$COUNT" > "$COUNTER_FILE"

# Issue detection from git branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "")
ISSUE_ID=""
if [[ "$CURRENT_BRANCH" =~ (FEAT|FIX|CHORE|EPIC)-[0-9]+ ]]; then
    ISSUE_ID="${BASH_REMATCH[0]}"
fi

# Thresholds
CALL_WARNING=150
CALL_CRITICAL=175
CALL_FORCE=200
LENGTH_FORCE=400000  # ~100k tokens (1 token ≈ 4 chars)

# ============================================================
# Check content length threshold first (most critical)
# ============================================================
if [ "$TOTAL_LENGTH" -ge "$LENGTH_FORCE" ]; then
    rm -f "$COUNTER_FILE" "$LENGTH_FILE"
    
    LAST_WORDS="Content length threshold reached (${TOTAL_LENGTH} chars ≈ ${TOTAL_LENGTH}/4 tokens). Issue: ${ISSUE_ID:-unknown}. Continuing work from current state."
    
    if [ -n "$ISSUE_ID" ]; then
        nohup sh -c "sleep 2 && monoco ralph --issue $ISSUE_ID --prompt '$LAST_WORDS'" > /dev/null 2>&1 &
    fi
    
    cat << EOF
{
  "continue": false,
  "stopReason": "[Ralph Loop Triggered] Content length threshold reached (${TOTAL_LENGTH} chars ≈ ${TOTAL_LENGTH}/4 tokens). ${ISSUE_ID:+Issue $ISSUE_ID }Successor agent spawning..."
}
EOF
    exit 0
fi

# Length warning at 300k (75%)
if [ "$TOTAL_LENGTH" -ge 300000 ] && [ "$TOTAL_LENGTH" -lt 300050 ]; then
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[Ralph Loop Warning] Content length: ${TOTAL_LENGTH} chars (~${TOTAL_LENGTH}/4 tokens). Context at ~75%. Consider wrapping up or preparing handoff."
  }
}
EOF
    exit 0
fi

# Length critical at 350k (87.5%)
if [ "$TOTAL_LENGTH" -ge 350000 ] && [ "$TOTAL_LENGTH" -lt 350050 ]; then
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[Ralph Loop Critical] Content length: ${TOTAL_LENGTH} chars (~${TOTAL_LENGTH}/4 tokens). Context at ~87.5%. Strongly recommend completing milestone or handoff."
  }
}
EOF
    exit 0
fi

# ============================================================
# Check tool call count thresholds
# ============================================================
if [ "$COUNT" -eq "$CALL_WARNING" ]; then
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[Ralph Loop Warning] Tool call count: $COUNT/200. Context at ~75%. Consider wrapping up current task or prepare for handoff."
  }
}
EOF
    exit 0
fi

if [ "$COUNT" -eq "$CALL_CRITICAL" ]; then
    cat << EOF
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "additionalContext": "[Ralph Loop Critical] Tool call count: $COUNT/200. Context at ~87.5%. Strongly recommend completing current milestone or initiating handoff soon."
  }
}
EOF
    exit 0
fi

if [ "$COUNT" -ge "$CALL_FORCE" ]; then
    rm -f "$COUNTER_FILE" "$LENGTH_FILE"
    
    LAST_WORDS="Tool call threshold reached (200 calls). Issue: ${ISSUE_ID:-unknown}. Continuing work from current state."
    
    if [ -n "$ISSUE_ID" ]; then
        nohup sh -c "sleep 2 && monoco ralph --issue $ISSUE_ID --prompt '$LAST_WORDS'" > /dev/null 2>&1 &
    fi
    
    cat << EOF
{
  "continue": false,
  "stopReason": "[Ralph Loop Triggered] Tool call threshold reached (200 calls). ${ISSUE_ID:+Issue $ISSUE_ID }Successor agent spawning..."
}
EOF
    exit 0
fi

exit 0
