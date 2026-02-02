#!/bin/sh
# Issue Feature Pre-Commit Hook
# Runs monoco issue lint on staged Issue files

echo "[Monoco] Checking Issue integrity..."

# Get the list of staged Issue files
STAGED_ISSUES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^Issues/.*\.md$' || true)

if [ -z "$STAGED_ISSUES" ]; then
    echo "[Monoco] No Issue files staged. Skipping lint."
    exit 0
fi

# Run lint on staged Issue files
echo "[Monoco] Running lint on staged Issue files..."

# Build file list for monoco command
FILE_ARGS=""
for file in $STAGED_ISSUES; do
    FILE_ARGS="$FILE_ARGS $file"
done

# Execute lint
$MONOCO_CMD issue lint --files $FILE_ARGS
LINT_EXIT=$?

if [ $LINT_EXIT -ne 0 ]; then
    echo ""
    echo "[Monoco] Issue lint failed. Please fix the errors above."
    echo "[Monoco] You can run 'monoco issue lint --fix' to attempt automatic fixes."
    exit $LINT_EXIT
fi

echo "[Monoco] Issue lint passed."
exit 0
