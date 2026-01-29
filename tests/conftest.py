import pytest
import shutil
import tempfile
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
    Includes .monoco/workspace.yaml and Issues/ structure.
    """
    tmp_dir = tempfile.mkdtemp()
    project_root = Path(tmp_dir)

    # 1. Initialize .monoco structure
    dot_monoco = project_root / ".monoco"
    dot_monoco.mkdir()
    (dot_monoco / "workspace.yaml").write_text("paths:\n  issues: Issues\n")
    (dot_monoco / "project.yaml").write_text("name: Test Project\nkey: TEST\n")

    # 2. Initialize Issues structure
    issues_dir = project_root / "Issues"
    core.init(issues_dir)

    # Change CWD for CLI tests that rely on find_monoco_root / CWD
    import os

    old_cwd = os.getcwd()
    os.chdir(tmp_dir)

    # Clear config cache
    from monoco.core import config

    config._settings = None

    yield project_root

    # Restore CWD
    os.chdir(old_cwd)
    shutil.rmtree(tmp_dir)
