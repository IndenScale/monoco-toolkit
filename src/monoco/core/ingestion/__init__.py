"""
Monoco Mailroom - Automated Ingestion System

Provides environment discovery, file watching, and automated conversion
for document ingestion into the Monoco Artifact System.
"""

from .discovery import EnvironmentDiscovery, ConversionTool
from .worker import ConversionWorker, ConversionTask, ConversionResult
from .watcher import DropzoneWatcher, IngestionEvent

__all__ = [
    "EnvironmentDiscovery",
    "ConversionTool",
    "ConversionWorker",
    "ConversionTask",
    "ConversionResult",
    "DropzoneWatcher",
    "IngestionEvent",
]
