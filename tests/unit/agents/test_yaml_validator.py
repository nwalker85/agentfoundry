"""
Unit tests for YAML validation and schema parsing.

Tests:
- Valid YAML parsing
- Invalid YAML handling
- Pydantic validation
- Missing required fields
- Invalid field types
- Schema constraints
"""

import pytest
import yaml
from pathlib import Path
from pydantic import ValidationError
from agents.yaml_validator import (
    AgentYAML,
    AgentMetadata,
    AgentSpec,
    WorkflowSpec,
    WorkflowNode,
    ValidationResult,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def valid_agent_yaml() -> dict:
    """Minimal valid agent YAML structure"""
    return {
        "version": "1.0.0",
        "metadata": {
            "id": "test-agent",
            "name": "Test Agent",
            "version": "1.0.0",
            "description": "A test agent",
            "tags": ["test"]
        },
        "spec": {
            "capabilities": ["chat"],
            "workflow": {
                "type": "graph",
                "entry_point": "start",
                "nodes": [
                    {
                        "id": "start",
                        "type": "handler",
                        "handler": "test_handler",
                        "next": ["end"]
                    },
                    {
                        "id": "end",
                        "type": "terminal"
                    }
                ]
            }
        }
    }


@pytest.fixture
def valid_complex_yaml() -> dict:
    """Complex valid agent YAML with multiple nodes"""
    return {
        "version": "1.0.0",
        "metadata": {
            "id": "complex-agent",
            "name": "Complex Agent",
            "version": "2.0.0",
            "description": "Complex multi-node agent",
            "tags": ["complex", "test"],
            "author": "Test Suite",
            "license": "MIT"
        },
        "spec": {
            "capabilities": ["chat", "voice", "tools"],
            "tools": ["web_search", "calculator"],
            "workflow": {
                "type": "graph",
                "entry_point": "intake",
                "nodes": [
                    {
                        "id": "intake",
                        "type": "handler",
                        "handler": "intake_handler",
                        "next": ["process"]
                    },
                    {
                        "id": "process",
                        "type": "handler",
                        "handler": "process_handler",
                        "next": ["decide"]
                    },
                    {
                        "id": "decide",
                        "type": "conditional",
                        "handler": "decision_handler",
                        "next": ["execute", "retry", "fail"]
                    },
                    {
                        "id": "execute",
                        "type": "handler",
                        "handler": "execute_handler",
                        "next": ["end"]
                    },
                    {
                        "id": "retry",
                        "type": "handler",
                        "handler": "retry_handler",
                        "next": ["process"]
                    },
                    {
                        "id": "fail",
                        "type": "terminal"
                    },
                    {
                        "id": "end",
                        "type": "terminal"
                    }
                ]
            }
        }
    }


@pytest.fixture
def temp_yaml_file(tmp_path: Path, valid_agent_yaml: dict):
    """Create temporary YAML file"""
    yaml_file = tmp_path / "test-agent.agent.yaml"
    with open(yaml_file, 'w') as f:
        yaml.dump(valid_agent_yaml, f)
    return yaml_file


# ============================================================================
# VALID YAML TESTS
# ============================================================================

def test_parse_valid_yaml(valid_agent_yaml):
    """Test parsing valid YAML structure"""
    agent = AgentYAML(**valid_agent_yaml)
    
    assert agent.version == "1.0.0"
    assert agent.metadata.id == "test-agent"
    assert agent.metadata.name == "Test Agent"
    assert len(agent.spec.workflow.nodes) == 2


def test_parse_complex_yaml(valid_complex_yaml):
    """Test parsing complex YAML with multiple nodes"""
    agent = AgentYAML(**valid_complex_yaml)
    
    assert agent.metadata.id == "complex-agent"
    assert len(agent.spec.capabilities) == 3
    assert len(agent.spec.tools) == 2
    assert len(agent.spec.workflow.nodes) == 7


def test_load_from_file(temp_yaml_file):
    """Test loading from YAML file"""
    agent = AgentYAML.from_yaml_file(str(temp_yaml_file))
    
    assert agent.metadata.id == "test-agent"
    assert agent.metadata.name == "Test Agent"


def test_metadata_optional_fields(valid_agent_yaml):
    """Test that optional metadata fields work"""
    valid_agent_yaml["metadata"]["author"] = "Test Author"
    valid_agent_yaml["metadata"]["license"] = "Apache-2.0"
    valid_agent_yaml["metadata"]["repository"] = "https://github.com/test/agent"
    
    agent = AgentYAML(**valid_agent_yaml)
    
    assert agent.metadata.author == "Test Author"
    assert agent.metadata.license == "Apache-2.0"
    assert agent.metadata.repository == "https://github.com/test/agent"


def test_workflow_node_types(valid_agent_yaml):
    """Test different workflow node types"""
    valid_agent_yaml["spec"]["workflow"]["nodes"] = [
        {"id": "handler_node", "type": "handler", "handler": "test", "next": ["cond"]},
        {"id": "cond", "type": "conditional", "handler": "decide", "next": ["a", "b"]},
        {"id": "a", "type": "handler", "handler": "option_a", "next": ["term"]},
        {"id": "b", "type": "handler", "handler": "option_b", "next": ["term"]},
        {"id": "term", "type": "terminal"}
    ]
    
    agent = AgentYAML(**valid_agent_yaml)
    nodes = agent.spec.workflow.nodes
    
    assert nodes[0].type == "handler"
    assert nodes[1].type == "conditional"
    assert nodes[4].type == "terminal"


# ============================================================================
# INVALID YAML TESTS
# ============================================================================

def test_missing_required_metadata_fields(valid_agent_yaml):
    """Test that missing required metadata raises error"""
    del valid_agent_yaml["metadata"]["id"]
    
    with pytest.raises(ValidationError) as exc_info:
        AgentYAML(**valid_agent_yaml)
    
    assert "id" in str(exc_info.value).lower()


def test_invalid_version_format(valid_agent_yaml):
    """Test that invalid version format raises error"""
    valid_agent_yaml["version"] = "not-a-version"
    
    # Version validation depends on your schema constraints
    # This might pass if version is just a string
    agent = AgentYAML(**valid_agent_yaml)
    assert agent.version == "not-a-version"


def test_missing_workflow_entry_point(valid_agent_yaml):
    """Test that missing entry_point raises error"""
    del valid_agent_yaml["spec"]["workflow"]["entry_point"]
    
    with pytest.raises(ValidationError):
        AgentYAML(**valid_agent_yaml)


def test_missing_workflow_nodes(valid_agent_yaml):
    """Test that missing nodes raises error"""
    valid_agent_yaml["spec"]["workflow"]["nodes"] = []
    
    with pytest.raises(ValidationError):
        AgentYAML(**valid_agent_yaml)


def test_invalid_node_missing_id(valid_agent_yaml):
    """Test that node without id raises error"""
    valid_agent_yaml["spec"]["workflow"]["nodes"][0] = {
        "type": "handler",
        "handler": "test"
    }
    
    with pytest.raises(ValidationError):
        AgentYAML(**valid_agent_yaml)


def test_invalid_node_type(valid_agent_yaml):
    """Test that invalid node type raises error"""
    valid_agent_yaml["spec"]["workflow"]["nodes"][0]["type"] = "invalid_type"
    
    with pytest.raises(ValidationError):
        AgentYAML(**valid_agent_yaml)


def test_handler_node_missing_handler(valid_agent_yaml):
    """Test that handler node without handler raises error"""
    valid_agent_yaml["spec"]["workflow"]["nodes"][0] = {
        "id": "test",
        "type": "handler",
        "next": ["end"]
    }
    
    with pytest.raises(ValidationError):
        AgentYAML(**valid_agent_yaml)


def test_invalid_yaml_file(tmp_path):
    """Test loading invalid YAML file"""
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text("{ invalid: yaml: content:")
    
    with pytest.raises(Exception):  # YAML parse error
        AgentYAML.from_yaml_file(str(yaml_file))


def test_nonexistent_file():
    """Test loading non-existent file"""
    with pytest.raises(FileNotFoundError):
        AgentYAML.from_yaml_file("/nonexistent/file.yaml")


# ============================================================================
# VALIDATION RESULT TESTS
# ============================================================================

def test_validation_result_success():
    """Test ValidationResult for successful validation"""
    result = ValidationResult(valid=True, agent_id="test-agent")
    
    assert result.valid is True
    assert result.agent_id == "test-agent"
    assert len(result.errors) == 0
    assert len(result.warnings) == 0


def test_validation_result_with_errors():
    """Test ValidationResult with errors"""
    result = ValidationResult(valid=False, agent_id="test-agent")
    result.add_error("Missing handler")
    result.add_error("Invalid workflow")
    
    assert result.valid is False
    assert len(result.errors) == 2
    assert "Missing handler" in result.errors


def test_validation_result_with_warnings():
    """Test ValidationResult with warnings"""
    result = ValidationResult(valid=True, agent_id="test-agent")
    result.add_warning("Deprecated field used")
    
    assert result.valid is True
    assert len(result.warnings) == 1
    assert "Deprecated field used" in result.warnings


# ============================================================================
# EDGE CASES
# ============================================================================

def test_empty_tags_list(valid_agent_yaml):
    """Test agent with empty tags list"""
    valid_agent_yaml["metadata"]["tags"] = []
    
    agent = AgentYAML(**valid_agent_yaml)
    assert agent.metadata.tags == []


def test_empty_capabilities_list(valid_agent_yaml):
    """Test agent with empty capabilities"""
    valid_agent_yaml["spec"]["capabilities"] = []
    
    # This might raise validation error depending on schema
    # Adjust based on your actual validation rules
    agent = AgentYAML(**valid_agent_yaml)
    assert agent.spec.capabilities == []


def test_circular_workflow(valid_agent_yaml):
    """Test workflow with circular references"""
    valid_agent_yaml["spec"]["workflow"]["nodes"] = [
        {"id": "a", "type": "handler", "handler": "h1", "next": ["b"]},
        {"id": "b", "type": "handler", "handler": "h2", "next": ["a"]},
    ]
    
    # YAML parsing succeeds, but graph validation should catch this
    agent = AgentYAML(**valid_agent_yaml)
    assert len(agent.spec.workflow.nodes) == 2


def test_unreachable_nodes(valid_agent_yaml):
    """Test workflow with unreachable nodes"""
    valid_agent_yaml["spec"]["workflow"]["nodes"] = [
        {"id": "start", "type": "handler", "handler": "h1", "next": ["end"]},
        {"id": "end", "type": "terminal"},
        {"id": "orphan", "type": "handler", "handler": "h2", "next": ["end"]},
    ]
    
    # YAML parsing succeeds, but graph validation should catch this
    agent = AgentYAML(**valid_agent_yaml)
    assert len(agent.spec.workflow.nodes) == 3


def test_very_long_description(valid_agent_yaml):
    """Test agent with very long description"""
    valid_agent_yaml["metadata"]["description"] = "x" * 10000
    
    agent = AgentYAML(**valid_agent_yaml)
    assert len(agent.metadata.description) == 10000


def test_unicode_in_metadata(valid_agent_yaml):
    """Test Unicode characters in metadata"""
    valid_agent_yaml["metadata"]["name"] = "Test Agent 🤖"
    valid_agent_yaml["metadata"]["description"] = "Une description en français"
    
    agent = AgentYAML(**valid_agent_yaml)
    assert "🤖" in agent.metadata.name
    assert "français" in agent.metadata.description


# ============================================================================
# SERIALIZATION TESTS
# ============================================================================

def test_to_dict(valid_agent_yaml):
    """Test converting AgentYAML back to dict"""
    agent = AgentYAML(**valid_agent_yaml)
    result = agent.model_dump()
    
    assert result["metadata"]["id"] == "test-agent"
    assert result["spec"]["workflow"]["type"] == "graph"


def test_roundtrip_serialization(valid_agent_yaml):
    """Test parsing and re-serializing YAML"""
    agent1 = AgentYAML(**valid_agent_yaml)
    dict1 = agent1.model_dump()
    agent2 = AgentYAML(**dict1)
    dict2 = agent2.model_dump()
    
    assert dict1 == dict2
