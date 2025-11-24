"""
Python LangGraph → ReactFlow Converter
Parses Python LangGraph code and converts to ReactFlow graph structure.
"""

import ast


def parse_langgraph_code(python_code: str) -> dict:
    """
    Parse Python LangGraph code and extract graph structure.

    Args:
        python_code: Python code string containing StateGraph definition

    Returns:
        ReactFlow graph structure with nodes and edges
    """
    nodes = []
    edges = []
    node_counter = 0

    try:
        # Parse Python AST
        tree = ast.parse(python_code)

        # Track node names and their IDs
        node_map = {}

        # Find StateGraph initialization and node/edge definitions
        for node in ast.walk(tree):
            # Look for builder.add_node("name", function)
            if isinstance(node, ast.Call):
                if hasattr(node.func, "attr") and node.func.attr == "add_node":
                    if len(node.args) >= 1:
                        node_name = None
                        node_function = None

                        # Get node name (first arg)
                        if isinstance(node.args[0], ast.Constant):
                            node_name = node.args[0].value
                        elif isinstance(node.args[0], ast.Str):
                            node_name = node.args[0].s

                        # Get function name (second arg if exists)
                        if len(node.args) >= 2:
                            if isinstance(node.args[1], ast.Name):
                                node_function = node.args[1].id
                            elif isinstance(node.args[1], ast.Attribute):
                                node_function = node.args[1].attr

                        if node_name:
                            node_id = f"node_{node_counter}"
                            node_counter += 1

                            # Determine node type
                            node_type = "process"
                            if node_name.lower() in ["start", "entry", "begin"]:
                                node_type = "entry"
                            elif node_name.lower() in ["end", "finish", "complete"]:
                                node_type = "end"
                            elif "decision" in node_name.lower() or "condition" in node_name.lower():
                                node_type = "decision"

                            nodes.append(
                                {
                                    "id": node_id,
                                    "type": node_type,
                                    "position": {"x": 100 + (node_counter * 250), "y": 100},
                                    "data": {
                                        "label": node_name,
                                        "function": node_function or node_name,
                                        "description": f"Node: {node_name}",
                                    },
                                }
                            )

                            node_map[node_name] = node_id

                # Look for builder.add_edge(source, target)
                elif hasattr(node.func, "attr") and node.func.attr == "add_edge":
                    if len(node.args) >= 2:
                        source_name = None
                        target_name = None

                        # Get source
                        if isinstance(node.args[0], ast.Constant):
                            source_name = node.args[0].value
                        elif isinstance(node.args[0], ast.Str):
                            source_name = node.args[0].s

                        # Get target
                        if isinstance(node.args[1], ast.Constant):
                            target_name = node.args[1].value
                        elif isinstance(node.args[1], ast.Str):
                            target_name = node.args[1].s

                        if source_name and target_name:
                            source_id = node_map.get(source_name)
                            target_id = node_map.get(target_name)

                            if source_id and target_id:
                                edges.append(
                                    {
                                        "id": f"edge_{source_id}_{target_id}",
                                        "source": source_id,
                                        "target": target_id,
                                        "type": "default",
                                        "data": {"label": ""},
                                    }
                                )

                # Look for builder.add_conditional_edges
                elif hasattr(node.func, "attr") and node.func.attr == "add_conditional_edges":
                    if len(node.args) >= 2:
                        source_name = None

                        # Get source
                        if isinstance(node.args[0], ast.Constant):
                            source_name = node.args[0].value
                        elif isinstance(node.args[0], ast.Str):
                            source_name = node.args[0].s

                        source_id = node_map.get(source_name)

                        # Get path map (dict of conditions)
                        if len(node.args) >= 2 and isinstance(node.args[1], ast.Dict):
                            for key, value in zip(node.args[1].keys, node.args[1].values):
                                condition = None
                                target_name = None

                                if isinstance(key, ast.Constant):
                                    condition = key.value
                                elif isinstance(key, ast.Str):
                                    condition = key.s

                                if isinstance(value, ast.Constant):
                                    target_name = value.value
                                elif isinstance(value, ast.Str):
                                    target_name = value.s

                                target_id = node_map.get(target_name)

                                if source_id and target_id and condition:
                                    edges.append(
                                        {
                                            "id": f"edge_{source_id}_{target_id}_{condition}",
                                            "source": source_id,
                                            "target": target_id,
                                            "type": "conditional",
                                            "data": {"label": condition, "condition": condition},
                                        }
                                    )

        return {
            "nodes": nodes,
            "edges": edges,
            "metadata": {"imported_from": "python", "node_count": len(nodes), "edge_count": len(edges)},
        }

    except Exception as e:
        # Return error structure
        return {"nodes": [], "edges": [], "error": f"Failed to parse Python code: {e!s}"}


def extract_docstrings(python_code: str) -> dict[str, str]:
    """
    Extract function docstrings from Python code.

    Args:
        python_code: Python code string

    Returns:
        Dictionary mapping function names to docstrings
    """
    docstrings = {}

    try:
        tree = ast.parse(python_code)

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                docstring = ast.get_docstring(node)
                if docstring:
                    docstrings[node.name] = docstring

    except:
        pass

    return docstrings
