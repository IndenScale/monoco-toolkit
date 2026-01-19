import typer
from pathlib import Path
from typing import Optional, List
from monoco.core.registry import FeatureRegistry
from monoco.core.injection import PromptInjector
from monoco.core.config import get_config
from monoco.core.skills import SkillManager
from monoco.core.integrations import get_active_integrations
from rich.console import Console

console = Console()


def _get_targets(root: Path, config, cli_target: Optional[Path]) -> List[Path]:
    """Helper to determine target files."""
    targets = []

    # 1. CLI Target
    if cli_target:
        targets.append(cli_target)
        return targets

    # 2. Config Targets
    if config.agent.targets:
        for t in config.agent.targets:
            targets.append(root / t)
        return targets

    # 3. Registry Defaults (Dynamic Detection)
    integrations = get_active_integrations(
        root, config_overrides=config.agent.integrations, auto_detect=True
    )

    if integrations:
        for integration in integrations.values():
            targets.append(root / integration.system_prompt_file)
    else:
        # Fallback to standard Monoco header if nothing is detected
        # but we usually want at least one target for a generic sync.
        defaults = ["GEMINI.md", "CLAUDE.md"]
        targets.extend([root / fname for fname in defaults])

    return list(set(targets))  # Unique paths


def sync_command(
    ctx: typer.Context,
    target: Optional[Path] = typer.Option(
        None,
        "--target",
        "-t",
        help="Specific file to update (default: auto-detect from config or standard files)",
    ),
    check: bool = typer.Option(False, "--check", help="Dry run check mode"),
):
    """
    Synchronize Agent Environment (System Prompts & Skills).
    Aggregates prompts from all active features and injects them into the agent configuration files.
    """
    root = Path.cwd()  # TODO: Use workspace root detection properly if needed

    # 0. Load Config
    config = get_config(str(root))

    # 1. Register Features
    registry = FeatureRegistry()
    registry.load_defaults()

    # 2. Collect Data
    collected_prompts = {}

    # Filter features based on config if specified
    all_features = registry.get_features()
    active_features = []

    if config.agent.includes:
        for f in all_features:
            if f.name in config.agent.includes:
                active_features.append(f)
    else:
        active_features = all_features

    with console.status("[bold green]Collecting feature integration data...") as status:
        for feature in active_features:
            status.update(f"Scanning Feature: {feature.name}")
            try:
                data = feature.integrate(root, config.model_dump())
                if data:
                    if data.system_prompts:
                        collected_prompts.update(data.system_prompts)
            except Exception as e:
                console.print(
                    f"[red]Error integrating feature {feature.name}: {e}[/red]"
                )

    console.print(
        f"[blue]Collected {len(collected_prompts)} prompts from {len(active_features)} features.[/blue]"
    )

    # 3. Distribute Skills
    console.print("[bold blue]Distributing skills to agent frameworks...[/bold blue]")

    # Determine language from config
    skill_lang = config.i18n.source_lang if config.i18n.source_lang else "en"
    console.print(f"[dim]  Using language: {skill_lang}[/dim]")

    # Initialize SkillManager with active features
    skill_manager = SkillManager(root, active_features)

    # Get active integrations
    integrations = get_active_integrations(
        root, config_overrides=config.agent.integrations, auto_detect=True
    )

    if integrations:
        for framework_key, integration in integrations.items():
            skill_target_dir = root / integration.skill_root_dir
            console.print(
                f"[dim]  Distributing to {integration.name} ({skill_target_dir})...[/dim]"
            )

            try:
                # Distribute only the configured language version
                results = skill_manager.distribute(
                    skill_target_dir, lang=skill_lang, force=False
                )
                success_count = sum(1 for v in results.values() if v)
                console.print(
                    f"[green]  ✓ Distributed {success_count}/{len(results)} skills to {integration.name}[/green]"
                )
            except Exception as e:
                console.print(
                    f"[red]  Failed to distribute skills to {integration.name}: {e}[/red]"
                )
    else:
        console.print(
            "[yellow]No agent frameworks detected. Skipping skill distribution.[/yellow]"
        )

    # 4. Determine Targets
    targets = _get_targets(root, config, target)

    # Ensure targets exist for sync
    final_targets = []
    for t in targets:
        if not t.exists():
            # If explicit target, fail? Or create?
            # If default, create.
            if target:
                # CLI target
                console.print(f"[yellow]Creating {t.name}...[/yellow]")
                try:
                    t.touch()
                    final_targets.append(t)
                except Exception as e:
                    console.print(f"[red]Failed to create {t}: {e}[/red]")
            else:
                # Default/Config target -> only create if it's one of the defaults we manage?
                # For now, let's just create it to be safe, assuming user wants it.
                console.print(f"[yellow]Creating {t.name}...[/yellow]")
                try:
                    t.touch()
                    final_targets.append(t)
                except Exception as e:
                    console.print(f"[red]Failed to create {t}: {e}[/red]")
        else:
            final_targets.append(t)

    # 5. Inject System Prompts
    for t in final_targets:
        injector = PromptInjector(t)

        if check:
            console.print(f"[dim][Dry Run] Would check/update {t.name}[/dim]")
        else:
            try:
                changed = injector.inject(collected_prompts)
                if changed:
                    console.print(f"[green]✓ Updated {t.name}[/green]")
                else:
                    console.print(f"[dim]= {t.name} is up to date[/dim]")
            except Exception as e:
                console.print(f"[red]Failed to update {t.name}: {e}[/red]")


def uninstall_command(
    ctx: typer.Context,
    target: Optional[Path] = typer.Option(
        None,
        "--target",
        "-t",
        help="Specific file to clean (default: auto-detect from config or standard files)",
    ),
):
    """
    Remove Monoco Managed Block from Agent Environment files and clean up distributed skills.
    """
    root = Path.cwd()
    config = get_config(str(root))

    # 1. Clean up System Prompts
    targets = _get_targets(root, config, target)

    for t in targets:
        if not t.exists():
            if target:
                console.print(f"[yellow]Target {t} does not exist.[/yellow]")
            continue

        injector = PromptInjector(t)
        try:
            changed = injector.remove()
            if changed:
                console.print(
                    f"[green]✓ Removed Monoco Managed Block from {t.name}[/green]"
                )
            else:
                console.print(f"[dim]= No Monoco Block found in {t.name}[/dim]")
        except Exception as e:
            console.print(f"[red]Failed to uninstall from {t.name}: {e}[/red]")

    # 2. Clean up Skills
    console.print("[bold blue]Cleaning up distributed skills...[/bold blue]")

    # Load features to get skill list
    registry = FeatureRegistry()
    registry.load_defaults()
    active_features = registry.get_features()

    skill_manager = SkillManager(root, active_features)

    # Get active integrations
    integrations = get_active_integrations(
        root, config_overrides=config.agent.integrations, auto_detect=True
    )

    if integrations:
        for framework_key, integration in integrations.items():
            skill_target_dir = root / integration.skill_root_dir
            console.print(
                f"[dim]  Cleaning {integration.name} ({skill_target_dir})...[/dim]"
            )

            try:
                skill_manager.cleanup(skill_target_dir)
            except Exception as e:
                console.print(
                    f"[red]  Failed to clean skills from {integration.name}: {e}[/red]"
                )
    else:
        console.print(
            "[yellow]No agent frameworks detected. Skipping skill cleanup.[/yellow]"
        )
