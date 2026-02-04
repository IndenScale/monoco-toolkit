#!/bin/bash
# JIT Hook: before-tool for Issue workflow compliance
# Triggers: Bash, WriteFile tool calls
# Purpose: Check branch compliance before code modifications

---
type: agent
provider: claude-code
event: before-tool
matcher: ["Bash", "WriteFile"]
priority: 10
description: "Check code modification compliance (branch, sync-files)"
---

# Get current branch
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")

# Check if we're on a protected branch
if [[ "$CURRENT_BRANCH" == "main" || "$CURRENT_BRANCH" == "master" ]]; then
    cat << 'EOF'
{
  "decision": "ask",
  "reason": "Protected branch detected",
  "message": "🛑 You are currently on the main/master branch. Direct modifications are prohibited.",
  "metadata": {
    "additionalContext": {
      "current_branch": "main",
      "reminders": [
        "Use 'monoco issue start <ID> --branch' to create a feature branch",
        "Never modify code directly on main/master branch"
      ]
    }
  }
}
EOF
    exit 0
fi

# Check if branch name follows feature branch pattern (contains FEAT-, FIX-, CHORE-)
if [[ "$CURRENT_BRANCH" =~ (FEAT|FIX|CHORE)-[0-9]+ ]]; then
    ISSUE_ID="${BASH_REMATCH[0]}"
    
    # Check for uncommitted changes that might need sync-files
    if git diff --quiet HEAD 2>/dev/null; then
        # No uncommitted changes
        cat << EOF
{
  "decision": "allow",
  "reason": "Branch check passed",
  "message": "✅ Current in feature branch: $CURRENT_BRANCH",
  "metadata": {
    "additionalContext": {
      "current_issue": "$ISSUE_ID",
      "current_branch": "$CURRENT_BRANCH",
      "reminders": [
        "Run 'monoco issue sync-files' after modifying files",
        "Run 'monoco issue submit $ISSUE_ID' when ready for review"
      ]
    }
  }
}
EOF
    else
        # Has uncommitted changes
        cat << EOF
{
  "decision": "allow",
  "reason": "Branch check passed with pending changes",
  "message": "⚠️ You have uncommitted changes. Remember to run sync-files before submit.",
  "metadata": {
    "additionalContext": {
      "current_issue": "$ISSUE_ID",
      "current_branch": "$CURRENT_BRANCH",
      "uncommitted_changes": true,
      "reminders": [
        "Run 'monoco issue sync-files' to update files field",
        "Run 'monoco issue submit $ISSUE_ID' when ready for review"
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
  "decision": "ask",
  "reason": "Not on feature branch",
  "message": "⚠️ You are on '$CURRENT_BRANCH' which does not appear to be a feature branch.",
  "metadata": {
    "additionalContext": {
      "current_branch": "$CURRENT_BRANCH",
      "reminders": [
        "Use 'monoco issue start <ID> --branch' to work on an Issue",
        "Or ensure your branch name contains the Issue ID (e.g., FEAT-0123-xxx)"
      ]
    }
  }
}
EOF
fi
