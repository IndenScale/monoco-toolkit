#!/bin/sh
# Issue Feature Pre-Push Hook
# Checks for incomplete critical issues before pushing

echo "[Monoco] Checking critical issues before push..."

# Get the list of commits being pushed
# $1 = remote name, $2 = remote url (if available)
REMOTE="$1"
URL="$2"

# Check for high/critical issues that are not closed
# This uses monoco issue query to find open issues with high/critical criticality
echo "[Monoco] Scanning for incomplete critical issues..."

# Run the check using monoco command
$MONOCO_CMD issue check-critical --fail-on-warning
CHECK_EXIT=$?

if [ $CHECK_EXIT -eq 2 ]; then
    echo ""
    echo "[Monoco] ❌ Critical issues found! Push blocked."
    echo "[Monoco] Please close or resolve the critical issues above before pushing."
    exit 1
elif [ $CHECK_EXIT -eq 1 ]; then
    echo ""
    echo "[Monoco] ⚠️  High priority issues found."
    echo "[Monoco] Use --force-push to bypass this warning (not recommended)."
    # For now, we allow the push but warn
    # To block, change the exit code to 1
    exit 0
fi

echo "[Monoco] ✓ No blocking critical issues found."
exit 0
