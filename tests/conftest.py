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
