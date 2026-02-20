import pytest
import shutil
import tempfile
import os
from pathlib import Path
from monoco.features.issue import core


@pytest.fixture
def issues_root():
    """
    Provides a temporary initialized Monoco Issues root for testing.
    Cleaned up after test.
    """
    tmp_dir = tempfile.mkdtemp()
    path = Path(tmp_dir)
    core.init(path)

    yield path

    shutil.rmtree(tmp_dir)


@pytest.fixture
def project_env():
    """
    Provides a temporary initialized full Monoco project directory.
    Uses ~/.monoco/config.yaml for configuration (backed up and restored after test).
    """
    tmp_dir = tempfile.mkdtemp()
    project_root = Path(tmp_dir)

    # 1. Initialize git repo first
    import subprocess
    subprocess.run(["git", "init"], cwd=tmp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_dir,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_dir,
        check=True,
        capture_output=True,
    )

    # Ensure we're on main branch
    subprocess.run(["git", "checkout", "-b", "main"], cwd=tmp_dir, capture_output=True)

    # 2. Initialize .monoco structure (minimal, only for project marker)
    dot_monoco = project_root / ".monoco"
    dot_monoco.mkdir()

    # 3. Initialize Issues structure
    issues_dir = project_root / "Issues"
    core.init(issues_dir)

    # Create initial commit to ensure git repo has content
    (project_root / "README.md").write_text("# Test Project")
    subprocess.run(["git", "add", "."], cwd=tmp_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_dir,
        check=True,
        capture_output=True,
    )

    # 4. Setup global config (~/.monoco/config.yaml) with test settings
    global_config_dir = Path.home() / ".monoco"
    global_config_dir.mkdir(parents=True, exist_ok=True)
    global_config_path = global_config_dir / "config.yaml"

    # Backup original config if exists
    backup_config = None
    if global_config_path.exists():
        backup_config = global_config_path.read_text()

    # Write test config
    test_config = """project:
  name: Test Project
  key: TEST
paths:
  issues: Issues
"""
    global_config_path.write_text(test_config)

    # Change CWD for CLI tests that rely on find_monoco_root / CWD
    old_cwd = os.getcwd()
    os.chdir(tmp_dir)

    # Clear config cache
    from monoco.core import config

    config._settings = None

    yield project_root

    # Cleanup: Restore CWD
    os.chdir(old_cwd)
    shutil.rmtree(tmp_dir)

    # Restore original config or remove test config
    if backup_config is not None:
        global_config_path.write_text(backup_config)
    else:
        global_config_path.unlink(missing_ok=True)

    # Clear config cache again
    config._settings = None
