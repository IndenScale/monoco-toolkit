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

    # 2. Registry Defaults (Dynamic Detection)
    integrations = get_active_integrations(
        root, config_overrides=None, auto_detect=True
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
    workflows: bool = typer.Option(
        False,
        "--workflows",
        "-w",
        help="Also distribute Flow Skills as Antigravity Workflows to .agent/workflows/",
    ),
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

    # Filter features based on config if specified (Deprecated: agent config removed)
    all_features = registry.get_features()
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



    # 3. Distribute Roles
    console.print("[bold blue]Distributing agent roles...[/bold blue]")
    
    # Source: Builtin Resource Dir
    # monoco/core/sync.py -> monoco/core -> monoco -> features/agent/resources/roles
    resource_dir = Path(__file__).parent.parent / "features" / "agent" / "resources" / "roles"
    
    # Target: .monoco/roles
    target_roles_dir = root / ".monoco" / "roles"
    # Only create if we have sources
    if resource_dir.exists():
        target_roles_dir.mkdir(parents=True, exist_ok=True)
        import shutil
        
        count = 0
        for yaml_file in resource_dir.glob("*.yaml"):
            target_file = target_roles_dir / yaml_file.name
            try:
                # Copy only if different or new? For now, nice and simple overwrite.
                shutil.copy2(yaml_file, target_file)
                console.print(f"[dim]  ✓ Synced role {yaml_file.name}[/dim]")
                count += 1
            except Exception as e:
                console.print(f"[red]  Failed to sync role {yaml_file.name}: {e}[/red]")
        
        if count > 0:
             console.print(f"[green]  ✓ Updated {count} roles in .monoco/roles/[/green]")
    else:
        console.print("[yellow]  No builtin roles found to sync.[/yellow]")

    # 4. Distribute Skills
    console.print("[bold blue]Distributing skills to agent frameworks...[/bold blue]")

    # Determine language from config
    skill_lang = config.i18n.source_lang if config.i18n.source_lang else "en"
    console.print(f"[dim]  Using language: {skill_lang}[/dim]")

    # Initialize SkillManager with active features
    skill_manager = SkillManager(root, active_features)

    # Get active integrations
    integrations = get_active_integrations(
        root, config_overrides=None, auto_detect=True
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

    # 5. Distribute Workflows (if --workflows flag is set)
    if workflows:
        console.print("[bold blue]Distributing Flow Skills as Workflows...[/bold blue]")

        try:
            workflow_results = skill_manager.distribute_workflows(force=False, lang=skill_lang)
            success_count = sum(1 for v in workflow_results.values() if v)
            if workflow_results:
                console.print(
                    f"[green]  ✓ Distributed {success_count}/{len(workflow_results)} workflows to .agent/workflows/[/green]"
                )
            else:
                console.print(
                    "[yellow]  No Flow Skills found to convert[/yellow]"
                )
        except Exception as e:
            console.print(
                f"[red]  Failed to distribute workflows: {e}[/red]"
            )

    # 6. Sync Universal Hooks (Git & Agent)
    console.print("[bold blue]Synchronizing Universal Hooks...[/bold blue]")

    try:
        from monoco.features.hooks import UniversalHookManager, HookType
        from monoco.features.hooks.dispatchers import GitHookDispatcher, AgentHookDispatcher

        hooks_manager = UniversalHookManager()
        
        # Register Dispatchers
        git_dispatcher = GitHookDispatcher()
        hooks_manager.register_dispatcher(HookType.GIT, git_dispatcher)
        
        # Register Agent Dispatchers for active platforms
        agent_dispatchers = {}
        for provider in ["claude-code", "gemini-cli"]:
            dispatcher = AgentHookDispatcher(provider=provider)
            hooks_manager.register_dispatcher(HookType.AGENT, dispatcher)
            agent_dispatchers[provider] = dispatcher

        # 6.1 Scan for hooks
        all_hooks = []
        
        # 6.1.1 Scan builtin hooks from hooks feature
        try:
            from monoco.features import hooks as hooks_module
            hooks_feature_dir = Path(hooks_module.__file__).parent
            builtin_hooks_dir = hooks_feature_dir / "resources" / "hooks"
            if builtin_hooks_dir.exists():
                groups = hooks_manager.scan(builtin_hooks_dir)
                for group in groups.values():
                    all_hooks.extend(group.hooks)
        except Exception as e:
            console.print(f"[dim]  No builtin hooks found: {e}[/dim]")

        # 6.1.2 Scan for hooks in all active features
        for feature in active_features:
            if feature.name == "hooks":
                continue # Already scanned
                
            import importlib
            try:
                # Use the module where the feature class is defined (usually adapter.py)
                module_name = feature.__class__.__module__
                module = importlib.import_module(module_name)
                
                if hasattr(module, "__file__") and module.__file__:
                    # feature_dir is the directory containing adapter.py
                    feature_dir = Path(module.__file__).parent
                    hooks_resource_dir = feature_dir / "resources" / "hooks"
                    
                    if hooks_resource_dir.exists():
                        groups = hooks_manager.scan(hooks_resource_dir)
                        for group in groups.values():
                            all_hooks.extend(group.hooks)
            except Exception:
                continue

        # 6.2 Sync Git Hooks
        git_hooks = [h for h in all_hooks if h.metadata.type == HookType.GIT]
        git_results = git_dispatcher.sync(git_hooks, root)
        
        git_installed = sum(1 for v in git_results.values() if v)
        if git_installed > 0:
            console.print(f"[green]  ✓ Synchronized {git_installed} Git hooks[/green]")
        elif git_hooks:
            console.print("[yellow]  No Git hooks were successfully synchronized[/yellow]")

        # 6.3 Sync Agent Hooks (Distribution)
        agent_hooks = [h for h in all_hooks if h.metadata.type == HookType.AGENT]
        for hook in agent_hooks:
            provider = hook.metadata.provider
            if provider in agent_dispatchers:
                if agent_dispatchers[provider].install(hook, root):
                    console.print(f"[green]  ✓ Distributed agent hook: {hook.script_path.name} to {provider}[/green]")

    except Exception as e:
        console.print(f"[red]  Failed to synchronize Universal Hooks: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")

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
        root, config_overrides=None, auto_detect=True
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

    # 3. Clean up Workflows
    console.print("[bold blue]Cleaning up distributed workflows...[/bold blue]")

    try:
        removed_count = skill_manager.cleanup_workflows()
        if removed_count > 0:
            console.print(
                f"[green]  ✓ Removed {removed_count} workflows from .agent/workflows/[/green]"
            )
    except Exception as e:
        console.print(
            f"[red]  Failed to clean workflows: {e}[/red]"
        )

    # 4. Clean up Git Hooks
    console.print("[bold blue]Cleaning up Git Hooks...[/bold blue]")

    try:
        from monoco.features.hooks.dispatchers import GitHookDispatcher

        git_dispatcher = GitHookDispatcher()
        installed = git_dispatcher.list_installed(root)

        uninstalled = 0
        for hook_info in installed:
            if git_dispatcher.uninstall(hook_info["event"], root):
                uninstalled += 1

        if uninstalled > 0:
            console.print(
                f"[green]  ✓ Removed {uninstalled} Git hooks[/green]"
            )
        else:
            console.print("[dim]  No Monoco Git hooks to clean up[/dim]")
    except Exception as e:
        console.print(f"[red]  Failed to clean Git hooks: {e}[/red]")
