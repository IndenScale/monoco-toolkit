import re
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
import secrets


def is_chinese(text: str) -> bool:
    """Check if the text contains at least one Chinese character."""
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def validate_content_language(content: str, source_lang: str) -> bool:
    """
    Check if content matches source language using simple heuristics.
    Returns True if matched or if detection is not supported for the lang.
    """
    if source_lang == "zh":
        return is_chinese(content)
    # For 'en', we generally allow everything but could be more strict.
    # Requirement is mainly about enforcing 'zh' when configured.
    return True


def get_memos_dir(issues_root: Path) -> Path:
    """
    Get the directory for memos.
    Convention: Sibling of Issues directory.
    """
    # issues_root is usually ".../Issues"
    return issues_root.parent / "Memos"


def get_inbox_path(issues_root: Path) -> Path:
    return get_memos_dir(issues_root) / "inbox.md"


def generate_memo_id() -> str:
    """Generate a short 6-char ID."""
    return secrets.token_hex(3)


def format_memo(uid: str, content: str, context: Optional[str] = None) -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"## [{uid}] {timestamp}"

    body = content.strip()

    if context:
        body = f"> **Context**: `{context}`\n\n{body}"

    return f"\n{header}\n{body}\n"


def add_memo(issues_root: Path, content: str, context: Optional[str] = None) -> str:
    """
    Append a memo to the inbox.
    Returns the generated UID.
    """
    inbox_path = get_inbox_path(issues_root)

    if not inbox_path.exists():
        inbox_path.parent.mkdir(parents=True, exist_ok=True)
        inbox_path.write_text("# Monoco Memos Inbox\n", encoding="utf-8")

    uid = generate_memo_id()
    entry = format_memo(uid, content, context)

    with inbox_path.open("a", encoding="utf-8") as f:
        f.write(entry)

    return uid


def list_memos(issues_root: Path) -> List[Dict[str, str]]:
    """
    Parse memos from inbox.
    """
    inbox_path = get_inbox_path(issues_root)
    if not inbox_path.exists():
        return []

    content = inbox_path.read_text(encoding="utf-8")

    # Regex to find headers: ## [uid] timestamp
    # We split by headers

    pattern = re.compile(r"^## \[([a-f0-9]+)\] (.*?)$", re.MULTILINE)

    memos = []
    matches = list(pattern.finditer(content))

    for i, match in enumerate(matches):
        uid = match.group(1)
        timestamp = match.group(2)

        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)

        body = content[start:end].strip()

        memos.append({"id": uid, "timestamp": timestamp, "content": body})

    return memos


def delete_memo(issues_root: Path, memo_id: str) -> bool:
    """
    Delete a memo by its ID.
    Returns True if deleted, False if not found.
    """
    inbox_path = get_inbox_path(issues_root)
    if not inbox_path.exists():
        return False

    content = inbox_path.read_text(encoding="utf-8")
    pattern = re.compile(r"^## \[([a-f0-9]+)\] (.*?)$", re.MULTILINE)

    matches = list(pattern.finditer(content))
    target_idx = -1
    for i, m in enumerate(matches):
        if m.group(1) == memo_id:
            target_idx = i
            break

    if target_idx == -1:
        return False

    # Find boundaries
    start = matches[target_idx].start()
    # Include the potential newline before the header if it exists
    if start > 0 and content[start - 1] == "\n":
        start -= 1

    if target_idx + 1 < len(matches):
        end = matches[target_idx + 1].start()
        # Back up if there's a newline before the next header that we should keep?
        # Actually, if we delete a memo, we should probably remove one "entry block".
        # Entry blocks are format_memo: \n## header\nbody\n
        # So we want to remove the leading \n and the trailing parts.
    else:
        end = len(content)

    new_content = content[:start] + content[end:]
    inbox_path.write_text(new_content, encoding="utf-8")
    return True
