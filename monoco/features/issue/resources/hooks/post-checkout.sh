#!/bin/sh
# Issue Feature Post-Checkout Hook
# Automatically syncs issue status when switching branches

echo "[Monoco] Syncing issue status after branch checkout..."

# Get the previous and current HEAD
PREVIOUS_HEAD="$1"
NEW_HEAD="$2"
BRANCH_SWITCH="$3"  # 1 if branch switch, 0 if file checkout

# Only sync on actual branch switches, not file checkouts
if [ "$BRANCH_SWITCH" != "1" ]; then
    echo "[Monoco] File checkout detected, skipping issue sync."
    exit 0
fi

# Get current branch name
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "HEAD")

echo "[Monoco] Switched to branch: $CURRENT_BRANCH"

# Try to extract issue ID from branch name
# Common patterns: FEAT-123, feat/FEAT-123, feature/FEAT-123, fix/FEAT-123
ISSUE_ID=$(echo "$CURRENT_BRANCH" | grep -oE '[A-Z]+-[0-9]+' | head -1)

if [ -n "$ISSUE_ID" ]; then
    echo "[Monoco] Detected issue ID from branch: $ISSUE_ID"

    # Check if issue exists and update its isolation ref if needed
    $MONOCO_CMD issue sync-isolation "$ISSUE_ID" --branch "$CURRENT_BRANCH" 2>/dev/null || true
fi

# Run general sync to ensure files field is up to date
echo "[Monoco] Running issue file sync..."
$MONOCO_CMD issue sync-files 2>/dev/null || true

echo "[Monoco] Issue sync complete."
exit 0
