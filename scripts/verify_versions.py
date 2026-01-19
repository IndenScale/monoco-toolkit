import json
import sys
from pathlib import Path

# Try importing tomllib (Python 3.11+), otherwise fallback
try:
    import tomllib
except ImportError:
    tomllib = None


def get_version_toml(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        if tomllib:
            data = tomllib.loads(content)
            return data["project"]["version"]
        else:
            # Simple fallback parser for [project] section
            lines = content.splitlines()
            in_project = False
            for line in lines:
                line = line.strip()
                if line == "[project]":
                    in_project = True
                    continue
                if line.startswith("[") and line != "[project]":
                    in_project = False

                if in_project and line.startswith("version"):
                    # version = "0.2.6"
                    return line.split("=")[1].strip().strip('"')
    return None


def get_version_json(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data["version"]


def main():
    # Helper to find root relative to this script
    script_dir = Path(__file__).resolve().parent
    root = script_dir.parent

    files = {
        "CLI": root / "pyproject.toml",
        "Extension": root / "extensions/vscode/package.json",
        "WebUI": root / "Kanban/apps/webui/package.json",
        "KanbanCore": root / "Kanban/packages/core/package.json",
        "KanbanCLI": root / "Kanban/packages/monoco-kanban/package.json",
    }

    versions = {}
    has_error = False

    print(f"{'Component':<15} | {'Version':<10} | {'Path'}")
    print("-" * 60)

    for name, path in files.items():
        if not path.exists():
            print(f"{name:<15} | {'MISSING':<10} | {path}")
            has_error = True
            continue

        if str(path).endswith(".toml"):
            v = get_version_toml(path)
        else:
            v = get_version_json(path)

        versions[name] = v
        print(f"{name:<15} | {v:<10} | {path.relative_to(root)}")

    print("-" * 60)

    # Check internal consistency
    unique_versions = set(versions.values())
    if len(unique_versions) > 1:
        print("\n❌ INTERNAL MISMATCH: All components must have the same version.")
        sys.exit(1)

    current_version = list(unique_versions)[0]

    # Check against target argument if provided
    target = sys.argv[1] if len(sys.argv) > 1 else None

    # Check git branch if no explicit target provided
    if not target:
        try:
            import subprocess

            branch = subprocess.check_output(
                ["git", "symbolic-ref", "--short", "HEAD"], text=True
            ).strip()
            if branch.startswith("release/v"):
                target = branch.replace("release/v", "")
                print(f"\n🔄 Auto-detected release target from branch: {target}")
        except Exception:
            pass

    if target:
        if current_version != target:
            print(f"\n❌ TARGET MISMATCH: Expected {target}, found {current_version}.")
            sys.exit(1)
        else:
            print(f"\n✅ Version verified: {current_version} (Matches target/branch)")
    else:
        print(f"\n✅ Consistent version: {current_version}")


if __name__ == "__main__":
    main()
