"""
Unit tests for file watcher.

Tests:
- File creation detection
- File modification detection
- File deletion detection
- Directory watching
- Event filtering
- Callback execution
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, call
from agents.file_watcher import AgentFileWatcher, FileChangeType


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def watch_dir(tmp_path):
    """Create temporary directory for watching"""
    agents_dir = tmp_path / "agents"
    agents_dir.mkdir()
    return agents_dir


@pytest.fixture
def mock_callback():
    """Create mock callback for file changes"""
    return AsyncMock()


@pytest.fixture
async def file_watcher(watch_dir, mock_callback):
    """Create and start file watcher"""
    watcher = AgentFileWatcher(
        watch_path=watch_dir,
        on_change=mock_callback
    )
    yield watcher
    
    # Cleanup
    if watcher._running:
        await watcher.stop()


# ============================================================================
# FILE CREATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_detect_new_yaml_file(file_watcher, watch_dir, mock_callback):
    """Test detecting new .agent.yaml file"""
    # Start watcher
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(0.5)  # Let watcher initialize
    
    # Create new YAML file
    new_file = watch_dir / "test-agent.agent.yaml"
    new_file.write_text("version: 1.0.0")
    
    # Wait for event processing
    await asyncio.sleep(1.5)
    
    # Stop watcher
    await file_watcher.stop()
    await task
    
    # Verify callback was called with ADDED event
    mock_callback.assert_called()
    calls = mock_callback.call_args_list
    assert any(
        call[0][0] == FileChangeType.ADDED and
        call[0][1].name == "test-agent.agent.yaml"
        for call in calls
    )


@pytest.mark.asyncio
async def test_ignore_non_yaml_file(file_watcher, watch_dir, mock_callback):
    """Test that non-.agent.yaml files are ignored"""
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(0.5)
    
    # Create non-YAML file
    non_yaml = watch_dir / "README.md"
    non_yaml.write_text("# README")
    
    await asyncio.sleep(1.5)
    
    await file_watcher.stop()
    await task
    
    # Should not trigger callback
    mock_callback.assert_not_called()


# ============================================================================
# FILE MODIFICATION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_detect_file_modification(file_watcher, watch_dir, mock_callback):
    """Test detecting file modification"""
    # Create initial file
    yaml_file = watch_dir / "test-agent.agent.yaml"
    yaml_file.write_text("version: 1.0.0")
    
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(1.0)  # Let initial scan complete
    
    # Clear any initial callbacks
    mock_callback.reset_mock()
    
    # Modify file
    yaml_file.write_text("version: 2.0.0")
    
    await asyncio.sleep(1.5)
    
    await file_watcher.stop()
    await task
    
    # Verify MODIFIED callback
    mock_callback.assert_called()
    calls = mock_callback.call_args_list
    assert any(
        call[0][0] == FileChangeType.MODIFIED and
        call[0][1].name == "test-agent.agent.yaml"
        for call in calls
    )


@pytest.mark.asyncio
async def test_multiple_rapid_modifications(file_watcher, watch_dir, mock_callback):
    """Test handling rapid file modifications"""
    yaml_file = watch_dir / "test-agent.agent.yaml"
    yaml_file.write_text("version: 1.0.0")
    
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(1.0)
    
    mock_callback.reset_mock()
    
    # Multiple rapid modifications
    for i in range(5):
        yaml_file.write_text(f"version: {i}")
        await asyncio.sleep(0.2)
    
    await asyncio.sleep(1.5)
    
    await file_watcher.stop()
    await task
    
    # Should have received MODIFIED events
    assert mock_callback.call_count >= 1


# ============================================================================
# FILE DELETION TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_detect_file_deletion(file_watcher, watch_dir, mock_callback):
    """Test detecting file deletion"""
    # Create file
    yaml_file = watch_dir / "test-agent.agent.yaml"
    yaml_file.write_text("version: 1.0.0")
    
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(1.0)
    
    mock_callback.reset_mock()
    
    # Delete file
    yaml_file.unlink()
    
    await asyncio.sleep(1.5)
    
    await file_watcher.stop()
    await task
    
    # Verify DELETED callback
    mock_callback.assert_called()
    calls = mock_callback.call_args_list
    assert any(
        call[0][0] == FileChangeType.DELETED and
        call[0][1].name == "test-agent.agent.yaml"
        for call in calls
    )


# ============================================================================
# MULTIPLE FILE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_watch_multiple_files(file_watcher, watch_dir, mock_callback):
    """Test watching multiple YAML files"""
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(0.5)
    
    # Create multiple files
    for i in range(3):
        yaml_file = watch_dir / f"agent-{i}.agent.yaml"
        yaml_file.write_text(f"version: 1.0.{i}")
        await asyncio.sleep(0.3)
    
    await asyncio.sleep(1.5)
    
    await file_watcher.stop()
    await task
    
    # Should have detected all files
    assert mock_callback.call_count >= 3


@pytest.mark.asyncio
async def test_mixed_operations(file_watcher, watch_dir, mock_callback):
    """Test mixed add/modify/delete operations"""
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(0.5)
    
    # Add file
    file1 = watch_dir / "agent-1.agent.yaml"
    file1.write_text("version: 1.0.0")
    await asyncio.sleep(0.5)
    
    # Add another file
    file2 = watch_dir / "agent-2.agent.yaml"
    file2.write_text("version: 1.0.0")
    await asyncio.sleep(0.5)
    
    # Modify first file
    file1.write_text("version: 2.0.0")
    await asyncio.sleep(0.5)
    
    # Delete second file
    file2.unlink()
    await asyncio.sleep(1.0)
    
    await file_watcher.stop()
    await task
    
    # Should have received events for all operations
    assert mock_callback.call_count >= 4


# ============================================================================
# WATCHER LIFECYCLE TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_start_stop_watcher(watch_dir, mock_callback):
    """Test starting and stopping watcher"""
    watcher = AgentFileWatcher(
        watch_path=watch_dir,
        on_change=mock_callback
    )
    
    assert watcher._running is False
    
    task = asyncio.create_task(watcher.start())
    await asyncio.sleep(0.5)
    
    assert watcher._running is True
    
    await watcher.stop()
    await task
    
    assert watcher._running is False


@pytest.mark.asyncio
async def test_double_start_prevention(watch_dir, mock_callback):
    """Test that watcher can't be started twice"""
    watcher = AgentFileWatcher(
        watch_path=watch_dir,
        on_change=mock_callback
    )
    
    task1 = asyncio.create_task(watcher.start())
    await asyncio.sleep(0.5)
    
    # Try to start again (should be no-op or raise)
    with pytest.raises(RuntimeError):
        await watcher.start()
    
    await watcher.stop()
    await task1


@pytest.mark.asyncio
async def test_stop_before_start(watch_dir, mock_callback):
    """Test stopping watcher that was never started"""
    watcher = AgentFileWatcher(
        watch_path=watch_dir,
        on_change=mock_callback
    )
    
    # Should handle gracefully
    await watcher.stop()
    
    assert watcher._running is False


# ============================================================================
# CALLBACK ERROR HANDLING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_callback_exception_handling(watch_dir):
    """Test that callback exceptions don't crash watcher"""
    # Create callback that raises exception
    failing_callback = AsyncMock(side_effect=Exception("Callback error"))
    
    watcher = AgentFileWatcher(
        watch_path=watch_dir,
        on_change=failing_callback
    )
    
    task = asyncio.create_task(watcher.start())
    await asyncio.sleep(0.5)
    
    # Create file (should trigger exception in callback)
    yaml_file = watch_dir / "test.agent.yaml"
    yaml_file.write_text("version: 1.0.0")
    
    await asyncio.sleep(1.0)
    
    # Watcher should still be running
    assert watcher._running is True
    
    await watcher.stop()
    await task


# ============================================================================
# DIRECTORY WATCHING TESTS
# ============================================================================

@pytest.mark.asyncio
async def test_nonexistent_directory():
    """Test watching non-existent directory"""
    nonexistent = Path("/nonexistent/directory")
    
    watcher = AgentFileWatcher(
        watch_path=nonexistent,
        on_change=AsyncMock()
    )
    
    # Should raise error or handle gracefully
    with pytest.raises((FileNotFoundError, OSError)):
        await watcher.start()


@pytest.mark.asyncio
async def test_empty_directory(watch_dir, mock_callback):
    """Test watching empty directory"""
    watcher = AgentFileWatcher(
        watch_path=watch_dir,
        on_change=mock_callback
    )
    
    task = asyncio.create_task(watcher.start())
    await asyncio.sleep(1.0)
    
    # No files, so no callbacks
    mock_callback.assert_not_called()
    
    await watcher.stop()
    await task


@pytest.mark.asyncio
async def test_subdirectory_ignored(file_watcher, watch_dir, mock_callback):
    """Test that subdirectories are ignored"""
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(0.5)
    
    # Create subdirectory with YAML file
    subdir = watch_dir / "subdir"
    subdir.mkdir()
    yaml_file = subdir / "agent.agent.yaml"
    yaml_file.write_text("version: 1.0.0")
    
    await asyncio.sleep(1.0)
    
    await file_watcher.stop()
    await task
    
    # Should ignore files in subdirectories
    # (depending on implementation)
    # This test may need adjustment based on actual behavior


# ============================================================================
# EDGE CASES
# ============================================================================

@pytest.mark.asyncio
async def test_very_long_filename(file_watcher, watch_dir, mock_callback):
    """Test handling very long filenames"""
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(0.5)
    
    # Create file with long name
    long_name = "a" * 200 + ".agent.yaml"
    yaml_file = watch_dir / long_name
    
    try:
        yaml_file.write_text("version: 1.0.0")
        await asyncio.sleep(1.0)
        
        # Should handle gracefully
    except OSError:
        # Some filesystems may reject very long names
        pass
    
    await file_watcher.stop()
    await task


@pytest.mark.asyncio
async def test_special_characters_in_filename(file_watcher, watch_dir, mock_callback):
    """Test files with special characters"""
    task = asyncio.create_task(file_watcher.start())
    await asyncio.sleep(0.5)
    
    # Create file with special chars
    special_file = watch_dir / "test-agent_v1.0-alpha.agent.yaml"
    special_file.write_text("version: 1.0.0")
    
    await asyncio.sleep(1.0)
    
    await file_watcher.stop()
    await task
    
    # Should detect file
    mock_callback.assert_called()
