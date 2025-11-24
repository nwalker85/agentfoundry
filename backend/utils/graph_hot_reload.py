"""
Graph Hot-Reload System
Caches compiled graphs and reloads them when YAML files change.
"""

import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Base directory for agent YAML files
AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"


class GraphCache:
    """
    In-memory cache for compiled agent graphs with hot-reload support.

    Caches graphs by ID and tracks file modification times to invalidate
    stale entries when YAML files change.
    """

    def __init__(self):
        """Initialize empty cache"""
        # Cache structure: {graph_id: (compiled_graph, yaml_path, mtime)}
        self._cache: dict[str, tuple[Any, Path, float]] = {}
        logger.info("GraphCache initialized")

    def get_graph(self, graph_id: str, yaml_path: str) -> dict[str, Any] | None:
        """
        Get a graph from cache or load from YAML file.

        Args:
            graph_id: Unique graph identifier
            yaml_path: Path to YAML file

        Returns:
            Graph dictionary or None if not found
        """
        path = Path(yaml_path)

        if not path.exists():
            logger.warning(f"Graph YAML not found: {yaml_path}")
            return None

        # Get file modification time
        mtime = path.stat().st_mtime

        # Check cache
        if graph_id in self._cache:
            cached_graph, cached_path, cached_mtime = self._cache[graph_id]

            # Return cached if file hasn't changed
            if cached_path == path and cached_mtime >= mtime:
                logger.debug(f"Cache hit for graph {graph_id}")
                return cached_graph
            else:
                logger.info(f"Cache invalidated for graph {graph_id} (file modified)")

        # Load from file
        try:
            graph_data = self._load_graph_from_yaml(path)

            # Cache the loaded graph
            self._cache[graph_id] = (graph_data, path, mtime)
            logger.info(f"Loaded and cached graph {graph_id} from {path}")

            return graph_data

        except Exception as e:
            logger.error(f"Failed to load graph {graph_id} from {yaml_path}: {e}")
            return None

    def _load_graph_from_yaml(self, yaml_path: Path) -> dict[str, Any]:
        """
        Load graph data from YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            Graph dictionary
        """
        import yaml

        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        return data

    def invalidate(self, graph_id: str) -> None:
        """
        Invalidate a cached graph.

        Args:
            graph_id: Graph to invalidate
        """
        if graph_id in self._cache:
            del self._cache[graph_id]
            logger.info(f"Invalidated cache for graph {graph_id}")

    def invalidate_all(self) -> None:
        """Invalidate all cached graphs"""
        count = len(self._cache)
        self._cache.clear()
        logger.info(f"Invalidated all cached graphs ({count} entries)")

    def get_stats(self) -> dict[str, Any]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        return {"cached_graphs": len(self._cache), "graph_ids": list(self._cache.keys())}


class GraphLoader:
    """
    Loads and compiles graphs from YAML files with hot-reload support.
    """

    def __init__(self):
        """Initialize graph loader with cache"""
        self.cache = GraphCache()
        logger.info("GraphLoader initialized")

    def load_graph(self, graph_id: str, yaml_path: str) -> dict[str, Any] | None:
        """
        Load a graph by ID and YAML path.

        Uses cache with automatic invalidation when files change.

        Args:
            graph_id: Unique graph identifier
            yaml_path: Path to YAML file

        Returns:
            Graph dictionary or None
        """
        return self.cache.get_graph(graph_id, yaml_path)

    def compile_to_python(self, graph_data: dict[str, Any]) -> str:
        """
        Compile graph data to Python LangGraph code.

        Args:
            graph_data: Graph dictionary from YAML

        Returns:
            Python code as string
        """
        try:
            from backend.converters.react_flow_to_python import reactflow_to_python

            # Extract nodes and edges from graph spec
            spec = graph_data.get("spec", {})
            graph_spec = spec.get("graph", {})
            nodes = graph_spec.get("nodes", [])
            edges = graph_spec.get("edges", [])

            # Convert to Python
            python_code = reactflow_to_python({"nodes": nodes, "edges": edges})

            return python_code

        except Exception as e:
            logger.error(f"Failed to compile graph to Python: {e}")
            raise

    def reload_all_graphs(self) -> int:
        """
        Reload all graphs from disk (invalidate cache).

        Returns:
            Number of graphs invalidated
        """
        stats = self.cache.get_stats()
        count = stats["cached_graphs"]
        self.cache.invalidate_all()
        logger.info(f"Reloaded all graphs ({count} invalidated)")
        return count


# Global graph loader instance
graph_loader = GraphLoader()


def get_graph_loader() -> GraphLoader:
    """
    Get the global graph loader instance.

    Returns:
        GraphLoader instance
    """
    return graph_loader


def load_graph_runtime(graph_id: str, yaml_path: str) -> dict[str, Any] | None:
    """
    Load a graph for runtime execution with hot-reload.

    Convenience function that uses the global graph loader.

    Args:
        graph_id: Graph identifier
        yaml_path: Path to YAML file

    Returns:
        Graph dictionary or None
    """
    return graph_loader.load_graph(graph_id, yaml_path)
