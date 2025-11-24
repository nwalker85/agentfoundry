"""
ReactFlow → Python LangGraph Converter
Generates Python LangGraph code from ReactFlow graph structure.
"""

from typing import Any


def generate_langgraph_code(graph_data: dict, agent_name: str = "agent") -> str:
    """
    Convert ReactFlow graph to Python LangGraph code.

    Args:
        graph_data: ReactFlow graph with nodes and edges
        agent_name: Name for the generated agent

    Returns:
        Python code string for LangGraph agent
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    # Build imports
    imports = [
        "from typing import TypedDict, Literal, Any",
        "from langgraph.graph import StateGraph, START, END",
    ]

    # Build state class
    state_class = f"""
class {agent_name.capitalize()}State(TypedDict, total=False):
    \"\"\"State for {agent_name} agent\"\"\"
    # Add your state fields here
    input: str
    output: str
    error: str | None
"""

    # Build node functions
    node_functions = []
    for node in nodes:
        node_id = node.get("id", "")
        node_data = node.get("data", {})
        function_name = node_data.get("function", node_data.get("label", "node"))
        label = node_data.get("label", function_name)
        description = node_data.get("description", f"Process node: {label}")

        # Sanitize function name
        function_name = sanitize_identifier(function_name)

        node_functions.append(f"""
def {function_name}(state: {agent_name.capitalize()}State) -> {agent_name.capitalize()}State:
    \"\"\"
    {description}
    \"\"\"
    # TODO: Implement {label} logic
    return state
""")

    # Build graph construction
    graph_builder = f"""
# Build the graph
builder = StateGraph({agent_name.capitalize()}State)
"""

    # Add nodes
    for node in nodes:
        node_data = node.get("data", {})
        node_label = node_data.get("label", "node")
        function_name = sanitize_identifier(node_data.get("function", node_label))

        graph_builder += f'builder.add_node("{node_label}", {function_name})\n'

    graph_builder += "\n"

    # Add edges
    # Group edges by source to identify conditional edges
    edge_map = {}
    for edge in edges:
        source = edge.get("source")
        target = edge.get("target")
        edge_type = edge.get("type", "default")
        edge_data = edge.get("data", {})

        if source not in edge_map:
            edge_map[source] = []

        edge_map[source].append({"target": target, "type": edge_type, "data": edge_data})

    # Find node labels by ID
    node_labels = {node["id"]: node["data"].get("label", "node") for node in nodes}

    # Add START edges
    for node in nodes:
        if node.get("type") == "entry" or node["data"].get("label") == "start":
            node_label = node["data"].get("label")
            graph_builder += f'builder.add_edge(START, "{node_label}")\n'

    # Add END edges
    for node in nodes:
        if node.get("type") == "end" or node["data"].get("label") == "end":
            node_label = node["data"].get("label")
            # Find edges pointing to this node
            for source_id, targets in edge_map.items():
                for target_edge in targets:
                    if target_edge["target"] == node["id"]:
                        source_label = node_labels.get(source_id)
                        if source_label:
                            graph_builder += f'builder.add_edge("{source_label}", END)\n'

    # Add normal edges
    for source_id, targets in edge_map.items():
        source_label = node_labels.get(source_id)

        # Check if this is a conditional edge (multiple targets)
        conditional_targets = [t for t in targets if t["type"] == "conditional"]

        if conditional_targets:
            # Conditional edges
            path_map = {}
            for target_edge in conditional_targets:
                target_label = node_labels.get(target_edge["target"])
                condition = target_edge["data"].get("condition", target_edge["data"].get("label", "default"))
                if target_label:
                    path_map[condition] = target_label

            if path_map:
                graph_builder += "builder.add_conditional_edges(\n"
                graph_builder += f'    "{source_label}",\n'
                graph_builder += "    # TODO: Add routing function here\n"
                graph_builder += f"    {path_map}\n"
                graph_builder += ")\n"
        else:
            # Regular edges
            for target_edge in targets:
                if target_edge["type"] != "conditional":
                    target_label = node_labels.get(target_edge["target"])
                    if target_label and source_label:
                        # Skip if target is END (handled above)
                        target_node = next((n for n in nodes if n["id"] == target_edge["target"]), None)
                        if target_node and target_node.get("type") != "end":
                            graph_builder += f'builder.add_edge("{source_label}", "{target_label}")\n'

    # Compile graph
    graph_builder += """
# Compile the graph
graph = builder.compile()
"""

    # Build main execution
    main_code = f"""
# Example usage
if __name__ == "__main__":
    initial_state = {{
        "input": "Hello, {agent_name}!",
        "output": "",
        "error": None
    }}

    result = graph.invoke(initial_state)
    print(result)
"""

    # Combine all parts
    full_code = "\n".join(imports)
    full_code += "\n"
    full_code += state_class
    full_code += "\n"
    full_code += "\n".join(node_functions)
    full_code += "\n"
    full_code += graph_builder
    full_code += "\n"
    full_code += main_code

    return full_code


def sanitize_identifier(name: str) -> str:
    """
    Convert a label to a valid Python identifier.

    Args:
        name: Original name

    Returns:
        Valid Python identifier
    """
    import re

    # Replace spaces and special chars with underscores
    name = re.sub(r"[^a-zA-Z0-9_]", "_", name)

    # Remove leading/trailing underscores
    name = name.strip("_")

    # Ensure it doesn't start with a number
    if name and name[0].isdigit():
        name = f"node_{name}"

    # Default if empty
    if not name:
        name = "node"

    return name.lower()


def extract_node_metadata(graph_data: dict) -> dict[str, Any]:
    """
    Extract metadata about the graph structure.

    Args:
        graph_data: ReactFlow graph

    Returns:
        Metadata dictionary
    """
    nodes = graph_data.get("nodes", [])
    edges = graph_data.get("edges", [])

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "node_types": list(set(n.get("type", "default") for n in nodes)),
        "has_conditional_edges": any(e.get("type") == "conditional" for e in edges),
        "entry_nodes": [n["data"].get("label") for n in nodes if n.get("type") == "entry"],
        "end_nodes": [n["data"].get("label") for n in nodes if n.get("type") == "end"],
    }
