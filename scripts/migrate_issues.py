import os
import re
from pathlib import Path

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
    Path("."),
    Path("Chassis"),
    Path("Toolkit")
]

def migrate_root(root_path: Path):
    issues_dir = root_path / "ISSUES"
    if not issues_dir.exists():
        issues_dir = root_path / "Issues"
    
    if not issues_dir.exists():
        print(f"No ISSUES dir found in {root_path}")
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
                print(f"  Renaming {old_path} -> {new_path}")
                old_path.rename(new_path)

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
            
            # Replace Type in Frontmatter
            for old_type, new_type in TYPE_MAP.items():
                new_content = re.sub(rf"type:\s*{old_type}", f"type: {new_type}", new_content, flags=re.IGNORECASE)
            
            # Replace ID Prefixes in links and metadata
            for old_prefix, new_prefix in ID_PREFIX_MAP.items():
                # Replace [[STORY-123]] -> [[FEAT-123]]
                new_content = new_content.replace(f"[[{old_prefix}-", f"[[{new_prefix}-")
                # Replace id: STORY-123 -> id: FEAT-123
                new_content = new_content.replace(f"id: {old_prefix}-", f"id: {new_prefix}-")
                # Replace parent: STORY-123 -> parent: FEAT-123
                new_content = new_content.replace(f"parent: {old_prefix}-", f"parent: {new_prefix}-")
                 # Replace in dependencies: [STORY-123] -> [FEAT-123]
                new_content = new_content.replace(f"{old_prefix}-", f"{new_prefix}-")

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
