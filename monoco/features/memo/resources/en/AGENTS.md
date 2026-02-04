### Memo (Fleeting Notes)

Lightweight note-taking for ideas and quick thoughts. **Signal Queue Model** (FEAT-0165).

#### Signal Queue Semantics

- **Memo is a signal, not an asset** - Its value is in triggering action
- **File existence = signal pending** - Inbox has unprocessed memos
- **File cleared = signal consumed** - Memos are deleted after processing
- **Git is the archive** - History is in git, not app state

#### Commands

- **Add**: `monoco memo add "Content" [-c context]` - Create a signal
- **List**: `monoco memo list` - Show pending signals (consumed memos are in git history)
- **Delete**: `monoco memo delete <id>` - Manual delete (normally auto-consumed)
- **Open**: `monoco memo open` - Edit inbox directly

#### Workflow

1. Capture ideas as memos
2. When threshold (5) is reached, Architect is auto-triggered
3. Memos are consumed (deleted) and embedded in Architect's prompt
4. Architect creates Issues from memos
5. No need to "link" or "resolve" memos - they're gone after consumption

#### Guideline

- Use Memos for **fleeting ideas** - things that might become Issues
- Use Issues for **actionable work** - structured, tracked, with lifecycle
- Never manually link memos to Issues - if important, create an Issue
