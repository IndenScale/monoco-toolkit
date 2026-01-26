#!/usr/bin/env python3
import sys
import re
from pathlib import Path


def update_version(file_path, new_version):
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {path}")
        return False

    content = path.read_text(encoding="utf-8")
    original_content = content

    if path.name == "pyproject.toml":
        # Match version = "x.y.z" specifically in the [project] section context roughly
        # But for simplicity and based on our file structure, looking for top-level version regex is usually safe options.
        # However, to be safer, we can loosely anchor.
        # The file has: version = "0.2.7"
        pattern = r'(^version\s*=\s*")[^"]+(")'
        # We need multiline mode usually if we use ^, but here we can just iterate.
        # Actually standard re.sub with multiline flag is good.
        content = re.sub(
            pattern, f"\\g<1>{new_version}\\g<2>", content, flags=re.MULTILINE
        )

    elif path.name == "package.json":
        # Match "version": "x.y.z"
        # We only want to replace the first occurrence which is the project version
        pattern = r'("version"\s*:\s*")[^"]+(")'
        content = re.sub(pattern, f"\\g<1>{new_version}\\g<2>", content, count=1)

    if content != original_content:
        path.write_text(content, encoding="utf-8")
        print(f"✅ Updated {path.relative_to(Path(__file__).parent.parent)}")
        return True
    else:
        print(
            f"⚠️  No changes or match found in {path.relative_to(Path(__file__).parent.parent)}"
        )
        return False


def main():
    if len(sys.argv) != 2:
        print("Usage: python set_version.py <new_version>")
        sys.exit(1)

    new_version = sys.argv[1]

    # Root dir relative to script
    root = Path(__file__).resolve().parent.parent

    files = [
        root / "pyproject.toml",
        root / "extensions/vscode/package.json",
        root / "Kanban/apps/webui/package.json",
        root / "Kanban/packages/core/package.json",
        root / "Kanban/packages/monoco-kanban/package.json",
        root / "site/package.json",
    ]

    print(f"🚀 Setting version to: {new_version}\n")

    success_count = 0
    for file_path in files:
        if update_version(file_path, new_version):
            success_count += 1

    print(f"\n✨ Updated {success_count} files.")


if __name__ == "__main__":
    main()
