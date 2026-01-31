import sys
from pathlib import Path
from typing import List, Generator, Union
import importlib.util

# Use standard importlib.resources for Python 3.9+
if sys.version_info < (3, 9):
    # Fallback or error - for now assume 3.9+ as this is a modern toolkit
    raise RuntimeError("Monoco requires Python 3.9+")
from importlib.resources import files, as_file

from .models import ResourceNode, ResourceType

class ResourceFinder:
    """
    Scans Python packages for Monoco standard resources.
    Standard Layout: <package>/resources/<lang>/<type>/<file>
    """

    def scan_package(self, package_name: str) -> List[ResourceNode]:
        """
        Traverses the 'resources' directory of a given package.
        Returns a flat list of ResourceNode objects.
        """
        nodes = []
        
        # Check if package exists
        if not importlib.util.find_spec(package_name):
            return []

        try:
            pkg_root = files(package_name)
            resources_root = pkg_root.joinpath("resources")
            
            if not resources_root.is_dir():
                return []
                
            # Iterate over languages (direct children of resources/)
            for lang_dir in resources_root.iterdir():
                if not lang_dir.is_dir() or lang_dir.name.startswith("_"):
                    continue
                
                lang = lang_dir.name
                
                # Iterate over resource types (children of lang/)
                for type_dir in lang_dir.iterdir():
                    if not type_dir.is_dir() or type_dir.name.startswith("_"):
                        continue
                        
                    try:
                        res_type = ResourceType(type_dir.name)
                    except ValueError:
                        res_type = ResourceType.OTHER

                    # Iterate over files (children of type/)
                    # Note: This effectively supports shallow structure. 
                    # For recursive (like skills folders), we might need recursion.
                    # For now, let's assume flat files or folders treated as units (like flow skill dirs).
                    
                    for item in type_dir.iterdir():
                         # For skills, the item might be a directory (Flow Skill)
                         # We treat the directory path as the resource path in that case?
                         # Or we recursively scan?
                         # ResourceNode expects a path.
                         
                         # Use as_file to ensure we have a filesystem path (needed for symlinks/copy)
                         with as_file(item) as item_path:
                             # Note: as_file context manager keeps the temporary file alive if extracted from zip.
                             # But here we probably want the path to persist?
                             # if it's a real file system, item_path is the real path.
                             
                             if item.is_dir():
                                 # Flow skills are directories
                                 # We add the directory itself as a node?
                                 if res_type == ResourceType.SKILLS:
                                     nodes.append(ResourceNode(
                                         name=item.name,
                                         path=item_path,
                                         type=res_type,
                                         language=lang
                                     ))
                             elif item.is_file():
                                 if item.name.startswith("."):
                                     continue
                                     
                                 nodes.append(ResourceNode(
                                     name=item.name,
                                     path=item_path,
                                     type=res_type,
                                     language=lang
                                 ))

        except Exception as e:
            # gracefully handle errors, maybe log?
            print(f"Warning: Error scanning resources in {package_name}: {e}")
            return []

        return nodes
