import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from monoco.core.resource import ResourceManager, ResourceFinder, ResourceType, ResourceNode

@pytest.fixture
def mock_package_structure(tmp_path):
    """Creates a temporary directory structure mimicking a package resources layout."""
    resources_dir = tmp_path / "resources"
    
    # Create EN resources
    (resources_dir / "en" / "prompts").mkdir(parents=True)
    (resources_dir / "en" / "prompts" / "system.md").write_text("System Prompt EN")
    (resources_dir / "en" / "prompts" / "user.md").write_text("User Prompt EN")
    
    # Create ZH resources (Partial override)
    (resources_dir / "zh" / "prompts").mkdir(parents=True)
    (resources_dir / "zh" / "prompts" / "system.md").write_text("System Prompt ZH")
    
    return tmp_path

def test_finder_scan_package(mock_package_structure):
    with patch("monoco.core.resource.finder.files") as mock_files, \
         patch("monoco.core.resource.finder.importlib.util.find_spec") as mock_spec:
         
        mock_spec.return_value = True
        mock_files.return_value = mock_package_structure
        
        finder = ResourceFinder()
        nodes = finder.scan_package("dummy.package")
        
        # We expect 3 nodes: en/system.md, en/user.md, zh/system.md
        assert len(nodes) == 3
        
        # Check types
        assert all(n.type == ResourceType.PROMPTS for n in nodes)
        
        # Check languages
        langs = [n.language for n in nodes]
        assert langs.count("en") == 2
        assert langs.count("zh") == 1

def test_manager_get_merged_resources(mock_package_structure):
    with patch("monoco.core.resource.finder.files") as mock_files, \
         patch("monoco.core.resource.finder.importlib.util.find_spec") as mock_spec:
        
        mock_spec.return_value = True
        mock_files.return_value = mock_package_structure
        
        manager = ResourceManager(source_lang="en")
        
        # Scenario 1: Request Source Lang (EN)
        nodes = manager.get_merged_resources("dummy", ResourceType.PROMPTS, "en")
        assert len(nodes) == 2
        content_map = {n.name: n.read_text() for n in nodes}
        assert content_map["system.md"] == "System Prompt EN"
        assert content_map["user.md"] == "User Prompt EN"
        
        # Scenario 2: Request Target Lang (ZH)
        # Should get ZH for system.md (override) and EN for user.md (fallback)
        nodes = manager.get_merged_resources("dummy", ResourceType.PROMPTS, "zh")
        assert len(nodes) == 2
        content_map = {n.name: n.read_text() for n in nodes}
        assert content_map["system.md"] == "System Prompt ZH"
        assert content_map["user.md"] == "User Prompt EN"

def test_manager_extract(mock_package_structure, tmp_path):
    with patch("monoco.core.resource.finder.files") as mock_files, \
         patch("monoco.core.resource.finder.importlib.util.find_spec") as mock_spec:
        
        mock_spec.return_value = True
        mock_files.return_value = mock_package_structure
        
        manager = ResourceManager(source_lang="en")
        nodes = manager.get_merged_resources("dummy", ResourceType.PROMPTS, "zh")
        
        extract_dest = tmp_path / "extracted"
        manager.extract_to(nodes, extract_dest, symlink=False)
        
        assert (extract_dest / "system.md").read_text() == "System Prompt ZH"
        assert (extract_dest / "user.md").read_text() == "User Prompt EN"
