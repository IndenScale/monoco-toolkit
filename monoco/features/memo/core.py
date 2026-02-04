import re
from pathlib import Path
from typing import List, Optional, Any
import secrets
from datetime import datetime

from .models import Memo

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
    return True


def get_memos_dir(issues_root: Path) -> Path:
    """
    Get the directory for memos.
    Convention: Sibling of Issues directory.
    """
    return issues_root.parent / "Memos"

def get_inbox_path(issues_root: Path) -> Path:
    return get_memos_dir(issues_root) / "inbox.md"

def generate_memo_id() -> str:
    """Generate a short 6-char ID."""
    return secrets.token_hex(3)

def parse_memo_block(block: str) -> Optional[Memo]:
    """
    Parse a text block into a Memo object.
    
    Signal Queue Model (FEAT-0165):
    - No status field parsing (file existence is the state)
    - No ref field parsing (traceability via git history)
    
    Block format:
    ## [uid] YYYY-MM-DD HH:MM:SS
    - **Key**: Value
    ...
    Content
    """
    lines = block.strip().split("\n")
    if not lines:
        return None
        
    header = lines[0]
    match = re.match(r"^## \[([a-f0-9]+)\] (.*?)$", header)
    if not match:
        return None
        
    uid = match.group(1)
    ts_str = match.group(2)
    try:
        timestamp = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        timestamp = datetime.now() # Fallback

    content_lines = []
    metadata = {}
    
    # Simple state machine
    # 0: Header (done)
    # 1: Metadata
    # 2: Content
    
    state = 1
    
    for line in lines[1:]:
        stripped = line.strip()
        if state == 1:
            if not stripped:
                continue
            # Check for metadata line: - **Key**: Value
            meta_match = re.match(r"^\- \*\*([a-zA-Z]+)\*\*: (.*)$", stripped)
            if meta_match:
                key = meta_match.group(1).lower()
                val = meta_match.group(2).strip()
                metadata[key] = val
            else:
                # First non-metadata line marks start of content
                state = 2
                content_lines.append(line)
        elif state == 2:
            content_lines.append(line)
            
    content = "\n".join(content_lines).strip()
        
    return Memo(
        uid=uid,
        timestamp=timestamp,
        content=content,
        author=metadata.get("from", "User"),
        source=metadata.get("source", "cli"),
        type=metadata.get("type", "insight"),
        context=metadata.get("context")
    )

def load_memos(issues_root: Path) -> List[Memo]:
    """
    Parse all memos from inbox.
    """
    inbox_path = get_inbox_path(issues_root)
    if not inbox_path.exists():
        return []

    content = inbox_path.read_text(encoding="utf-8")
    
    # Split by headers: ## [uid]
    # We use a lookahead or just standard split carefully
    parts = re.split(r"(^## \[)", content, flags=re.MULTILINE)[1:] # Skip preamble
    
    # parts will be like: ['## [', 'abc] 2023...\n...', '## [', 'def] ...']
    # Reassemble pairs
    blocks = []
    for i in range(0, len(parts), 2):
        if i+1 < len(parts):
            blocks.append(parts[i] + parts[i+1])
            
    memos = []
    for block in blocks:
        memo = parse_memo_block(block)
        if memo:
            memos.append(memo)
            
    # Sort by timestamp desc? Or keep file order? File order is usually append (time asc).
    return memos

def save_memos(issues_root: Path, memos: List[Memo]) -> None:
    """
    Rewrite the inbox file with the given list of memos.
    """
    inbox_path = get_inbox_path(issues_root)
    
    # Header
    lines = ["# Monoco Memos Inbox", ""]
    
    for memo in memos:
        lines.append(memo.to_markdown().strip())
        lines.append("") # Spacer
        
    inbox_path.write_text("\n".join(lines), encoding="utf-8")


def add_memo(
    issues_root: Path, 
    content: str, 
    context: Optional[str] = None,
    author: str = "User",
    source: str = "cli",
    memo_type: str = "insight"
) -> str:
    """
    Append a memo to the inbox.
    Returns the generated UID.
    """
    uid = generate_memo_id()
    memo = Memo(
        uid=uid,
        content=content,
        context=context,
        author=author,
        source=source,
        type=memo_type
    )
    
    # Append mode is more robust against concurrent reads than rewrite, 
    # but for consistent formatting we might want to just append string.
    inbox_path = get_inbox_path(issues_root)
    
    if not inbox_path.exists():
        inbox_path.parent.mkdir(parents=True, exist_ok=True)
        inbox_path.write_text("# Monoco Memos Inbox\n\n", encoding="utf-8")
        
    with inbox_path.open("a", encoding="utf-8") as f:
        f.write("\n" + memo.to_markdown().strip() + "\n")
        
    return uid

def delete_memo(issues_root: Path, memo_id: str) -> bool:
    """
    Delete a memo by its ID.
    """
    memos = load_memos(issues_root)
    initial_count = len(memos)
    memos = [m for m in memos if m.uid != memo_id]
    
    if len(memos) < initial_count:
        save_memos(issues_root, memos)
        return True
    return False

# Compatibility shim
list_memos = load_memos