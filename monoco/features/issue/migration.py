import os
import re
import yaml
import hashlib
import secrets
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from .models import generate_uid

# Migration Mappings
DIR_MAP = {
    "STORIES": "Features",
    "Stories": "Features",
    "TASKS": "Chores",
    "Tasks": "Chores",
    "BUGS": "Fixes",
    "Bugs": "Fixes",
    "EPICS": "Epics",
    "Epics": "Epics",
    "features": "Features",
    "chores": "Chores",
    "fixes": "Fixes",
    "epics": "Epics"
}

TYPE_MAP = {
    "story": "feature",
    "task": "chore",
    "bug": "fix"
}

ID_PREFIX_MAP = {
    "STORY": "FEAT",
    "TASK": "CHORE",
    "BUG": "FIX"
}

def migrate_issues_directory(issues_dir: Path):
    """
    Core migration logic to upgrade an Issues directory to the latest Monoco standard.
    """
    if not issues_dir.exists():
        return

    # 1. Rename Directories
    for old_name, new_name in DIR_MAP.items():
        old_path = issues_dir / old_name
        if old_path.exists():
            new_path = issues_dir / new_name
            
            # Case sensitivity check for some filesystems
            same_inode = False
            try:
                if new_path.exists() and os.path.samefile(old_path, new_path):
                    same_inode = True
            except OSError:
                pass

            if same_inode:
                if old_path.name != new_path.name:
                    old_path.rename(new_path)
                continue

            if new_path.exists():
                import shutil
                for item in old_path.iterdir():
                    dest = new_path / item.name
                    if dest.exists() and item.is_dir():
                        for subitem in item.iterdir():
                            shutil.move(str(subitem), str(dest / subitem.name))
                        shutil.rmtree(item)
                    else:
                        shutil.move(str(item), str(dest))
                shutil.rmtree(old_path)
            else:
                old_path.rename(new_path)

    # 2. Rename Files and Update Content
    for subdir_name in ["Features", "Chores", "Fixes", "Epics"]:
        subdir = issues_dir / subdir_name
        if not subdir.exists():
            continue
            
        for file_path in subdir.rglob("*.md"):
            content = file_path.read_text(encoding="utf-8")
            new_content = content
            
            # Replace Type in Frontmatter
            for old_type, new_type in TYPE_MAP.items():
                new_content = re.sub(rf"^type:\s*{old_type}", f"type: {new_type}", new_content, flags=re.IGNORECASE | re.MULTILINE)
            
            # Replace ID Prefixes
            for old_prefix, new_prefix in ID_PREFIX_MAP.items():
                new_content = new_content.replace(f"[[{old_prefix}-", f"[[{new_prefix}-")
                new_content = re.sub(rf"^id: {old_prefix}-", f"id: {new_prefix}-", new_content, flags=re.MULTILINE)
                new_content = re.sub(rf"^parent: {old_prefix}-", f"parent: {new_prefix}-", new_content, flags=re.MULTILINE)
                new_content = new_content.replace(f"{old_prefix}-", f"{new_prefix}-")

            # Structural Updates (UID, Stage)
            match = re.search(r"^---(.*?)---", new_content, re.DOTALL | re.MULTILINE)
            if match:
                yaml_str = match.group(1)
                try:
                    data = yaml.safe_load(yaml_str) or {}
                    changed = False
                    
                    if 'uid' not in data:
                        data['uid'] = generate_uid()
                        changed = True
                        
                    if 'stage' in data and data['stage'] == 'todo':
                        data['stage'] = 'draft'
                        changed = True
                            
                    if changed:
                         new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
                         new_content = new_content.replace(match.group(1), "\n" + new_yaml)
                except yaml.YAMLError:
                    pass

            if new_content != content:
                file_path.write_text(new_content, encoding="utf-8")

            # Rename File
            filename = file_path.name
            new_filename = filename
            for old_prefix, new_prefix in ID_PREFIX_MAP.items():
                if filename.startswith(f"{old_prefix}-"):
                    new_filename = filename.replace(f"{old_prefix}-", f"{new_prefix}-", 1)
                    break
            
            if new_filename != filename:
                file_path.rename(file_path.parent / new_filename)
