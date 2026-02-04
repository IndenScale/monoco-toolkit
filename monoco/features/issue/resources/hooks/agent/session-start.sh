#!/bin/bash
# JIT Hook: session-start for Issue context injection
# Triggers: At the beginning of agent session
# Purpose: Inject current Issue context into agent session

---
type: agent
provider: claude-code
event: session-start
priority: 5
description: "Inject current Issue context into session"
---

# Get current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Try to extract Issue ID from branch name
if [[ "$CURRENT_BRANCH" =~ (FEAT|FIX|CHORE|EPIC)-[0-9]+ ]]; then
    ISSUE_ID="${BASH_REMATCH[0]}"
    
    # Try to find the Issue file
    ISSUE_FILE=$(find /Users/indenscale/Documents/Projects/Monoco/Toolkit/Issues -name "${ISSUE_ID}*.md" 2>/dev/null | head -1)
    
    if [[ -n "$ISSUE_FILE" && -f "$ISSUE_FILE" ]]; then
        # Extract issue metadata from front matter
        ISSUE_STATUS=$(grep -E "^status:" "$ISSUE_FILE" | head -1 | cut -d: -f2 | tr -d ' ' || echo "unknown")
        ISSUE_STAGE=$(grep -E "^stage:" "$ISSUE_FILE" | head -1 | cut -d: -f2 | tr -d ' ' || echo "unknown")
        ISSUE_TITLE=$(grep -E "^title:" "$ISSUE_FILE" | head -1 | cut -d: -f2- | sed 's/^ *//' || echo "unknown")
        
        cat << EOF
{
  "decision": "allow",
  "reason": "Issue context loaded",
  "message": "📋 Active Issue: $ISSUE_ID - $ISSUE_TITLE",
  "metadata": {
    "additionalContext": {
      "current_issue": "$ISSUE_ID",
      "issue_title": "$ISSUE_TITLE",
      "issue_status": "$ISSUE_STATUS",
      "issue_stage": "$ISSUE_STAGE",
      "current_branch": "$CURRENT_BRANCH",
      "reminders": [
        "Issue: $ISSUE_ID ($ISSUE_STATUS / $ISSUE_STAGE)",
        "Run 'monoco issue sync-files' after file modifications",
        "Run 'monoco issue submit $ISSUE_ID' when ready for review"
      ]
    }
  }
}
EOF
    else
        # Issue file not found
        cat << EOF
{
  "decision": "allow",
  "reason": "Partial context loaded",
  "message": "📋 Detected Issue ID: $ISSUE_ID from branch",
  "metadata": {
    "additionalContext": {
      "current_issue": "$ISSUE_ID",
      "current_branch": "$CURRENT_BRANCH",
      "reminders": [
        "Working on: $ISSUE_ID",
        "Run 'monoco issue sync-files' after file modifications"
      ]
    }
  }
}
EOF
    fi
else
    # Not on a feature branch
    cat << EOF
{
  "decision": "allow",
  "reason": "No active Issue detected",
  "message": "ℹ️ No active Issue detected from branch name",
  "metadata": {
    "additionalContext": {
      "current_branch": "$CURRENT_BRANCH",
      "reminders": [
        "To start working: monoco issue start <ID> --branch"
      ]
    }
  }
}
EOF
fi
