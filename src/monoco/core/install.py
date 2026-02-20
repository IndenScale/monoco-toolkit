import typer
import subprocess
from pathlib import Path
from typing import Optional, List
from enum import Enum
from rich.console import Console

from monoco.core.registry import FeatureRegistry
from monoco.core.injection import PromptInjector
from monoco.core.config import get_config
from monoco.core.skills import SkillManager
from monoco.core.integrations import get_active_integrations

console = Console()


class InstallModule(str, Enum):
    """Available installable modules."""
    ROLES = "roles"
    SKILLS = "skills"
    WORKFLOWS = "workflows"
    HOOKS = "hooks"
    PROMPTS = "prompts"


# Module dependency graph: child -> parents
MODULE_DEPENDENCIES = {
    InstallModule.WORKFLOWS: [InstallModule.SKILLS, InstallModule.ROLES],
    InstallModule.SKILLS: [InstallModule.ROLES],
    InstallModule.HOOKS: [],
    InstallModule.PROMPTS: [],
    InstallModule.ROLES: [],
}


def _resolve_module_dependencies(modules: List[InstallModule]) -> List[InstallModule]:
    """Resolve module dependencies using topological sort."""
    result = []
    visited = set()
    temp_mark = set()

    def visit(module: InstallModule):
        if module in temp_mark:
            raise ValueError(f"Circular dependency detected for module {module}")
        if module in visited:
            return
        temp_mark.add(module)
        for dep in MODULE_DEPENDENCIES.get(module, []):
            visit(dep)
        temp_mark.remove(module)
        visited.add(module)
        result.append(module)

    for module in modules:
        visit(module)

    return result


class InstallScope(str, Enum):
    """Installation scope: global or project."""
    GLOBAL = "global"
    PROJECT = "project"


def _get_global_paths() -> dict:
    """Get global installation paths."""
    home = Path.home()
    return {
        "monoco_root": home / ".monoco",
        "roles": home / ".monoco" / "roles",
        "skills": home / ".config" / "agents" / "skills",
        "prompts": home / ".config" / "agents" / "AGENTS.md",
        "workflows": home / ".monoco" / "workflows",
        # Hooks don't have global path (git hooks are repo-specific)
        "hooks": None,
    }


def _get_project_paths(root: Path) -> dict:
    """Get project installation paths."""
    return {
        "monoco_root": root / ".monoco",
        "roles": root / ".monoco" / "roles",
        "skills": root / ".agents" / "skills",
        "prompts": root / "AGENTS.md",  # Will be multiple: AGENTS.md, GEMINI.md, CLAUDE.md
        "workflows": root / ".agent" / "workflows",
        "hooks": root / ".git" / "hooks",
    }


def _get_targets_for_scope(
    scope: InstallScope, root: Path, config, cli_target: Optional[Path]
) -> List[Path]:
    """Helper to determine target files based on scope."""
    if scope == InstallScope.GLOBAL:
        # For global scope, target is ~/.config/agents/AGENTS.md
        global_paths = _get_global_paths()
        agents_md = global_paths["prompts"]
        if agents_md.exists():
            return [agents_md]
        # Also check for other agent files
        global_agents_dir = Path.home() / ".config" / "agents"
        targets = []
        for fname in ["AGENTS.md", "GEMINI.md", "CLAUDE.md"]:
            fpath = global_agents_dir / fname
            targets.append(fpath)
        return targets
    else:
        # Project scope - use existing logic
        return _get_project_targets(root, config, cli_target)


def _get_project_targets(root: Path, config, cli_target: Optional[Path]) -> List[Path]:
    """Helper to determine target files for project scope."""
    targets = []

    # 1. CLI Target
    if cli_target:
        targets.append(cli_target)
        return targets

    # 2. Registry Defaults (Dynamic Detection)
    integrations = get_active_integrations(
        root, config_overrides=None, auto_detect=False
    )

    if integrations:
        for integration in integrations.values():
            targets.append(root / integration.system_prompt_file)
    else:
        # Fallback to standard Monoco header if nothing is detected
        defaults = ["GEMINI.md", "CLAUDE.md"]
        targets.extend([root / fname for fname in defaults])

    return list(set(targets))  # Unique paths


def _install_roles(
    scope: InstallScope,
    root: Path,
    config,
    active_features: List,
    force: bool = False,
) -> bool:
    """Install roles to the specified scope."""
    console.print("[bold blue]Distributing agent roles...[/bold blue]")

    # Determine language from config
    role_lang = config.i18n.source_lang if config.i18n.source_lang else "en"
    console.print(f"[dim]  Using language: {role_lang}[/dim]")

    # Source: Builtin Resource Dir with language support
    base_resource_dir = Path(__file__).parent.parent / "features" / "agent" / "resources"
    resource_dir = base_resource_dir / role_lang / "roles"

    # Fallback to 'en' if specific language not found
    if not resource_dir.exists():
        console.print(f"[yellow]  Roles for '{role_lang}' not found, falling back to 'en'[/yellow]")
        resource_dir = base_resource_dir / "en" / "roles"

    # Determine target based on scope
    if scope == InstallScope.GLOBAL:
        target_roles_dir = _get_global_paths()["roles"]
    else:
        target_roles_dir = _get_project_paths(root)["roles"]

    if resource_dir.exists():
        target_roles_dir.mkdir(parents=True, exist_ok=True)
        import shutil

        count = 0
        for yaml_file in resource_dir.glob("*.yaml"):
            target_file = target_roles_dir / yaml_file.name
            try:
                # Always overwrite - source of truth is builtin roles
                shutil.copy2(yaml_file, target_file)
                console.print(f"[dim]  ✓ Installed role {yaml_file.name}[/dim]")
                count += 1
            except Exception as e:
                console.print(f"[red]  Failed to install role {yaml_file.name}: {e}[/red]")

        if count > 0:
            console.print(f"[green]  ✓ Updated {count} roles in {target_roles_dir}[/green]")
        # Remove old role files that no longer exist in source
        if target_roles_dir.exists():
            source_names = {f.name for f in resource_dir.glob("*.yaml")}
            for existing_file in target_roles_dir.glob("*.yaml"):
                if existing_file.name not in source_names:
                    try:
                        existing_file.unlink()
                        console.print(f"[dim]  ✓ Removed obsolete role {existing_file.name}[/dim]")
                    except Exception as e:
                        console.print(f"[red]  Failed to remove obsolete role {existing_file.name}: {e}[/red]")
        return True
    else:
        console.print("[yellow]  No builtin roles found to install.[/yellow]")
        return False


def _install_skills(
    scope: InstallScope,
    root: Path,
    config,
    active_features: List,
    skill_manager: SkillManager,
    force: bool = False,
) -> bool:
    """Install skills to the specified scope."""
    console.print("[bold blue]Distributing skills to agent frameworks...[/bold blue]")

    # Determine language from config
    skill_lang = config.i18n.source_lang if config.i18n.source_lang else "en"
    console.print(f"[dim]  Using language: {skill_lang}[/dim]")

    # Determine target based on scope
    if scope == InstallScope.GLOBAL:
        target_dir = _get_global_paths()["skills"]
        target_dir.mkdir(parents=True, exist_ok=True)

        # For global scope, we distribute to a single directory
        console.print(f"[dim]  Distributing to global skills ({target_dir})...[/dim]")

        try:
            results = skill_manager.distribute(target_dir, lang=skill_lang, force=force)
            success_count = sum(1 for v in results.values() if v)
            console.print(
                f"[green]  ✓ Distributed {success_count}/{len(results)} skills globally[/green]"
            )
            return True
        except Exception as e:
            console.print(f"[red]  Failed to distribute skills globally: {e}[/red]")
            return False
    else:
        # Project scope - distribute to each integration
        integrations = get_active_integrations(
            root, config_overrides=None, auto_detect=False
        )

        if integrations:
            for framework_key, integration in integrations.items():
                skill_target_dir = root / integration.skill_root_dir
                console.print(
                    f"[dim]  Distributing to {integration.name} ({skill_target_dir})...[/dim]"
                )

                try:
                    results = skill_manager.distribute(
                        skill_target_dir, lang=skill_lang, force=force
                    )
                    success_count = sum(1 for v in results.values() if v)
                    console.print(
                        f"[green]  ✓ Distributed {success_count}/{len(results)} skills to {integration.name}[/green]"
                    )
                except Exception as e:
                    console.print(
                        f"[red]  Failed to distribute skills to {integration.name}: {e}[/red]"
                    )
            return True
        else:
            console.print(
                "[yellow]No agent frameworks detected. Skipping skill distribution.[/yellow]"
            )
            return False


def _install_workflows(
    scope: InstallScope,
    root: Path,
    config,
    skill_manager: SkillManager,
    force: bool = False,
) -> bool:
    """Install workflows to the specified scope."""
    console.print("[bold blue]Distributing Flow Skills as Workflows...[/bold blue]")

    # Determine language from config
    skill_lang = config.i18n.source_lang if config.i18n.source_lang else "en"

    try:
        if scope == InstallScope.GLOBAL:
            # For global scope, distribute to ~/.monoco/workflows/
            target_dir = _get_global_paths()["workflows"]
            target_dir.mkdir(parents=True, exist_ok=True)

            # Note: WorkflowDistributor is currently project-root based
            # For global workflows, we might need a different approach
            console.print(
                "[yellow]  Global workflow distribution not yet implemented, skipping[/yellow]"
            )
            return False
        else:
            workflow_results = skill_manager.distribute_workflows(force=force, lang=skill_lang)
            success_count = sum(1 for v in workflow_results.values() if v)
            if workflow_results:
                console.print(
                    f"[green]  ✓ Distributed {success_count}/{len(workflow_results)} workflows to .agent/workflows/[/green]"
                )
            else:
                console.print(
                    "[yellow]  No Flow Skills found to convert[/yellow]"
                )
            return True
    except Exception as e:
        console.print(f"[red]  Failed to distribute workflows: {e}[/red]")
        return False


def _install_hooks(
    scope: InstallScope,
    root: Path,
    active_features: List,
) -> bool:
    """Install hooks to the specified scope."""
    if scope == InstallScope.GLOBAL:
        console.print("[yellow]Skipping hooks installation for global scope (hooks are repository-specific)[/yellow]")
        return False

    console.print("[bold blue]Synchronizing Universal Hooks...[/bold blue]")

    try:
        from monoco.features.hooks import UniversalHookManager, HookType
        from monoco.features.hooks.dispatchers import (
            GitHookDispatcher,
            ClaudeCodeDispatcher,
            GeminiDispatcher,
        )

        hooks_manager = UniversalHookManager()

        # Register Dispatchers
        git_dispatcher = GitHookDispatcher()
        hooks_manager.register_dispatcher(HookType.GIT, git_dispatcher)

        # Register Agent Dispatchers for active platforms
        agent_dispatchers = {
            "claude-code": ClaudeCodeDispatcher(),
            "gemini-cli": GeminiDispatcher(),
        }
        for dispatcher in agent_dispatchers.values():
            hooks_manager.register_dispatcher(HookType.AGENT, dispatcher)

        # Scan for hooks
        all_hooks = []

        # Scan builtin hooks from hooks feature
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

        # Scan for hooks in all active features
        for feature in active_features:
            if feature.name == "hooks":
                continue  # Already scanned

            import importlib
            try:
                module_name = feature.__class__.__module__
                module = importlib.import_module(module_name)

                if hasattr(module, "__file__") and module.__file__:
                    feature_dir = Path(module.__file__).parent
                    hooks_resource_dir = feature_dir / "resources" / "hooks"

                    if hooks_resource_dir.exists():
                        groups = hooks_manager.scan(hooks_resource_dir)
                        for group in groups.values():
                            all_hooks.extend(group.hooks)
            except Exception:
                continue

        # Sync Git Hooks
        git_hooks = [h for h in all_hooks if h.metadata.type == HookType.GIT]

        if not (root / ".git").exists():
            console.print("[dim]  Git repository not found. Initializing...[/dim]")
            subprocess.run(["git", "config", "--global", "init.defaultBranch", "main"], check=False)
            subprocess.run(["git", "init"], cwd=root, check=False)

        git_results = git_dispatcher.sync(git_hooks, root)

        git_installed = sum(1 for v in git_results.values() if v)
        if git_installed > 0:
            console.print(f"[green]  ✓ Synchronized {git_installed} Git hooks[/green]")
        elif git_hooks:
            console.print("[yellow]  No Git hooks were successfully synchronized[/yellow]")

        # Sync Agent Hooks
        agent_hooks = [h for h in all_hooks if h.metadata.type == HookType.AGENT]

        for provider, dispatcher in agent_dispatchers.items():
            provider_hooks = [h for h in agent_hooks if h.metadata.provider == provider]
            if provider_hooks:
                results = dispatcher.sync(provider_hooks, root)
                success_count = sum(1 for v in results.values() if v)
                if success_count > 0:
                    console.print(f"[green]  ✓ Synchronized {success_count} agent hooks to {provider}[/green]")

        return True
    except Exception as e:
        console.print(f"[red]  Failed to synchronize Universal Hooks: {e}[/red]")
        import traceback
        console.print(f"[dim]{traceback.format_exc()}[/dim]")
        return False


def _install_prompts(
    scope: InstallScope,
    root: Path,
    config,
    active_features: List,
    cli_target: Optional[Path] = None,
    check: bool = False,
) -> bool:
    """Install prompts to the specified scope."""
    console.print("[bold blue]Installing system prompts...[/bold blue]")

    # 1. Register Features
    registry = FeatureRegistry()
    registry.load_defaults()

    # 2. Collect Data
    collected_prompts = {}

    all_features = registry.get_features()
    active_features_list = all_features

    with console.status("[bold green]Collecting feature integration data...") as status:
        for feature in active_features_list:
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
        f"[blue]Collected {len(collected_prompts)} prompts from {len(active_features_list)} features.[/blue]"
    )

    # 3. Determine Targets
    targets = _get_targets_for_scope(scope, root, config, cli_target)

    # Ensure targets exist
    final_targets = []
    for t in targets:
        if not t.exists():
            console.print(f"[yellow]Creating {t.name}...[/yellow]")
            try:
                t.parent.mkdir(parents=True, exist_ok=True)
                t.touch()
                final_targets.append(t)
            except Exception as e:
                console.print(f"[red]Failed to create {t}: {e}[/red]")
        else:
            final_targets.append(t)

    # 4. Inject System Prompts
    success = True
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
                success = False

    return success


def install_command(
    ctx: typer.Context,
    modules: Optional[List[str]] = typer.Argument(
        None,
        help="Modules to install (roles, skills, workflows, hooks, prompts). If not specified, installs all.",
    ),
    target: Optional[Path] = typer.Option(
        None,
        "--target",
        "-t",
        help="Specific file to update (default: auto-detect from config or standard files)",
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Install to global scope (~/.monoco/, ~/.config/agents/)",
    ),
    project_scope: bool = typer.Option(
        False,
        "--project",
        "-p",
        help="Install to project scope (default)",
    ),
    all_modules: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Install all modules (default if no modules specified)",
    ),
    check: bool = typer.Option(False, "--check", help="Dry run check mode"),
    workflows_flag: bool = typer.Option(
        False,
        "--workflows",
        "-w",
        help="Also distribute Flow Skills as Antigravity Workflows to .agent/workflows/",
    ),
):
    """
    Install Monoco modules to the Agent Environment.

    Supports both global and project scope installation, with fine-grained module selection.

    Examples:
        monoco install                              # Install all modules to project
        monoco install roles skills                 # Install only roles and skills
        monoco install -g                           # Install all modules globally
        monoco install -g roles skills              # Install roles and skills globally
        monoco sync                                 # Alias for 'monoco install --all --project'
    """
    root = Path.cwd()

    # Determine scope
    if global_scope and project_scope:
        console.print("[red]Error: Cannot specify both --global and --project[/red]")
        raise typer.Exit(code=1)

    scope = InstallScope.GLOBAL if global_scope else InstallScope.PROJECT

    # 0. Load Config
    config = get_config(str(root))

    # 1. Determine modules to install
    if not modules or all_modules:
        # Install all modules (except hooks for global scope)
        if scope == InstallScope.GLOBAL:
            modules_to_install = [
                InstallModule.ROLES,
                InstallModule.SKILLS,
                InstallModule.WORKFLOWS,
                InstallModule.PROMPTS,
            ]
            console.print("[dim]Installing all modules (hooks skipped for global scope)[/dim]")
        else:
            modules_to_install = list(InstallModule)
            console.print("[dim]Installing all modules[/dim]")
    else:
        # Parse module names
        modules_to_install = []
        for m in modules:
            try:
                modules_to_install.append(InstallModule(m.lower()))
            except ValueError:
                console.print(f"[red]Unknown module: {m}. Valid modules: {', '.join(InstallModule)}[/red]")
                raise typer.Exit(code=1)

    # Resolve dependencies
    modules_to_install = _resolve_module_dependencies(modules_to_install)
    console.print(f"[dim]Modules to install: {', '.join(m.value for m in modules_to_install)}[/dim]")
    console.print(f"[dim]Scope: {scope.value}[/dim]")

    # 2. Register Features and create SkillManager
    registry = FeatureRegistry()
    registry.load_defaults()
    all_features = registry.get_features()
    skill_manager = SkillManager(root, all_features)

    # 3. Install each module
    results = {}

    for module in modules_to_install:
        if module == InstallModule.ROLES:
            results[module] = _install_roles(scope, root, config, all_features)
        elif module == InstallModule.SKILLS:
            results[module] = _install_skills(scope, root, config, all_features, skill_manager)
        elif module == InstallModule.WORKFLOWS:
            results[module] = _install_workflows(scope, root, config, skill_manager)
        elif module == InstallModule.HOOKS:
            results[module] = _install_hooks(scope, root, all_features)
        elif module == InstallModule.PROMPTS:
            results[module] = _install_prompts(scope, root, config, all_features, target, check)

    # Summary
    console.print("\n[bold]Installation Summary:[/bold]")
    for module, success in results.items():
        status = "[green]✓[/green]" if success else "[red]✗[/red]"
        console.print(f"  {status} {module.value}")

    # Exit with error if any module failed
    if not all(results.values()):
        raise typer.Exit(code=1)


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

    This is an alias for 'monoco install --all --project'.
    Kept for backward compatibility.
    """
    # Call install_command with --all --project
    return install_command(
        ctx=ctx,
        modules=None,
        target=target,
        global_scope=False,
        project_scope=True,
        all_modules=True,
        check=check,
        workflows_flag=workflows,
    )


def _uninstall_module(
    module: InstallModule,
    scope: InstallScope,
    root: Path,
    config,
    skill_manager: SkillManager,
    targets: List[Path],
) -> bool:
    """Uninstall a specific module from the given scope."""
    if module == InstallModule.ROLES:
        console.print("[bold blue]Cleaning up roles...[/bold blue]")
        if scope == InstallScope.GLOBAL:
            target_dir = _get_global_paths()["roles"]
        else:
            target_dir = _get_project_paths(root)["roles"]

        if target_dir.exists():
            import shutil
            shutil.rmtree(target_dir)
            console.print(f"[green]  ✓ Removed roles from {target_dir}[/green]")
            return True
        return False

    elif module == InstallModule.SKILLS:
        console.print("[bold blue]Cleaning up skills...[/bold blue]")
        if scope == InstallScope.GLOBAL:
            target_dir = _get_global_paths()["skills"]
            if target_dir.exists():
                skill_manager.cleanup(target_dir)
                return True
        else:
            integrations = get_active_integrations(root, config_overrides=None, auto_detect=True)
            if integrations:
                for framework_key, integration in integrations.items():
                    skill_target_dir = root / integration.skill_root_dir
                    console.print(f"[dim]  Cleaning {integration.name} ({skill_target_dir})...[/dim]")
                    try:
                        skill_manager.cleanup(skill_target_dir)
                    except Exception as e:
                        console.print(f"[red]  Failed to clean skills from {integration.name}: {e}[/red]")
                return True
        return False

    elif module == InstallModule.WORKFLOWS:
        console.print("[bold blue]Cleaning up workflows...[/bold blue]")
        if scope == InstallScope.GLOBAL:
            target_dir = _get_global_paths()["workflows"]
            if target_dir.exists():
                import shutil
                shutil.rmtree(target_dir)
                console.print(f"[green]  ✓ Removed workflows from {target_dir}[/green]")
                return True
        else:
            try:
                removed_count = skill_manager.cleanup_workflows()
                if removed_count > 0:
                    console.print(f"[green]  ✓ Removed {removed_count} workflows from .agent/workflows/[/green]")
                    return True
            except Exception as e:
                console.print(f"[red]  Failed to clean workflows: {e}[/red]")
        return False

    elif module == InstallModule.HOOKS:
        if scope == InstallScope.GLOBAL:
            console.print("[yellow]Skipping hooks cleanup for global scope (none installed)[/yellow]")
            return False

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
                console.print(f"[green]  ✓ Removed {uninstalled} Git hooks[/green]")
                return True
            else:
                console.print("[dim]  No Monoco Git hooks to clean up[/dim]")
        except Exception as e:
            console.print(f"[red]  Failed to clean Git hooks: {e}[/red]")

        console.print("[bold blue]Cleaning up Agent Hooks...[/bold blue]")
        try:
            from monoco.features.hooks.dispatchers import (
                ClaudeCodeDispatcher,
                GeminiDispatcher,
            )

            # Clean up Claude Code hooks
            claude_dispatcher = ClaudeCodeDispatcher()
            claude_settings = claude_dispatcher.get_settings_path(root)
            if claude_settings and claude_settings.exists():
                try:
                    import json
                    with open(claude_settings, "r", encoding="utf-8") as f:
                        settings = json.load(f)

                    if "hooks" in settings:
                        # Remove Monoco-managed hooks
                        for event in list(settings["hooks"].keys()):
                            configs = settings["hooks"][event]
                            if isinstance(configs, list):
                                settings["hooks"][event] = [
                                    c for c in configs if not c.get("_monoco_managed")
                                ]
                        # Clean up empty events
                        settings["hooks"] = {
                            k: v for k, v in settings["hooks"].items() if v
                        }

                        with open(claude_settings, "w", encoding="utf-8") as f:
                            json.dump(settings, f, indent=2, ensure_ascii=False)

                        console.print("[green]  ✓ Cleaned up Claude Code hooks[/green]")
                        return True
                except Exception as e:
                    console.print(f"[red]  Failed to clean Claude Code hooks: {e}[/red]")

            # Clean up Gemini CLI hooks
            gemini_dispatcher = GeminiDispatcher()
            gemini_settings = gemini_dispatcher.get_settings_path(root)
            if gemini_settings and gemini_settings.exists():
                try:
                    import json
                    with open(gemini_settings, "r", encoding="utf-8") as f:
                        settings = json.load(f)

                    if "hooks" in settings:
                        # Remove Monoco-managed hooks
                        for event in list(settings["hooks"].keys()):
                            configs = settings["hooks"][event]
                            if isinstance(configs, list):
                                settings["hooks"][event] = [
                                    c for c in configs if not c.get("_monoco_managed")
                                ]
                        # Clean up empty events
                        settings["hooks"] = {
                            k: v for k, v in settings["hooks"].items() if v
                        }

                        with open(gemini_settings, "w", encoding="utf-8") as f:
                            json.dump(settings, f, indent=2, ensure_ascii=False)

                        console.print("[green]  ✓ Cleaned up Gemini CLI hooks[/green]")
                        return True
                except Exception as e:
                    console.print(f"[red]  Failed to clean Gemini CLI hooks: {e}[/red]")

        except Exception as e:
            console.print(f"[red]  Failed to clean Agent hooks: {e}[/red]")
        return False

    elif module == InstallModule.PROMPTS:
        console.print("[bold blue]Cleaning up system prompts...[/bold blue]")
        success = False
        for t in targets:
            if not t.exists():
                continue

            injector = PromptInjector(t)
            try:
                changed = injector.remove()
                if changed:
                    console.print(f"[green]  ✓ Removed Monoco Managed Block from {t.name}[/green]")
                    success = True
                else:
                    console.print(f"[dim]  = No Monoco Block found in {t.name}[/dim]")
            except Exception as e:
                console.print(f"[red]  Failed to uninstall from {t.name}: {e}[/red]")
        return success

    return False


def uninstall_command(
    ctx: typer.Context,
    modules: Optional[List[str]] = typer.Argument(
        None,
        help="Modules to uninstall (roles, skills, workflows, hooks, prompts). If not specified, uninstalls all.",
    ),
    target: Optional[Path] = typer.Option(
        None,
        "--target",
        "-t",
        help="Specific file to clean (default: auto-detect from config or standard files)",
    ),
    global_scope: bool = typer.Option(
        False,
        "--global",
        "-g",
        help="Uninstall from global scope (~/.monoco/, ~/.config/agents/)",
    ),
    project_scope: bool = typer.Option(
        False,
        "--project",
        "-p",
        help="Uninstall from project scope (default)",
    ),
    all_modules: bool = typer.Option(
        False,
        "--all",
        "-a",
        help="Uninstall all modules (default if no modules specified)",
    ),
):
    """
    Uninstall Monoco modules from the Agent Environment.

    Examples:
        monoco uninstall                            # Uninstall all modules from project
        monoco uninstall roles skills               # Uninstall only roles and skills
        monoco uninstall -g                         # Uninstall all modules globally
    """
    root = Path.cwd()
    config = get_config(str(root))

    # Determine scope
    if global_scope and project_scope:
        console.print("[red]Error: Cannot specify both --global and --project[/red]")
        raise typer.Exit(code=1)

    scope = InstallScope.GLOBAL if global_scope else InstallScope.PROJECT

    # Determine modules to uninstall
    if not modules or all_modules:
        # Uninstall all modules (except hooks for global scope)
        if scope == InstallScope.GLOBAL:
            modules_to_uninstall = [
                InstallModule.ROLES,
                InstallModule.SKILLS,
                InstallModule.WORKFLOWS,
                InstallModule.PROMPTS,
            ]
            console.print("[dim]Uninstalling all modules (hooks skipped for global scope)[/dim]")
        else:
            modules_to_uninstall = list(InstallModule)
            console.print("[dim]Uninstalling all modules[/dim]")
    else:
        # Parse module names
        modules_to_uninstall = []
        for m in modules:
            try:
                modules_to_uninstall.append(InstallModule(m.lower()))
            except ValueError:
                console.print(f"[red]Unknown module: {m}. Valid modules: {', '.join(InstallModule)}[/red]")
                raise typer.Exit(code=1)

    console.print(f"[dim]Modules to uninstall: {', '.join(m.value for m in modules_to_uninstall)}[/dim]")
    console.print(f"[dim]Scope: {scope.value}[/dim]")

    # Initialize SkillManager
    registry = FeatureRegistry()
    registry.load_defaults()
    all_features = registry.get_features()
    skill_manager = SkillManager(root, all_features)

    # Get targets for prompts
    targets = _get_targets_for_scope(scope, root, config, target)

    # Uninstall each module
    results = {}
    for module in modules_to_uninstall:
        results[module] = _uninstall_module(
            module, scope, root, config, skill_manager, targets
        )

    # Summary
    console.print("\n[bold]Uninstallation Summary:[/bold]")
    for module, success in results.items():
        status = "[green]✓[/green]" if success else "[dim]-[/dim]"
        console.print(f"  {status} {module.value}")
