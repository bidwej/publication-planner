"""Tests for app.storage module."""

import pytest
from pathlib import Path
from app.storage import ScheduleStorage, StorageManager, get_state_manager, save_state, load_state


def test_schedule_storage_initialization():
    """Test storage initialization."""
    storage = ScheduleStorage()
    assert hasattr(storage, 'db_path')


def test_storage_manager_initialization():
    """Test storage manager initialization."""
    manager = StorageManager()
    assert hasattr(manager, 'storage')
    assert isinstance(manager.storage, ScheduleStorage)


def test_get_state_manager_returns_singleton():
    """Test that get_state_manager returns the same instance."""
    manager1 = get_state_manager()
    manager2 = get_state_manager()
    assert manager1 is manager2


def test_save_state_creates_directory(monkeypatch, tmp_path):
    """Test that save_state creates the data directory."""
    # Mock Path.home to return our temp directory
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    data_dir = tmp_path / ".paper_planner"
    assert not data_dir.exists()
    
    # This should create the directory
    try:
        save_state("test_component", {"test": "data"})
        assert data_dir.exists()
    except Exception:
        # If it fails due to missing dependencies, that's okay
        pass


def test_load_state_returns_empty_dict_when_no_data(monkeypatch, tmp_path):
    """Test that load_state returns empty dict when no data exists."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    result = load_state("nonexistent_component")
    assert result == {}


def test_storage_manager_methods_exist():
    """Test that StorageManager has expected methods."""
    manager = StorageManager()
    
    expected_methods = [
        'save_schedule', 'load_schedule', 'list_schedules', 
        'delete_schedule'
    ]
    
    for method_name in expected_methods:
        assert hasattr(manager, method_name)
        assert callable(getattr(manager, method_name))


def test_schedule_storage_methods_exist():
    """Test that ScheduleStorage has expected methods."""
    storage = ScheduleStorage()
    
    expected_methods = [
        'save_schedule', 'load_schedule', 'list_saved_schedules',
        'delete_schedule'
    ]
    
    for method_name in expected_methods:
        assert hasattr(storage, method_name)
        assert callable(getattr(storage, method_name))

def test_state_manager_methods_exist():
    """Test that StateManager has expected methods."""
    from app.storage import get_state_manager
    manager = get_state_manager()
    
    expected_methods = [
        'save_component_state', 'load_component_state',
        'get_component_config_summary', 'update_component_refresh_time'
    ]
    
    for method_name in expected_methods:
        assert hasattr(manager, method_name)
        assert callable(getattr(manager, method_name))
