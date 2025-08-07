"""Tests for app.storage module."""

from unittest.mock import Mock, patch
from app.storage import ScheduleStorage
from src.core.models import ScheduleState, SchedulerStrategy


class TestScheduleStorage:
    """Test cases for ScheduleStorage functionality."""
    
    def test_storage_initialization(self):
        """Test storage initialization."""
        storage = ScheduleStorage()
        assert hasattr(storage, 'db_path')
    
    @patch('app.storage.sqlite3.connect')
    def test_save_schedule_success(self, mock_connect):
        """Test successful schedule saving."""
        mock_conn = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        storage = ScheduleStorage()
        schedule_state = Mock(spec=ScheduleState)
        schedule_state.to_dict.return_value = {"test": "data"}
        schedule_state.timestamp = "2024-01-01"
        schedule_state.strategy = SchedulerStrategy.GREEDY
        schedule_state.schedule = [Mock(), Mock()]  # 2 submissions
        
        result = storage.save_schedule(schedule_state, "test_schedule.json")
        
        assert result is True
        # Check that execute was called at least once (for the insert)
        assert mock_conn.execute.call_count >= 1
        # Check that commit was called at least once (may be called during init and operation)
        assert mock_conn.commit.call_count >= 1
    
    @patch('app.storage.sqlite3.connect')
    def test_load_schedule_success(self, mock_connect):
        """Test successful schedule loading."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = ('{"test": "data"}',)
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        storage = ScheduleStorage()
        
        result = storage.load_schedule("test_schedule.json")
        
        # Should return a ScheduleState object
        assert result is not None
        assert isinstance(result, ScheduleState)
    
    @patch('app.storage.sqlite3.connect')
    def test_load_schedule_not_found(self, mock_connect):
        """Test schedule loading when not found."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchone.return_value = None
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        storage = ScheduleStorage()
        
        result = storage.load_schedule("nonexistent.json")
        
        assert result is None
    
    @patch('app.storage.sqlite3.connect')
    def test_list_saved_schedules(self, mock_connect):
        """Test listing saved schedules."""
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [
            ("test1.json", "2024-01-01", "GREEDY", 2),
            ("test2.json", "2024-01-02", "OPTIMAL", 3)
        ]
        mock_conn.execute.return_value = mock_cursor
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        storage = ScheduleStorage()
        
        result = storage.list_saved_schedules()
        
        assert len(result) == 2
        assert result[0]["filename"] == "test1.json"
        assert result[1]["filename"] == "test2.json"
    
    @patch('app.storage.sqlite3.connect')
    def test_delete_schedule(self, mock_connect):
        """Test schedule deletion."""
        mock_conn = Mock()
        mock_connect.return_value.__enter__.return_value = mock_conn
        
        storage = ScheduleStorage()
        
        result = storage.delete_schedule("test_schedule.json")
        
        assert result is True
        # Check that execute was called at least once (for the delete)
        assert mock_conn.execute.call_count >= 1
        # Check that commit was called at least once (may be called during init and operation)
        assert mock_conn.commit.call_count >= 1
    
    @patch('app.storage.Path.home')
    def test_storage_initialization_error(self, mock_home):
        """Test storage initialization with error."""
        mock_home.side_effect = Exception("Permission denied")
        
        storage = ScheduleStorage()
        
        assert storage.db_path is None
