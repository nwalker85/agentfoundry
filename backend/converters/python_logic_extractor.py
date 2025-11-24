"""
Python Logic Extractor for LangGraph Agents
Parses Python agent implementations and extracts:
- System prompts (f-strings)
- Conditional logic (if/elif/else)
- State mutations (state["field"] = value)
- LLM configurations
- Business rules and methods
- Source code
"""

import ast
from typing import Any


class NodeMetadata:
    """Metadata extracted from a single node function"""

    def __init__(self, node_id: str):
        self.node_id = node_id
        self.prompts: list[dict[str, str]] = []
        self.conditions: list[dict[str, str]] = []
        self.state_mutations: list[dict[str, str]] = []
        self.llm_config: dict[str, Any] = {}
        self.business_rules: list[str] = []
        self.source_code: str = ""
        self.function_calls: list[str] = []

    def to_dict(self) -> dict:
        return {
            "node_id": self.node_id,
            "prompts": self.prompts,
            "conditions": self.conditions,
            "state_mutations": self.state_mutations,
            "llm_config": self.llm_config,
            "business_rules": self.business_rules,
            "source_code": self.source_code,
            "function_calls": self.function_calls,
        }


class LangGraphLogicExtractor:
    """Extract implementation logic from Python LangGraph agents"""

    def __init__(self):
        self.current_file_content = ""
        self.current_tree = None

    def extract_from_file(self, python_path: str) -> dict[str, Any]:
        """
        Extract all metadata from a Python agent file

        Args:
            python_path: Path to Python file (e.g., "agents/cibc_card_activation.py")

        Returns:
            Dictionary with nodes, business_methods, class_info
        """
        # Read file
        with open(python_path, encoding="utf-8") as f:
            self.current_file_content = f.read()

        # Parse AST
        try:
            self.current_tree = ast.parse(self.current_file_content)
        except SyntaxError as e:
            return {"error": f"Failed to parse Python file: {e}"}

        # Find the agent class
        agent_class = self._find_agent_class()
        if not agent_class:
            return {"error": "No agent class found in file"}

        # Extract class-level info
        class_info = self._extract_class_info(agent_class)

        # Extract all methods
        nodes = {}
        business_methods = {}

        for item in agent_class.body:
            if isinstance(item, ast.FunctionDef):
                method_name = item.name

                # Skip __init__ and private methods
                if method_name.startswith("__"):
                    continue

                # Check if it's a node handler (process_, human_) or business method
                if method_name.startswith("process_") or method_name.startswith("human_"):
                    # Extract node metadata
                    metadata = self.extract_node_implementation(item, method_name)
                    nodes[method_name] = metadata.to_dict()
                else:
                    # Business logic method
                    business_methods[method_name] = self._extract_business_method(item)

        return {
            "class_info": class_info,
            "nodes": nodes,
            "business_methods": business_methods,
            "total_nodes": len(nodes),
            "total_business_methods": len(business_methods),
        }

    def extract_node_implementation(self, func_node: ast.FunctionDef, node_id: str) -> NodeMetadata:
        """Extract metadata from a single node function"""
        metadata = NodeMetadata(node_id)

        # Extract source code
        metadata.source_code = self._get_source_code(func_node)

        # Extract docstring
        docstring = ast.get_docstring(func_node)
        if docstring:
            metadata.business_rules.append(f"Docstring: {docstring}")

        # Walk the AST to find patterns
        for node in ast.walk(func_node):
            # Extract system prompts
            prompts = self._extract_system_prompts(node)
            if prompts:
                metadata.prompts.extend(prompts)

            # Extract conditions
            conditions = self._extract_conditions(node)
            if conditions:
                metadata.conditions.extend(conditions)

            # Extract state mutations
            mutations = self._extract_state_mutations(node)
            if mutations:
                metadata.state_mutations.extend(mutations)

            # Extract LLM calls
            llm_config = self._extract_llm_config(node)
            if llm_config:
                metadata.llm_config.update(llm_config)

            # Extract function calls (business methods)
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name and not func_name.startswith("_"):
                    metadata.function_calls.append(func_name)

        return metadata

    def _find_agent_class(self) -> ast.ClassDef | None:
        """Find the main agent class (ends with 'Agent')"""
        for node in ast.walk(self.current_tree):
            if isinstance(node, ast.ClassDef):
                if node.name.endswith("Agent"):
                    return node
        return None

    def _extract_class_info(self, class_node: ast.ClassDef) -> dict:
        """Extract class-level information"""
        info = {"class_name": class_node.name, "docstring": ast.get_docstring(class_node) or "", "init_attributes": []}

        # Find __init__ method
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef) and item.name == "__init__":
                # Extract self.attribute = value assignments
                for node in ast.walk(item):
                    if isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Attribute):
                                if isinstance(target.value, ast.Name) and target.value.id == "self":
                                    attr_name = target.attr
                                    # Get the value
                                    value_str = ast.unparse(node.value) if hasattr(ast, "unparse") else str(node.value)
                                    info["init_attributes"].append(
                                        {
                                            "name": attr_name,
                                            "value": value_str[:200],  # Truncate long values
                                        }
                                    )

        return info

    def _extract_system_prompts(self, node: ast.AST) -> list[dict[str, str]]:
        """Extract system_prompt assignments"""
        prompts = []

        # Look for: system_prompt = f"""..."""
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "system_prompt":
                    # Get the value
                    if isinstance(node.value, ast.JoinedStr):  # f-string
                        prompt_text = self._extract_fstring_text(node.value)
                        prompts.append({"type": "system_prompt", "condition": None, "text": prompt_text})

        return prompts

    def _extract_conditions(self, node: ast.AST) -> list[dict[str, str]]:
        """Extract if/elif/else conditions"""
        conditions = []

        if isinstance(node, ast.If):
            # Get the test condition
            condition_str = ast.unparse(node.test) if hasattr(ast, "unparse") else self._format_compare(node.test)

            # Check if this if-block contains system_prompt assignment
            has_system_prompt = False
            for child in ast.walk(node):
                if isinstance(child, ast.Assign):
                    for target in child.targets:
                        if isinstance(target, ast.Name) and target.id == "system_prompt":
                            has_system_prompt = True
                            break

            if has_system_prompt or "workflow_type" in condition_str:
                conditions.append({"type": "if_condition", "test": condition_str, "branch": "if"})

            # Check for elif/else
            if node.orelse:
                for else_node in node.orelse:
                    if isinstance(else_node, ast.If):
                        else_condition = ast.unparse(else_node.test) if hasattr(ast, "unparse") else "else if"
                        conditions.append({"type": "elif_condition", "test": else_condition, "branch": "elif"})

        return conditions

    def _extract_state_mutations(self, node: ast.AST) -> list[dict[str, str]]:
        """Extract state["field"] = value assignments"""
        mutations = []

        # Look for: new_state["field"] = value or state["field"] = value
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Subscript):
                    # Check if it's state or new_state
                    if isinstance(target.value, ast.Name):
                        var_name = target.value.id
                        if var_name in ["state", "new_state"]:
                            # Get the field name
                            if isinstance(target.slice, ast.Constant):
                                field_name = target.slice.value
                            elif isinstance(target.slice, ast.Str):  # Python 3.7
                                field_name = target.slice.s
                            else:
                                field_name = "unknown"

                            # Get the value
                            value_str = ast.unparse(node.value) if hasattr(ast, "unparse") else "..."

                            mutations.append(
                                {
                                    "field": field_name,
                                    "action": value_str[:100],  # Truncate long values
                                    "variable": var_name,
                                }
                            )

        return mutations

    def _extract_llm_config(self, node: ast.AST) -> dict[str, Any]:
        """Extract LLM configuration (ChatOpenAI, ChatAnthropic calls)"""
        config = {}

        if isinstance(node, ast.Call):
            func_name = self._get_function_name(node.func)

            if func_name in ["ChatOpenAI", "ChatAnthropic"]:
                config["model_class"] = func_name

                # Extract keyword arguments
                for keyword in node.keywords:
                    key = keyword.arg
                    value = ast.unparse(keyword.value) if hasattr(ast, "unparse") else "..."
                    config[key] = value

        return config

    def _extract_business_method(self, func_node: ast.FunctionDef) -> dict:
        """Extract business logic method metadata"""
        return {
            "method_name": func_node.name,
            "docstring": ast.get_docstring(func_node) or "",
            "source_code": self._get_source_code(func_node),
            "parameters": [arg.arg for arg in func_node.args.args if arg.arg != "self"],
        }

    def _get_source_code(self, func_node: ast.FunctionDef) -> str:
        """Extract source code for a function"""
        try:
            # Use ast.unparse if available (Python 3.9+)
            if hasattr(ast, "unparse"):
                return ast.unparse(func_node)
            else:
                # Fallback: extract from original source
                return self._extract_from_source(func_node)
        except Exception:
            return "# Source code extraction failed"

    def _extract_from_source(self, func_node: ast.FunctionDef) -> str:
        """Extract source code from original file content"""
        try:
            lines = self.current_file_content.split("\n")
            start_line = func_node.lineno - 1
            end_line = func_node.end_lineno if hasattr(func_node, "end_lineno") else start_line + 10
            return "\n".join(lines[start_line:end_line])
        except Exception:
            return "# Source extraction failed"

    def _extract_fstring_text(self, fstring: ast.JoinedStr) -> str:
        """Extract text from f-string"""
        parts = []
        for value in fstring.values:
            if isinstance(value, ast.Constant):
                parts.append(value.value)
            elif isinstance(value, ast.Str):  # Python 3.7
                parts.append(value.s)
            elif isinstance(value, ast.FormattedValue):
                # Extract the expression
                expr = ast.unparse(value.value) if hasattr(ast, "unparse") else "{...}"
                parts.append(f"{{{expr}}}")
        return "".join(parts)

    def _format_compare(self, node: ast.AST) -> str:
        """Format comparison node to string"""
        if hasattr(ast, "unparse"):
            return ast.unparse(node)

        # Fallback for older Python
        if isinstance(node, ast.Compare):
            left = node.left.id if isinstance(node.left, ast.Name) else "?"
            op = "==" if isinstance(node.ops[0], ast.Eq) else "?"
            right = node.comparators[0].s if isinstance(node.comparators[0], ast.Str) else "?"
            return f"{left} {op} {right}"
        return "unknown"

    def _get_function_name(self, node: ast.AST) -> str | None:
        """Get function name from Call node"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None


# Example usage
if __name__ == "__main__":
    extractor = LangGraphLogicExtractor()
    result = extractor.extract_from_file("/app/agents/cibc_card_activation.py")

    print(f"Found {result['total_nodes']} nodes")
    print(f"Found {result['total_business_methods']} business methods")

    # Print first node details
    if result["nodes"]:
        first_node = list(result["nodes"].values())[0]
        print(f"\nFirst node: {first_node['node_id']}")
        print(f"Prompts: {len(first_node['prompts'])}")
        print(f"Conditions: {len(first_node['conditions'])}")
        print(f"State mutations: {len(first_node['state_mutations'])}")
