from typing import List, Optional, Dict
from pathlib import Path
import shutil
import os

from .models import ResourceNode, ResourceType
from .finder import ResourceFinder

class ResourceManager:
    def __init__(self, source_lang: str = "en"):
        self.finder = ResourceFinder()
        self.source_lang = source_lang

    def list_resources(self, package: str, type: Optional[ResourceType] = None, lang: Optional[str] = None) -> List[ResourceNode]:
        """
        Low-level listing of resources with optional exact filtering.
        """
        all_nodes = self.finder.scan_package(package)
        filtered = []
        for node in all_nodes:
            if type and node.type != type:
                continue
            if lang and node.language != lang:
                continue
            filtered.append(node)
        return filtered

    def get_merged_resources(self, package: str, type: ResourceType, target_lang: str) -> List[ResourceNode]:
        """
        Get resources of a specific type, merging source language defaults with target language overrides.
        Returns a list of unique resources (by name), prioritizing target_lang.
        """
        all_nodes = self.finder.scan_package(package)
        type_nodes = [n for n in all_nodes if n.type == type]
        
        # Dictionary to hold the best match for each filename: name -> ResourceNode
        best_matches: Dict[str, ResourceNode] = {}
        
        # 1. Populate with source language (Default Base)
        for node in type_nodes:
            if node.language == self.source_lang:
                best_matches[node.name] = node
                
        # 2. Override with target language if different
        if target_lang != self.source_lang:
            for node in type_nodes:
                if node.language == target_lang:
                    best_matches[node.name] = node
                    
        return list(best_matches.values())

    def extract_to(self, nodes: List[ResourceNode], destination: Path, symlink: bool = False, force: bool = True) -> int:
        """
        Extracts (copy or symlink) resources to the destination directory.
        Returns count of extracted items.
        
        Args:
            nodes: List of resources to extract
            destination: Target directory
            symlink: If True, create symbolic links instead of copying
            force: If True, overwrite existing files/symlinks
        """
        destination.mkdir(parents=True, exist_ok=True)
        count = 0
        
        for node in nodes:
            dest_path = destination / node.name
            
            if dest_path.exists():
                if not force:
                    continue
                # Remove existing
                if dest_path.is_symlink() or dest_path.is_file():
                    dest_path.unlink()
                elif dest_path.is_dir():
                    shutil.rmtree(dest_path)
            
            try:
                if symlink:
                    # Symlink target must be absolute
                    dest_path.symlink_to(node.path)
                else:
                    if node.path.is_dir():
                        shutil.copytree(node.path, dest_path)
                    else:
                        shutil.copy2(node.path, dest_path)
                count += 1
            except Exception as e:
                print(f"Error extracting {node.name}: {e}")
                
        return count
