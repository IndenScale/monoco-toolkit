import re
from pathlib import Path
from datetime import datetime


def parse_issue(file_path):
    content = file_path.read_text()
    match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
    if not match:
        return None

    fm_text = match.group(1)
    meta = {}
    # Simple line-based YAML parser for basic fields
    for line in fm_text.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip("'").strip('"')
            meta[key] = value
    return meta


def generate_changelog():
    # Use explicit absolute path or relative to project root
    root = Path(__file__).resolve().parent.parent
    closed_dir = root / "Issues" / "Features" / "closed"

    if not closed_dir.exists():
        print(f"Directory not found: {closed_dir}")
        return

    changes = []
    for f in closed_dir.glob("*.md"):
        meta = parse_issue(f)
        if meta and meta.get("status") == "closed":
            changes.append(
                {
                    "id": meta.get("id"),
                    "title": meta.get("title"),
                    "updated_at": meta.get("updated_at", ""),
                    "solution": meta.get("solution", ""),
                }
            )

    # Sort by ID descending
    changes.sort(key=lambda x: str(x["id"]), reverse=True)

    output = f"# Changelog\n\nGenerated on {datetime.now().strftime('%Y-%m-%d')}\n\n"
    output += "## [v0.3.2] - Recent Releases\n\n"

    for c in changes:
        output += f"### {c['id']}: {c['title']}\n"
        if c["solution"]:
            output += f"- *Result*: {c['solution']}\n"
        output += "\n"

    (root / "CHANGELOG.md").write_text(output)
    print(f"CHANGELOG.md updated with {len(changes)} entries.")


if __name__ == "__main__":
    generate_changelog()
