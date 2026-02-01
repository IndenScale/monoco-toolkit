import os
import re
import yaml
from pathlib import Path
from datetime import datetime

ISSUES_ROOT = Path("Issues")

def parse_date(date_str):
    if not date_str:
        return None
    # Handle various date formats if necessary
    try:
        if isinstance(date_str, datetime):
            return date_str
        return datetime.fromisoformat(str(date_str).replace('Z', '+00:00'))
    except ValueError:
        return None

def archive_issues():
    count = 0
    # Iterate over all types: Epics, Features, Fixes, Chores
    for type_dir in ISSUES_ROOT.iterdir():
        if not type_dir.is_dir() or type_dir.name.startswith("."):
            continue
        
        closed_dir = type_dir / "closed"
        if not closed_dir.exists():
            continue
            
        archived_dir = type_dir / "archived"
        archived_dir.mkdir(exist_ok=True)
        
        for issue_file in closed_dir.glob("*.md"):
            try:
                content = issue_file.read_text()
                match = re.search(r"^---(.*?)---", content, re.DOTALL | re.MULTILINE)
                if not match:
                    continue
                
                fm_text = match.group(1)
                data = yaml.safe_load(fm_text)
                
                updated_at = parse_date(data.get("updated_at"))
                created_at = parse_date(data.get("created_at"))
                
                # Logic: Archive if updated before 2026 OR created in 2025 and closed
                # Let's strictly follow: updated_at < 2026-01-01
                cutoff_date = datetime(2026, 1, 1)
                
                target_date = updated_at or created_at
                
                if target_date and target_date < cutoff_date:
                    print(f"Archiving {issue_file.name} ({target_date})")
                    
                    # Update status in content
                    new_fm_text = fm_text.replace("status: closed", "status: archived")
                    # If status: closed was not found (maybe Status: Closed), try regex or just data update
                    # For safety, let's just do a string replace if simple, else re-dump
                    if "status: closed" not in fm_text and "status: active" not in fm_text:
                         # Fallback re-dump might be safer but changes formatting. 
                         # Let's try simple replace first as toolkit uses "status: closed"
                         pass

                    new_content = content.replace(fm_text, new_fm_text)
                    
                    # Move file
                    target_path = archived_dir / issue_file.name
                    target_path.write_text(new_content)
                    issue_file.unlink()
                    count += 1
            except Exception as e:
                print(f"Error processing {issue_file.name}: {e}")

    print(f"Archived {count} issues.")

if __name__ == "__main__":
    archive_issues()
