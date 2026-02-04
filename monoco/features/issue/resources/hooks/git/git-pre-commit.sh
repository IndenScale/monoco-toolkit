#!/bin/sh
# ---
# type: git
# event: pre-commit
# matcher:
#   - "Issues/**/*.md"
# description: "Lint staged Issue files for integrity"
# priority: 100
# ---

echo "[Monoco] Checking Issue integrity..."

# Get the list of staged Issue files
STAGED_ISSUES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^Issues/.*\.md$' || true)

if [ -z "$STAGED_ISSUES" ]; then
    exit 0
fi

# Run lint on staged Issue files
echo "[Monoco] Running lint on staged Issue files..."

for file in $STAGED_ISSUES; do
    monoco issue lint "$file"
    if [ $? -ne 0 ]; then
        exit 1
    fi
done

echo "[Monoco] Issue lint passed."
exit 0
