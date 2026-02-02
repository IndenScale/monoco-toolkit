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

# Execute lint on each file
LINT_EXIT=0
for file in $STAGED_ISSUES; do
    $MONOCO_CMD issue lint "$file"
    if [ $? -ne 0 ]; then
        LINT_EXIT=1
    fi
done

if [ $LINT_EXIT -ne 0 ]; then
    echo ""
    echo "[Monoco] Issue lint failed. Please fix the errors above."
    echo "[Monoco] You can run 'monoco issue lint --fix' to attempt automatic fixes."
    exit $LINT_EXIT
fi

echo "[Monoco] Issue lint passed."
exit 0
