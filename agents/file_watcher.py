"""
File Watcher - Monitors agent directory for YAML file changes

Uses watchfiles for efficient file system monitoring.
Triggers callbacks on add/modify/delete events.
"""

import logging
from enum import Enum
from pathlib import Path
from typing import Callable, Set

from watchfiles import Change, awatch

logger = logging.getLogger(__name__)


class FileChangeType(str, Enum):
    """Types of file changes we care about."""
    ADDED = "added"
    MODIFIED = "modified"
    DELETED = "deleted"


class AgentFileWatcher:
    """
    Watches agent directory for .agent.yaml file changes.
    
    Monitors for:
    - New files → Load agent
    - Modified files → Reload agent
    - Deleted files → Unload agent
    """
    
    def __init__(
        self,
        watch_path: Path,
        on_change: Callable[[FileChangeType, Path], None]
    ):
        """Initialize file watcher.
        
        Args:
            watch_path: Directory to watch
            on_change: Async callback(change_type, file_path)
        """
        self.watch_path = Path(watch_path)
        self.on_change = on_change
        self._running = False
        self._watched_files: Set[Path] = set()
        
        if not self.watch_path.exists():
            raise FileNotFoundError(f"Watch path does not exist: {watch_path}")
        
        logger.info(f"AgentFileWatcher initialized for: {self.watch_path}")
    
    async def start(self):
        """Start watching for file changes.
        
        This is a blocking call that runs the watch loop.
        """
        logger.info(f"Starting file watch on: {self.watch_path}")
        self._running = True
        
        # Get initial list of agent YAML files
        self._scan_directory()
        
        try:
            async for changes in awatch(
                self.watch_path,
                watch_filter=self._filter_agent_yaml,
                recursive=False  # Only watch top-level directory
            ):
                if not self._running:
                    break
                
                for change_type, file_path_str in changes:
                    file_path = Path(file_path_str)
                    
                    # Map watchfiles Change enum to our enum
                    if change_type == Change.added:
                        await self._handle_change(FileChangeType.ADDED, file_path)
                    elif change_type == Change.modified:
                        await self._handle_change(FileChangeType.MODIFIED, file_path)
                    elif change_type == Change.deleted:
                        await self._handle_change(FileChangeType.DELETED, file_path)
        
        except Exception as e:
            logger.error(f"File watcher error: {e}", exc_info=True)
            raise
        finally:
            logger.info("File watcher stopped")
    
    async def stop(self):
        """Stop watching for file changes."""
        logger.info("Stopping file watcher...")
        self._running = False
    
    def _filter_agent_yaml(self, change: Change, path: str) -> bool:
        """Filter to only watch .agent.yaml files.
        
        Args:
            change: Type of change
            path: File path
            
        Returns:
            True if we should process this change
        """
        return path.endswith('.agent.yaml')
    
    def _scan_directory(self):
        """Scan directory for existing agent YAML files."""
        for yaml_file in self.watch_path.glob("*.agent.yaml"):
            self._watched_files.add(yaml_file)
        
        logger.info(f"Found {len(self._watched_files)} existing agent YAML files")
    
    async def _handle_change(self, change_type: FileChangeType, file_path: Path):
        """Handle a file change event.
        
        Args:
            change_type: Type of change (added/modified/deleted)
            file_path: Path to changed file
        """
        logger.info(f"File {change_type.value}: {file_path.name}")
        
        try:
            # Update our tracked files
            if change_type == FileChangeType.ADDED:
                self._watched_files.add(file_path)
            elif change_type == FileChangeType.DELETED:
                self._watched_files.discard(file_path)
            
            # Trigger callback
            await self.on_change(change_type, file_path)
            
        except Exception as e:
            logger.error(
                f"Error handling {change_type.value} for {file_path}: {e}",
                exc_info=True
            )
    
    @property
    def is_running(self) -> bool:
        """Check if watcher is running."""
        return self._running
    
    @property
    def watched_file_count(self) -> int:
        """Get count of currently watched files."""
        return len(self._watched_files)
    
    def get_watched_files(self) -> Set[Path]:
        """Get set of currently watched files."""
        return self._watched_files.copy()
