"""Tests for app.storage module."""

import json
from unittest.mock import mock_open, patch
from app.storage import Storage


class TestStorage:
    """Test cases for storage functionality."""
    
    def test_storage_initialization(self):
        """Test storage initialization."""
        storage = Storage()
        assert storage.config_file == "config.json"
        assert storage.schedule_file == "schedule.json"
    
    def test_storage_initialization_with_custom_paths(self):
        """Test storage initialization with custom file paths."""
        storage = Storage(config_file="custom_config.json", schedule_file="custom_schedule.json")
        assert storage.config_file == "custom_config.json"
        assert storage.schedule_file == "custom_schedule.json"
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "data"}')
    @patch('pathlib.Path.exists')
    def test_load_config_success(self, mock_exists, mock_file):
        """Test successful config loading."""
        mock_exists.return_value = True
        storage = Storage()
        
        result = storage.load_config()
        
        assert result == {"test": "data"}
        mock_file.assert_called_once_with("config.json", 'r', encoding='utf-8')
    
    @patch('pathlib.Path.exists')
    def test_load_config_file_not_found(self, mock_exists):
        """Test config loading when file doesn't exist."""
        mock_exists.return_value = False
        storage = Storage()
        
        result = storage.load_config()
        
        assert result == {}
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"schedule": "data"}')
    @patch('pathlib.Path.exists')
    def test_load_schedule_success(self, mock_exists, mock_file):
        """Test successful schedule loading."""
        mock_exists.return_value = True
        storage = Storage()
        
        result = storage.load_schedule()
        
        assert result == {"schedule": "data"}
        mock_file.assert_called_once_with("schedule.json", 'r', encoding='utf-8')
    
    @patch('pathlib.Path.exists')
    def test_load_schedule_file_not_found(self, mock_exists):
        """Test schedule loading when file doesn't exist."""
        mock_exists.return_value = False
        storage = Storage()
        
        result = storage.load_schedule()
        
        assert result == {}
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_config(self, mock_file):
        """Test config saving."""
        storage = Storage()
        config_data = {"test": "config"}
        
        storage.save_config(config_data)
        
        mock_file.assert_called_once_with("config.json", 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with(json.dumps(config_data, indent=2))
    
    @patch('builtins.open', new_callable=mock_open)
    def test_save_schedule(self, mock_file):
        """Test schedule saving."""
        storage = Storage()
        schedule_data = {"test": "schedule"}
        
        storage.save_schedule(schedule_data)
        
        mock_file.assert_called_once_with("schedule.json", 'w', encoding='utf-8')
        mock_file().write.assert_called_once_with(json.dumps(schedule_data, indent=2))
    
    @patch('builtins.open', side_effect=FileNotFoundError)
    @patch('pathlib.Path.exists')
    def test_load_config_file_error(self, mock_exists, mock_file):
        """Test config loading with file error."""
        mock_exists.return_value = True
        storage = Storage()
        
        result = storage.load_config()
        
        assert result == {}
    
    @patch('builtins.open', side_effect=json.JSONDecodeError("test", "test", 0))
    @patch('pathlib.Path.exists')
    def test_load_config_json_error(self, mock_exists, mock_file):
        """Test config loading with JSON decode error."""
        mock_exists.return_value = True
        storage = Storage()
        
        result = storage.load_config()
        
        assert result == {}
