"""
Last-Word: Configuration Management.

Handles loading and saving of last-word configuration.
"""

from pathlib import Path
from typing import Optional

from .models import LastWordConfig, KnowledgeBaseConfig
from .core import get_config_path, get_last_word_dir, ensure_directories


def load_config() -> LastWordConfig:
    """
    Load last-word configuration.
    
    If config doesn't exist, creates default configuration.
    
    Returns:
        LastWordConfig instance
    """
    config_path = get_config_path()
    
    if not config_path.exists():
        # Create default config
        config = create_default_config()
        save_config(config)
        return config
    
    try:
        import yaml
        data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        return LastWordConfig(**data)
    except Exception:
        # If loading fails, return default
        return create_default_config()


def save_config(config: LastWordConfig) -> None:
    """
    Save configuration to file.
    
    Args:
        config: Configuration to save
    """
    ensure_directories()
    config_path = get_config_path()
    
    import yaml
    data = {
        "version": config.version,
        "global_agents": {
            "name": config.global_agents.name,
            "path": config.global_agents.path,
            "enabled": config.global_agents.enabled,
            "description": config.global_agents.description,
        },
        "soul": {
            "name": config.soul.name,
            "path": config.soul.path,
            "enabled": config.soul.enabled,
            "description": config.soul.description,
        },
        "user": {
            "name": config.user.name,
            "path": config.user.path,
            "enabled": config.user.enabled,
            "description": config.user.description,
        },
        "session_bootstrap": config.session_bootstrap,
        "max_retries": config.max_retries,
        "retry_base_delay": config.retry_base_delay,
        "retry_max_delay": config.retry_max_delay,
    }
    
    if config.project_knowledge:
        data["project_knowledge"] = {
            "name": config.project_knowledge.name,
            "path": config.project_knowledge.path,
            "enabled": config.project_knowledge.enabled,
            "description": config.project_knowledge.description,
        }
    
    config_path.write_text(
        yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
        encoding="utf-8"
    )


def create_default_config() -> LastWordConfig:
    """Create default configuration."""
    return LastWordConfig()


def get_project_knowledge_path(project_root: Optional[Path] = None) -> Optional[Path]:
    """
    Auto-detect project knowledge base path.
    
    Looks for AGENTS.md in:
    1. Provided project_root
    2. Current working directory
    3. Git repository root
    
    Args:
        project_root: Optional project root path
        
    Returns:
        Path to AGENTS.md if found, None otherwise
    """
    import os
    
    # Check provided root
    if project_root:
        agents_md = project_root / "AGENTS.md"
        if agents_md.exists():
            return agents_md
    
    # Check current directory
    cwd = Path.cwd()
    agents_md = cwd / "AGENTS.md"
    if agents_md.exists():
        return agents_md
    
    # Try to find git root
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            cwd=cwd,
        )
        if result.returncode == 0:
            git_root = Path(result.stdout.strip())
            agents_md = git_root / "AGENTS.md"
            if agents_md.exists():
                return agents_md
    except Exception:
        pass
    
    return None


def init_project_knowledge(project_root: Optional[Path] = None) -> Optional[KnowledgeBaseConfig]:
    """
    Initialize project knowledge base configuration.
    
    Args:
        project_root: Optional project root path
        
    Returns:
        KnowledgeBaseConfig if AGENTS.md found, None otherwise
    """
    agents_path = get_project_knowledge_path(project_root)
    
    if agents_path:
        return KnowledgeBaseConfig(
            name="project",
            path=str(agents_path),
            enabled=True,
            description="Project-specific context from AGENTS.md"
        )
    
    return None


def get_effective_config(project_root: Optional[Path] = None) -> LastWordConfig:
    """
    Get configuration with auto-detected project knowledge.
    
    Args:
        project_root: Optional project root path
        
    Returns:
        LastWordConfig with project knowledge if detected
    """
    config = load_config()
    
    # Auto-detect project knowledge
    project_kb = init_project_knowledge(project_root)
    if project_kb:
        config.project_knowledge = project_kb
    
    return config
