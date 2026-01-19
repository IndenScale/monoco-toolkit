import json
import sys
from pathlib import Path

# Ensure we can import monoco
sys.path.append(str(Path(__file__).parent.parent))

from monoco.features.issue.models import IssueMetadata


def export_schema():
    # Target is relative to Toolkit root if running from there, or relative to script
    # Let's anchor relative to this script
    script_dir = Path(__file__).parent
    toolkit_root = script_dir.parent
    target_dir = toolkit_root / "extensions" / "vscode" / "server" / "src" / "schema"
    target_dir.mkdir(parents=True, exist_ok=True)

    schema = IssueMetadata.model_json_schema()

    output_path = target_dir / "issue_schema.json"
    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"Exported Issue Metadata Schema to {output_path}")


if __name__ == "__main__":
    export_schema()
