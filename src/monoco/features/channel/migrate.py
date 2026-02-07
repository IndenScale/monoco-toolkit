"""
Channel Configuration Migration - Migrate from .env to channels.yaml.

This module provides:
- Migration from .env file to channels.yaml
- Auto-detection of existing configurations
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from rich.console import Console
from rich.table import Table

from .models import DingtalkChannel, ChannelType
from .store import get_channel_store

logger = logging.getLogger(__name__)
console = Console()


def detect_env_config(project_root: Optional[Path] = None) -> Dict[str, str]:
    """
    Detect DingTalk configuration from .env file.

    Args:
        project_root: Project root directory (defaults to cwd)

    Returns:
        Dict of detected configuration values
    """
    if project_root is None:
        project_root = Path.cwd()

    env_path = project_root / ".env"
    config = {}

    if not env_path.exists():
        return config

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"\'')
                    config[key] = value
    except Exception as e:
        logger.warning(f"Failed to read .env file: {e}")

    return config


def parse_dingtalk_webhook(url: str) -> Tuple[str, str]:
    """
    Parse DingTalk webhook URL to extract token and keywords.

    Args:
        url: Full webhook URL

    Returns:
        Tuple of (webhook_url, keywords)
    """
    # Handle URLs with keywords parameter
    keywords = ""
    clean_url = url

    if "&keywords=" in url:
        parts = url.split("&keywords=")
        clean_url = parts[0]
        keywords = parts[1].split("&")[0]

    return clean_url, keywords


def migrate_from_env(
    project_root: Optional[Path] = None,
    dry_run: bool = False,
    channel_id: str = "dingtalk-default",
    channel_name: str = "DingTalk (migrated)",
) -> Tuple[bool, List[str]]:
    """
    Migrate configuration from .env to channels.yaml.

    Args:
        project_root: Project root directory
        dry_run: If True, only show what would be migrated
        channel_id: ID for the new channel
        channel_name: Name for the new channel

    Returns:
        Tuple of (success, messages)
    """
    messages = []

    # Detect .env config
    env_config = detect_env_config(project_root)

    if not env_config:
        messages.append("No .env configuration found")
        return False, messages

    # Look for DingTalk configuration
    webhook_url = env_config.get("DINGTALK_WEBHOOK_URL") or env_config.get("DINGTALK_WEBHOOK")
    secret = env_config.get("DINGTALK_SECRET") or env_config.get("DINGTALK_SECRET_KEY")

    if not webhook_url:
        messages.append("No DingTalk webhook URL found in .env")
        return False, messages

    # Parse URL
    clean_url, keywords = parse_dingtalk_webhook(webhook_url)

    # Check if already migrated
    store = get_channel_store()
    if store.exists(channel_id):
        messages.append(f"Channel '{channel_id}' already exists, skipping migration")
        return False, messages

    # Create channel
    channel = DingtalkChannel(
        id=channel_id,
        name=channel_name,
        webhook_url=clean_url,
        keywords=keywords,
        secret=secret or "",
    )

    if dry_run:
        messages.append("[DRY RUN] Would create channel:")
        messages.append(f"  ID: {channel_id}")
        messages.append(f"  Name: {channel_name}")
        messages.append(f"  Webhook: {clean_url[:50]}...")
        messages.append(f"  Keywords: {keywords or '(none)'}")
        messages.append(f"  Secret: {'(set)' if secret else '(none)'}")
        return True, messages

    # Save channel
    store.add(channel)
    messages.append(f"✓ Migrated DingTalk configuration to channel '{channel_id}'")

    # Optionally remove from .env (comment out)
    messages.append("Note: .env file not modified. You can manually remove:")
    messages.append("  - DINGTALK_WEBHOOK_URL")
    messages.append("  - DINGTALK_SECRET")

    return True, messages


def show_migration_status(project_root: Optional[Path] = None) -> None:
    """
    Show current migration status.

    Args:
        project_root: Project root directory
    """
    if project_root is None:
        project_root = Path.cwd()

    # Check .env
    env_config = detect_env_config(project_root)
    has_env_dingtalk = bool(
        env_config.get("DINGTALK_WEBHOOK_URL") or env_config.get("DINGTALK_WEBHOOK")
    )

    # Check channels.yaml
    store = get_channel_store()
    channels = store.list_all()
    dingtalk_channels = [c for c in channels if c.type == ChannelType.DINGTALK]

    # Display status
    table = Table(title="Channel Migration Status")
    table.add_column("Source", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Details")

    # .env status
    if has_env_dingtalk:
        table.add_row(
            ".env",
            "[yellow]Found[/yellow]",
            "DingTalk webhook URL detected",
        )
    else:
        table.add_row(
            ".env",
            "[dim]Not found[/dim]",
            "No DingTalk configuration in .env",
        )

    # channels.yaml status
    if dingtalk_channels:
        table.add_row(
            "channels.yaml",
            "[green]Configured[/green]",
            f"{len(dingtalk_channels)} DingTalk channel(s)",
        )
    else:
        table.add_row(
            "channels.yaml",
            "[dim]Empty[/dim]",
            "No DingTalk channels configured",
        )

    console.print(table)

    # Recommendations
    if has_env_dingtalk and not dingtalk_channels:
        console.print("\n[yellow]Recommendation:[/yellow] Run migration to move .env config to channels.yaml")
        console.print("  monoco channel migrate")
    elif dingtalk_channels:
        console.print("\n[green]✓[/green] Channel configuration is active")
