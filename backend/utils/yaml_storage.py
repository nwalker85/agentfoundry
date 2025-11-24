"""
YAML Storage Utilities for Agent Graphs
Handles reading/writing agent graph definitions to/from YAML files.
"""

import logging
from datetime import datetime
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)

# Base directory for all agent YAML files
AGENTS_DIR = Path(__file__).parent.parent.parent / "agents"


def ensure_directories() -> None:
    """
    Create directory structure for agent YAML storage.

    Structure:
        agents/
          user/
            {org-id}/
              {domain-id}/
          channels/
            chat/
            voice/
            api/
          system/
          templates/
    """
    directories = [
        AGENTS_DIR / "user",
        AGENTS_DIR / "channels" / "chat",
        AGENTS_DIR / "channels" / "voice",
        AGENTS_DIR / "channels" / "api",
        AGENTS_DIR / "system",
        AGENTS_DIR / "templates",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {directory}")


def get_yaml_path(
    graph_type: str, name: str, channel: str | None = None, org_id: str | None = None, domain_id: str | None = None
) -> Path:
    """
    Get the file path for a graph's YAML file based on its type.

    Args:
        graph_type: 'user', 'channel', or 'system'
        name: Agent/workflow name
        channel: For channel type: 'chat', 'voice', 'api'
        org_id: For user type: organization ID
        domain_id: For user type: domain ID

    Returns:
        Path object for the YAML file
    """
    # Sanitize name for filename
    safe_name = name.lower().replace(" ", "-").replace("/", "-")
    filename = f"{safe_name}.yaml"

    if graph_type == "user":
        if not org_id or not domain_id:
            raise ValueError("User agents require org_id and domain_id")
        # Ensure org/domain directories exist
        path = AGENTS_DIR / "user" / org_id / domain_id
        path.mkdir(parents=True, exist_ok=True)
        return path / filename

    elif graph_type == "channel":
        if not channel:
            raise ValueError("Channel workflows require channel (chat/voice/api)")
        path = AGENTS_DIR / "channels" / channel
        path.mkdir(parents=True, exist_ok=True)
        return path / filename

    elif graph_type == "system":
        path = AGENTS_DIR / "system"
        path.mkdir(parents=True, exist_ok=True)
        return path / filename

    else:
        raise ValueError(f"Invalid graph_type: {graph_type}")


def write_graph_yaml(graph_data: dict) -> str:
    """
    Write graph data to YAML file.

    Args:
        graph_data: Complete graph dictionary with metadata and spec

    Returns:
        String path where YAML was written
    """
    # Extract metadata
    metadata = graph_data.get("metadata", {})
    graph_type = metadata.get("type", "user")
    name = metadata.get("name", "untitled-graph")
    channel = metadata.get("channel")
    org_id = metadata.get("organization_id")
    domain_id = metadata.get("domain_id")

    # Get file path
    yaml_path = get_yaml_path(graph_type=graph_type, name=name, channel=channel, org_id=org_id, domain_id=domain_id)

    # Ensure parent directory exists
    yaml_path.parent.mkdir(parents=True, exist_ok=True)

    # Add updated timestamp
    if "metadata" not in graph_data:
        graph_data["metadata"] = {}
    graph_data["metadata"]["updated"] = datetime.utcnow().isoformat() + "Z"

    # Write YAML
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(graph_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    logger.info(f"Wrote graph YAML to: {yaml_path}")
    return str(yaml_path)


def read_graph_yaml(yaml_path: str) -> dict:
    """
    Read graph data from YAML file.

    Args:
        yaml_path: Path to YAML file

    Returns:
        Dictionary with graph data
    """
    path = Path(yaml_path)

    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {yaml_path}")

    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    logger.info(f"Read graph YAML from: {yaml_path}")
    return data


def delete_graph_yaml(yaml_path: str) -> None:
    """
    Delete a graph's YAML file.

    Args:
        yaml_path: Path to YAML file to delete
    """
    path = Path(yaml_path)

    if path.exists():
        path.unlink()
        logger.info(f"Deleted graph YAML: {yaml_path}")

        # Clean up empty parent directories (org/domain folders)
        try:
            if path.parent != AGENTS_DIR:
                # Remove domain directory if empty
                if not any(path.parent.iterdir()):
                    path.parent.rmdir()
                    logger.info(f"Removed empty directory: {path.parent}")

                    # Remove org directory if empty
                    if path.parent.parent != AGENTS_DIR and not any(path.parent.parent.iterdir()):
                        path.parent.parent.rmdir()
                        logger.info(f"Removed empty directory: {path.parent.parent}")
        except Exception as e:
            logger.warning(f"Could not clean up empty directories: {e}")
    else:
        logger.warning(f"YAML file not found for deletion: {yaml_path}")


def create_graph_yaml_template(
    graph_type: str, name: str, channel: str | None = None, org_id: str | None = None, domain_id: str | None = None
) -> dict:
    """
    Create a template graph YAML structure.

    Args:
        graph_type: 'user', 'channel', or 'system'
        name: Graph name
        channel: For channel type
        org_id: For user type
        domain_id: For user type

    Returns:
        Template dictionary
    """
    import uuid

    template = {
        "apiVersion": "foundry.ai/v1",
        "kind": "AgentGraph",
        "metadata": {
            "id": str(uuid.uuid4()),
            "name": name,
            "type": graph_type,
            "version": "1.0.0",
            "description": f"Graph for {name}",
            "created": datetime.utcnow().isoformat() + "Z",
            "updated": datetime.utcnow().isoformat() + "Z",
        },
        "spec": {"state_schema_id": None, "triggers": [], "graph": {"nodes": [], "edges": []}},
    }

    # Add type-specific metadata
    if graph_type == "channel" and channel:
        template["metadata"]["channel"] = channel

    if graph_type == "user" and org_id and domain_id:
        template["metadata"]["organization_id"] = org_id
        template["metadata"]["domain_id"] = domain_id

    if graph_type == "system":
        template["metadata"]["is_system_agent"] = True
        template["metadata"]["system_tier"] = 0

    return template


def list_graph_yamls(graph_type: str | None = None, channel: str | None = None) -> list[Path]:
    """
    List all graph YAML files.

    Args:
        graph_type: Filter by type ('user', 'channel', 'system')
        channel: Filter by channel (for channel type)

    Returns:
        List of Path objects for YAML files
    """
    ensure_directories()

    yaml_files = []

    if graph_type == "user" or graph_type is None:
        user_dir = AGENTS_DIR / "user"
        if user_dir.exists():
            yaml_files.extend(user_dir.rglob("*.yaml"))

    if graph_type == "channel" or graph_type is None:
        channels_dir = AGENTS_DIR / "channels"
        if channel:
            # Filter by specific channel
            channel_dir = channels_dir / channel
            if channel_dir.exists():
                yaml_files.extend(channel_dir.glob("*.yaml"))
        # All channels
        elif channels_dir.exists():
            yaml_files.extend(channels_dir.rglob("*.yaml"))

    if graph_type == "system" or graph_type is None:
        system_dir = AGENTS_DIR / "system"
        if system_dir.exists():
            yaml_files.extend(system_dir.glob("*.yaml"))

    # Exclude templates directory
    yaml_files = [f for f in yaml_files if "templates" not in f.parts]

    return sorted(yaml_files)
