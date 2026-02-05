#!/bin/sh
# ---
# type: git
# event: pre-push
# description: "Check for incomplete critical issues before pushing"
# priority: 100
# ---

echo "[Monoco] Checking critical issues before push..."

# Run the check using monoco command
monoco issue check-critical --fail-on-warning
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
    exit 0
fi

echo "[Monoco] ✓ No blocking critical issues found."
exit 0
