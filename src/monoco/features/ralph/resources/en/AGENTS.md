## Ralph Loop

> **Reincarnation and relay triumphs over struggling in the mud.**

When the current Agent hits a bottleneck (insufficient context, local optimum trap, need for fresh perspective), launch a successor Agent to continue the Issue.

## Core Concepts

- **Last Words** - Key information left for the successor: completed work, current state, next steps suggestion
- **Relay, Not Restart** - The successor inherits Issue context and workspace, not starting from scratch
- **Graceful Handoff** - Triggered proactively when the current Agent judges efficiency is declining, not forced persistence

## Commands

- `monoco ralph --issue {issue-id} --prompt "{last-words}"` - Pass last words as string directly
- `monoco ralph --issue {issue-id} --path {last-words-file}` - Read last words from file (for long content)
- `monoco ralph --issue {issue-id}` - Let system auto-generate context summary as Last Words

## Auto-Trigger Mechanism

Ralph Loop automatically triggers when **either** condition is met (no human intervention needed):

### Tool Call Count

| Threshold | Behavior |
|-----------|----------|
| **150 calls** | Warning: Context ~75% used, suggest preparing to wrap up |
| **175 calls** | Critical warning: Context ~87.5% used, strongly recommend completing milestone or preparing handoff |
| **200 calls** | **Force handoff**: Auto-starts `monoco ralph`, current Agent session ends |

### Content Length Accumulation

Based on response character count (1 token ≈ 4 characters):

| Threshold | Behavior |
|-----------|----------|
| **300k chars** (~75k tokens) | Warning: Suggest preparing to wrap up |
| **350k chars** (~87.5k tokens) | Critical warning: Recommend completing or handing off soon |
| **400k chars** (~100k tokens) | **Force handoff**: Auto-starts `monoco ralph` |

### Tracked Tools

**Tool call counting** tracks:
- `Bash`, `Write`, `Edit`, `Read`
- `Glob`, `Grep`, `Task`
- `WebFetch`, `WebSearch`

**Content length** measures responses from:
- `Read`, `Glob`, `Grep`
- `WebFetch`, `WebSearch`

### Skip Mechanism

To temporarily disable auto-trigger (e.g., during critical atomic operations):

```bash
export MONOCO_SKIP_RALPH=1
```

With this set, even at thresholds, forced handoff will not occur.

## Workflow

1. **Self-Assessment**: Current Agent judges if hitting a bottleneck
   - Context window running low (auto-trigger handles this)
   - Multiple failed attempts on same problem
   - Feeling lost in details while missing the big picture

2. **Write Last Words**: Summarize key information
   - ✅ Completed work and verified results
   - ✅ Current code/file status
   - ✅ Obstacles encountered or uncertainties
   - ✅ Suggested next steps

3. **Execute Relay**: Run `monoco ralph` to launch successor Agent

4. **Smooth Transition**: Successor Agent reads Last Words and Issue context, continues推进

## Guidelines

### When to Use Ralph

| Suitable For | Not Suitable For |
|-------------|-----------------|
| Complex refactoring across many files | Simple bug fixes |
| Insufficient context window (auto-trigger) | Single-file changes |
| Multiple failed attempts, need fresh perspective | Almost done, just need finishing touches |
| Trapped in technical details, need global view | Verification tests |

### Last Words Best Practices

- **Be concise**: Focus on key information, not complete history
- **State-first**: Describe "where we are now" rather than "how we got here"
- **Clear direction**: Give the successor a clear next-step suggestion
- **Honest record**: Don't hide failed attempts, prevent successor from repeating mistakes

### After Relay

- Current Agent ends session normally
- Successor Agent launches in isolated environment, inherits Issue context
- No manual file sync needed, `monoco ralph` handles it automatically
