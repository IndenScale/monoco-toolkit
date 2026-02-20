"""
Last-Word: CLI Commands.

CLI interface for last-word operations:
- status: View pending updates
- apply: Manually trigger apply
- resolve: Resolve conflicts
- validate: Validate syntax
"""

from pathlib import Path
from typing import Optional

import click

from .core import (
    get_last_word_dir,
    get_staging_dir,
    list_staged,
    apply_yaml_to_markdown,
    process_session_end,
)
from .config import load_config, save_config, get_effective_config
from .models import LastWordSchema


@click.group(name="last-word")
def last_word_group():
    """Last-word: Session-end knowledge delta protocol."""
    pass


@last_word_group.command()
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Show detailed information"
)
def status(verbose: bool):
    """View pending updates and staging status."""
    config = load_config()
    staged = list_staged()
    
    click.echo("Last-Word Status")
    click.echo("=" * 40)
    
    # Show knowledge bases
    click.echo("\n📚 Knowledge Bases:")
    click.echo(f"  Global Agents: {config.global_agents.path}")
    click.echo(f"  Soul: {config.soul.path}")
    click.echo(f"  User: {config.user.path}")
    
    if config.project_knowledge:
        click.echo(f"  Project: {config.project_knowledge.path}")
    
    # Show session bootstrap
    click.echo(f"\n🚀 Session Bootstrap: {', '.join(config.session_bootstrap)}")
    
    # Show staged files
    click.echo(f"\n📦 Staged Files ({len(staged)}):")
    if staged:
        for sf in staged:
            click.echo(f"  - {sf.filename}")
            click.echo(f"    Target: {sf.target_file}")
            click.echo(f"    Created: {sf.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
            if verbose:
                try:
                    import yaml
                    data = yaml.safe_load(sf.path.read_text(encoding="utf-8"))
                    if "error" in data:
                        click.echo(f"    Error: {data['error']}")
                    entries = data.get("entries", [])
                    click.echo(f"    Entries: {len(entries)}")
                except Exception as e:
                    click.echo(f"    Error reading: {e}")
    else:
        click.echo("  No staged files")
    
    # Show pending YAML files
    yaml_files = list(get_last_word_dir().glob("kb-*.yaml"))
    click.echo(f"\n📝 Pending Updates ({len(yaml_files)}):")
    if yaml_files:
        for yf in sorted(yaml_files):
            try:
                schema = LastWordSchema.from_yaml(yf.read_text(encoding="utf-8"))
                click.echo(f"  - {yf.name}: {len(schema.entries)} entries")
            except Exception:
                click.echo(f"  - {yf.name}: (error reading)")
    else:
        click.echo("  No pending updates")


@last_word_group.command()
@click.option(
    "--dry-run", "-n",
    is_flag=True,
    help="Show what would be done without making changes"
)
@click.option(
    "--file", "target_file",
    type=str,
    help="Apply only updates for specific target file (e.g., USER.md)"
)
@click.option(
    "--all", "apply_all",
    is_flag=True,
    help="Apply all pending updates including staged"
)
def apply(dry_run: bool, target_file: Optional[str], apply_all: bool):
    """Apply pending updates to knowledge bases."""
    
    # Apply pending YAML files
    yaml_files = list(get_last_word_dir().glob("kb-*.yaml"))
    
    applied_count = 0
    failed_count = 0
    
    for yaml_path in sorted(yaml_files):
        try:
            # Check if this matches target filter
            if target_file:
                content = yaml_path.read_text(encoding="utf-8")
                schema = LastWordSchema.from_yaml(content)
                paths = [e.key.path for e in schema.entries]
                if not any(target_file in p for p in paths):
                    continue
            
            if dry_run:
                click.echo(f"Would apply: {yaml_path.name}")
                results = apply_yaml_to_markdown(yaml_path, dry_run=True)
                for r in results:
                    status = "✓" if r.success else "✗"
                    click.echo(f"  {status} {r.entry.key.heading}")
            else:
                click.echo(f"Applying: {yaml_path.name}")
                results = apply_yaml_to_markdown(yaml_path, dry_run=False)
                
                all_success = all(r.success for r in results)
                if all_success:
                    # Remove YAML file after successful apply
                    yaml_path.unlink()
                    click.echo(f"  ✓ Applied successfully, removed {yaml_path.name}")
                    applied_count += 1
                else:
                    failed_count += 1
                    for r in results:
                        if not r.success:
                            click.echo(f"  ✗ {r.entry.key.heading}: {r.error}")
        
        except Exception as e:
            click.echo(f"  ✗ Error processing {yaml_path.name}: {e}")
            failed_count += 1
    
    # Apply staged files if --all
    if apply_all:
        staged = list_staged()
        for sf in staged:
            try:
                if target_file and target_file not in sf.target_file:
                    continue
                
                if dry_run:
                    click.echo(f"Would apply staged: {sf.filename}")
                else:
                    click.echo(f"Applying staged: {sf.filename}")
                    results = apply_yaml_to_markdown(sf.path, dry_run=False)
                    
                    all_success = all(r.success for r in results)
                    if all_success:
                        sf.path.unlink()
                        click.echo(f"  ✓ Applied successfully")
                        applied_count += 1
                    else:
                        failed_count += 1
            except Exception as e:
                click.echo(f"  ✗ Error: {e}")
                failed_count += 1
    
    click.echo(f"\nSummary: {applied_count} applied, {failed_count} failed")


@last_word_group.command()
@click.argument("staged_file")
@click.option(
    "--edit", "-e",
    is_flag=True,
    help="Open in editor before applying"
)
def resolve(staged_file: str, edit: bool):
    """Resolve a staged conflict file."""
    staging_dir = get_staging_dir()
    
    # Find the staged file
    target_path = staging_dir / staged_file
    if not target_path.exists():
        # Try to find by prefix match
        matches = list(staging_dir.glob(f"*{staged_file}*"))
        if len(matches) == 1:
            target_path = matches[0]
        elif len(matches) > 1:
            click.echo(f"Multiple matches for '{staged_file}':")
            for m in matches:
                click.echo(f"  - {m.name}")
            return
        else:
            click.echo(f"Staged file not found: {staged_file}")
            return
    
    if edit:
        # Open in default editor
        import subprocess
        editor = os.environ.get("EDITOR", "vim")
        subprocess.run([editor, str(target_path)])
    
    # Ask for confirmation
    click.echo(f"Resolve {target_path.name}?")
    click.echo("This will apply the update and remove the staged file.")
    
    if click.confirm("Continue?"):
        results = apply_yaml_to_markdown(target_path, dry_run=False)
        
        all_success = all(r.success for r in results)
        if all_success:
            target_path.unlink()
            click.echo("✓ Resolved successfully")
        else:
            click.echo("✗ Some entries failed:")
            for r in results:
                if not r.success:
                    click.echo(f"  - {r.entry.key.heading}: {r.error}")


@last_word_group.command()
@click.argument("yaml_file")
def validate(yaml_file: str):
    """Validate a last-word YAML file."""
    path = Path(yaml_file)
    
    if not path.exists():
        # Try in last-word directory
        path = get_last_word_dir() / yaml_file
        if not path.exists():
            click.echo(f"File not found: {yaml_file}")
            return
    
    try:
        content = path.read_text(encoding="utf-8")
        schema = LastWordSchema.from_yaml(content)
        
        click.echo(f"✓ Valid YAML structure")
        click.echo(f"  Version: {schema.version}")
        click.echo(f"  Source: {schema.source or 'N/A'}")
        click.echo(f"  Entries: {len(schema.entries)}")
        
        # Validate entries
        from .core import validate_entries
        validation = validate_entries(schema.entries)
        
        if validation.has_errors:
            click.echo(f"\n✗ Validation errors ({len(validation.errors)}):")
            for e in validation.errors:
                click.echo(f"  - {e.entry.key.heading}: {e.error}")
        else:
            click.echo("\n✓ All entries valid")
        
        # Show entries
        if schema.entries:
            click.echo("\nEntries:")
            for entry in schema.entries:
                op_emoji = {
                    "no-op": "⏸",
                    "update": "📝",
                    "clear": "🧹",
                    "delete": "🗑",
                }.get(entry.operation.value, "❓")
                click.echo(f"  {op_emoji} {entry.key.heading} ({entry.operation.value})")
                click.echo(f"     Path: {entry.key.path}")
                if entry.meta.reason:
                    click.echo(f"     Reason: {entry.meta.reason}")
    
    except Exception as e:
        click.echo(f"✗ Invalid: {e}")


@last_word_group.command()
def init():
    """Initialize last-word configuration and directories."""
    from .core import ensure_directories
    
    ensure_directories()
    config = get_effective_config()
    save_config(config)
    
    click.echo("✓ Last-word initialized")
    click.echo(f"  Config: {get_last_word_dir() / 'config.yaml'}")
    click.echo(f"  Staging: {get_staging_dir()}")
    
    if config.project_knowledge:
        click.echo(f"\n📁 Detected project knowledge:")
        click.echo(f"  {config.project_knowledge.path}")


@last_word_group.command()
@click.option(
    "--session-id",
    type=str,
    help="Session identifier"
)
def flush(session_id: Optional[str]):
    """Process session buffer (for testing/hooks)."""
    result = process_session_end()
    
    click.echo(f"Status: {result['status']}")
    click.echo(f"Message: {result['message']}")
    
    if result.get('errors'):
        click.echo(f"\nErrors:")
        for e in result['errors']:
            click.echo(f"  - {e['entry']}: {e['error']}")
    
    if result.get('staged_files'):
        click.echo(f"\nStaged files:")
        for f in result['staged_files']:
            click.echo(f"  - {f}")
    
    if result.get('written'):
        click.echo(f"\nWritten files:")
        for f in result['written']:
            click.echo(f"  - {f}")


# Import os for the resolve command
import os  # noqa: E402

def register_commands(cli: click.Group) -> None:
    """Register last-word commands with the main CLI."""
    cli.add_command(last_word_group)
