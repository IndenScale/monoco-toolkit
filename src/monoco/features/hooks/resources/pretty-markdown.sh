#!/usr/bin/env bash
#
# ---
# type: agent
# provider: claude-code
# event: after-tool
# matcher:
#   - "WriteFile"
#   - "StrReplaceFile"
# priority: 100
# description: "Lint Markdown files after save and inject issues into Agent context"
# ---
#
# Pretty Markdown Hook
# 
# This hook runs after WriteFile or StrReplaceFile to check Markdown files
# for linting issues. It uses markdownlint to detect problems and injects
# the results into the Agent context for autonomous decision-making.
#
# Design Philosophy (L3 Agentic Mode):
# - Hook only collects information (lint results), does not make decisions
# - Injects problem context into Agent working memory
# - Agent combines with current task state to autonomously decide how to handle
#
# Issue Classification:
# - Format issues (prettier fixable): MD013, MD004, MD009, MD012
# - Content issues (Agent judgment): MD033, MD041, MD024, MD002, MD025

set -e

# Read input from stdin
INPUT=$(cat)

# Debug mode
if [[ "${MONOCO_HOOK_DEBUG}" == "1" || "${MONOCO_HOOK_DEBUG}" == "true" ]]; then
  echo "[pretty-markdown] Input: ${INPUT}" >&2
fi

# Extract file path from tool input
FILE_PATH=$(echo "${INPUT}" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    input_data = data.get('input', {})
    # Try different possible path fields
    path = input_data.get('path', '')
    if not path:
        # Try to extract from content if it's a string
        content = str(input_data)
        # Look for path in the content
        import re
        match = re.search(r'[\'\"]path[\'\"]\s*:\s*[\'\"]([^\'\"]+)[\'\"]', content)
        if match:
            path = match.group(1)
    print(path)
except Exception as e:
    print('', end='')
" 2>/dev/null || echo "")

if [[ -z "${FILE_PATH}" ]]; then
  # No path found, silently exit
  echo '{"decision": "allow"}'
  exit 0
fi

# Check if file is Markdown
if [[ ! "${FILE_PATH}" =~ \.(md|mdx)$ ]]; then
  # Not a markdown file, silently exit
  echo '{"decision": "allow"}'
  exit 0
fi

# Check if file exists
if [[ ! -f "${FILE_PATH}" ]]; then
  echo '{"decision": "allow"}'
  exit 0
fi

# Find project root (look for .monoco directory)
PROJECT_ROOT="$(pwd)"
DIR="$(dirname "${FILE_PATH}")"
while [[ "${DIR}" != "/" ]]; do
  if [[ -d "${DIR}/.monoco" ]]; then
    PROJECT_ROOT="${DIR}"
    break
  fi
  DIR="$(dirname "${DIR}")"
done

# Check if markdownlint is available
if ! command -v markdownlint &> /dev/null && ! npx markdownlint --version &> /dev/null 2>&1; then
  # markdownlint not available, silently allow
  if [[ "${MONOCO_HOOK_DEBUG}" == "1" || "${MONOCO_HOOK_DEBUG}" == "true" ]]; then
    echo "[pretty-markdown] markdownlint not found, skipping" >&2
  fi
  echo '{"decision": "allow"}'
  exit 0
fi

# Determine markdownlint command
MDL_CMD="markdownlint"
if ! command -v markdownlint &> /dev/null; then
  MDL_CMD="npx markdownlint"
fi

# Run markdownlint with JSON output
LINT_OUTPUT=""
LINT_EXIT=0
if ! LINT_OUTPUT=$(${MDL_CMD} --json "${FILE_PATH}" 2>/dev/null); then
  LINT_EXIT=$?
fi

# If no issues found, silently exit
if [[ -z "${LINT_OUTPUT}" ]] || [[ "${LINT_OUTPUT}" == "[]" ]]; then
  echo '{"decision": "allow"}'
  exit 0
fi

# Parse issues and classify them
# Format issues: MD013, MD004, MD009, MD012
# Content issues: MD033, MD041, MD024, MD002, MD025
FORMAT_RULES=("MD013" "MD004" "MD009" "MD012")
CONTENT_RULES=("MD033" "MD041" "MD024" "MD002" "MD025")

# Build context message for Agent
CONTEXT_MSG="📋 Markdown Lint Report: ${FILE_PATH}

The following issues were detected in the saved Markdown file:

\${LINT_OUTPUT}

---

**Issue Classification:**

| Rule | Type | Suggested Action |
|------|------|------------------|
"

# Parse JSON and build table
TABLE_ROWS=$(echo "${LINT_OUTPUT}" | python3 -c "
import sys, json

try:
    issues = json.load(sys.stdin)
    if not issues:
        sys.exit(0)
    
    format_rules = {'MD013', 'MD004', 'MD009', 'MD012'}
    content_rules = {'MD033', 'MD041', 'MD024', 'MD002', 'MD025'}
    
    for issue in issues:
        rule = issue.get('ruleNames', ['UNKNOWN'])[0] if issue.get('ruleNames') else 'UNKNOWN'
        line = issue.get('lineNumber', '?')
        desc = issue.get('ruleDescription', 'Unknown issue')
        
        if rule in format_rules:
            issue_type = 'Format'
            action = f'Run: prettier --write {issue.get(\"fileName\", \"\")}'
        elif rule in content_rules:
            issue_type = 'Content'
            action = 'Review and fix manually'
        else:
            issue_type = 'Other'
            action = 'Review'
        
        print(f'| {rule} (L{line}) | {issue_type} | {action} |')
        print(f'|      {desc} | | |')
except Exception as e:
    print(f'| Error parsing: {e} | | |')
" 2>/dev/null || echo "| (Error parsing lint output) | | |")

CONTEXT_MSG="${CONTEXT_MSG}${TABLE_ROWS}

---

**Quick Fix:**
If you want to auto-fix format issues, run:
\`\`\`bash
prettier --write \"${FILE_PATH}\"
\`\`\`
"

# Output the context message to stderr (injected into Agent context)
echo "" >&2
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
echo "${CONTEXT_MSG}" >&2
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" >&2
echo "" >&2

# Return allow decision - we don't block, just inform
# Agent will decide what to do based on the injected context
echo '{"decision": "allow", "message": "Markdown lint issues detected. See stderr for details."}'
exit 0
