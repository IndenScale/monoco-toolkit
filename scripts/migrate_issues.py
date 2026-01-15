import os
import re
import yaml
import hashlib
import secrets
from pathlib import Path
from datetime import datetime

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
    "features": "Features", # Handle lowercase just in case
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

ROOTS = [
    Path("/Users/indenscale/Documents/Projects/Monoco"),
    Path("/Users/indenscale/Documents/Projects/Monoco/Chassis"),
    Path("/Users/indenscale/Documents/Projects/Monoco/Toolkit")
]

def generate_uid() -> str:
    """
    Generate a globally unique 6-character short hash for issue identity.
    Uses timestamp + random bytes to ensure uniqueness across projects.
    """
    timestamp = str(datetime.now().timestamp()).encode()
    random_bytes = secrets.token_bytes(8)
    combined = timestamp + random_bytes
    hash_digest = hashlib.sha256(combined).hexdigest()
    return hash_digest[:6]

def migrate_root(root_path: Path):
    issues_dir = root_path / "Issues"
    # Fallback to check if ISSUES exists and migrate logic if needed, but for now we assume Issues
    if not issues_dir.exists():
        if (root_path / "ISSUES").exists():
             issues_dir = root_path / "ISSUES"
        else:
             print(f"[{root_path}] No Issues dir found. Skipping.")
             return

    print(f"Migrating {issues_dir}...")

    # 1. Rename Directories
    for old_name, new_name in DIR_MAP.items():
        old_path = issues_dir / old_name
        if old_path.exists():
            new_path = issues_dir / new_name
            # Check if they point to the same inode
            same_inode = False
            try:
                if old_path.exists() and new_path.exists() and os.path.samefile(old_path, new_path):
                    same_inode = True
            except OSError:
                pass

            if same_inode:
                # If they are the same directory but names differ (case change), just rename
                if old_path.name != new_path.name:
                    print(f"  Fixing case {old_path.name} -> {new_path.name}")
                    old_path.rename(new_path)
                continue

            if new_path.exists():
                # True merge (different directories)
                print(f"  Merging {old_path} -> {new_path}")
                import shutil
                for item in old_path.iterdir():
                    dest = new_path / item.name
                    if dest.exists() and item.is_dir():
                        for subitem in item.iterdir():
                            shutil.move(str(subitem), str(dest / subitem.name))
                        import shutil
                        shutil.rmtree(item)
                    else:
                        shutil.move(str(item), str(dest))
                # Cleanup old dir
                import shutil
                shutil.rmtree(old_path)
            else:
                try:
                    print(f"  Renaming {old_path} -> {new_path}")
                    old_path.rename(new_path)
                except OSError as e:
                    print(f"  Warning: Could not rename {old_path}: {e}")

    # 2. Rename Files and Update Content
    # We now operate on the NEW directory names
    for subdir_name in ["Features", "Chores", "Fixes", "Epics"]:
        subdir = issues_dir / subdir_name
        if not subdir.exists():
            continue
            
        for file_path in subdir.rglob("*.md"):
            # Update Content first
            content = file_path.read_text()
            new_content = content
            
            # --- Regex based replacements for Type and Links ---
            
            # Replace Type in Frontmatter
            for old_type, new_type in TYPE_MAP.items():
                new_content = re.sub(rf"^type:\s*{old_type}", f"type: {new_type}", new_content, flags=re.IGNORECASE | re.MULTILINE)
            
            # Replace ID Prefixes in links and metadata
            for old_prefix, new_prefix in ID_PREFIX_MAP.items():
                # Replace [[STORY-123]] -> [[FEAT-123]]
                new_content = new_content.replace(f"[[{old_prefix}-", f"[[{new_prefix}-")
                # Replace id: STORY-123 -> id: FEAT-123
                new_content = re.sub(rf"^id: {old_prefix}-", f"id: {new_prefix}-", new_content, flags=re.MULTILINE)
                # Replace parent: STORY-123 -> parent: FEAT-123
                new_content = re.sub(rf"^parent: {old_prefix}-", f"parent: {new_prefix}-", new_content, flags=re.MULTILINE)
                 # Replace in dependencies: [STORY-123] -> [FEAT-123]
                new_content = new_content.replace(f"{old_prefix}-", f"{new_prefix}-")

            # --- YAML Parsing for Structural Updates (UID, Stage) ---
            match = re.search(r"^---(.*?)---", new_content, re.DOTALL | re.MULTILINE)
            if match:
                yaml_str = match.group(1)
                try:
                    data = yaml.safe_load(yaml_str) or {}
                    changed = False
                    
                    # 1. Backfill UID
                    if 'uid' not in data:
                        data['uid'] = generate_uid()
                        changed = True
                        print(f"  Backfilling UID for {file_path.name}")
                        
                    # 2. Migrate Stage: todo -> draft
                    if 'stage' in data:
                        if data['stage'] == 'todo':
                            data['stage'] = 'draft'
                            changed = True
                            print(f"  Migrating stage todo->draft for {file_path.name}")
                            
                    if changed:
                         # Re-serialize YAML
                         # We want to preserve comments if possible, but safe_dump kills them.
                         # Since we are automating, re-dumping is acceptable collateral.
                         new_yaml = yaml.dump(data, sort_keys=False, allow_unicode=True)
                         new_content = new_content.replace(match.group(1), "\n" + new_yaml)
                except yaml.YAMLError:
                    print(f"  Warning: Invalid YAML in {file_path}")

            if new_content != content:
                print(f"  Updating content in {file_path}")
                file_path.write_text(new_content)

            # Rename File
            filename = file_path.name
            new_filename = filename
            for old_prefix, new_prefix in ID_PREFIX_MAP.items():
                if filename.startswith(f"{old_prefix}-"):
                    new_filename = filename.replace(f"{old_prefix}-", f"{new_prefix}-", 1)
                    break
            
            if new_filename != filename:
                new_file_path = file_path.parent / new_filename
                print(f"  Renaming file {filename} -> {new_filename}")
                file_path.rename(new_file_path)

if __name__ == "__main__":
    for root in ROOTS:
        migrate_root(root.resolve())
