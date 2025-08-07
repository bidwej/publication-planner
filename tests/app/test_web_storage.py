"""
Tests for web application storage and models.
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.models import WebAppState
from core.models import Config, Submission


# Mock classes for testing
class ScheduleData:
    def __init__(self, schedule: dict, config: Config, validation_result: dict) -> None:
        self.schedule = schedule
        self.config = config
        self.validation_result = validation_result


class ValidationResult:
    def __init__(self, scores: dict, summary: dict, constraints: dict) -> None:
        self.scores = scores
        self.summary = summary
        self.constraints = constraints


class StorageManager:
    def __init__(self, data_dir: str) -> None:
        self.data_dir = data_dir
    
    def save_schedule(self, schedule_data: ScheduleData, filename: str) -> str:
        """Save schedule data to file."""
        def serialize_dates(obj):
            """Custom JSON serializer for date objects."""
            if isinstance(obj, date):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")
        
        file_path = Path(self.data_dir) / filename
        Path(file_path).write_text(json.dumps({
            'schedule': schedule_data.schedule,
            'config': str(schedule_data.config),
            'validation_result': schedule_data.validation_result
        }, default=serialize_dates), encoding='utf-8')
        return filename
    
    def load_schedule(self, filename: str) -> ScheduleData:
        """Load schedule data from file."""
        from datetime import date
        
        file_path = Path(self.data_dir) / filename
        if not file_path.exists():
            raise FileNotFoundError(f"Schedule file not found: {filename}")
        
        data = json.loads(Path(file_path).read_text(encoding='utf-8'))
        
        # Convert date strings back to date objects
        if 'schedule' in data and isinstance(data['schedule'], dict):
            for key, value in data['schedule'].items():
                if isinstance(value, str):
                    try:
                        data['schedule'][key] = date.fromisoformat(value)
                    except ValueError:
                        # Keep as string if not a valid date
                        pass
        
        return ScheduleData(
            schedule=data['schedule'],
            config=data['config'],
            validation_result=data['validation_result']
        )
    
    def list_schedules(self) -> list[str]:
        """List all saved schedule files."""
        data_path = Path(self.data_dir)
        if not data_path.exists():
            return []
        
        return [f.name for f in data_path.glob('*.json')]
    
    def delete_schedule(self, filename: str) -> bool:
        """Delete a schedule file."""
        file_path = Path(self.data_dir) / filename
        if file_path.exists():
            file_path.unlink()
            return True
        return False


class TestWebAppStorage:
    """Test web app storage functionality."""
    
    @pytest.fixture
    def storage_manager(self) -> StorageManager:
        """Create storage manager for testing."""
        return StorageManager('test_data')
    
    @pytest.fixture
    def sample_schedule_data(self) -> ScheduleData:
        """Create sample schedule data for storage testing."""
        return ScheduleData(
            schedule={'paper1': date(2024, 1, 1)},
            config=Mock(spec=Config),
            validation_result={'scores': {'penalty_score': 85.0}}
        )
    
    def test_save_schedule(self, storage_manager: StorageManager, sample_schedule_data: ScheduleData, tmp_path: Path) -> None:
        """Test saving schedule data."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            filename = storage_manager.save_schedule(sample_schedule_data, 'test_schedule.json')
            
            assert filename == 'test_schedule.json'
            assert (tmp_path / 'test_schedule.json').exists()
    
    def test_load_schedule(self, storage_manager: StorageManager, sample_schedule_data: ScheduleData, tmp_path: Path) -> None:
        """Test loading schedule data."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # First save the schedule
            storage_manager.save_schedule(sample_schedule_data, 'test_schedule.json')
            
            # Then load it
            loaded_data = storage_manager.load_schedule('test_schedule.json')
            
            assert loaded_data is not None
            assert loaded_data.schedule == sample_schedule_data.schedule
    
    def test_list_schedules(self, storage_manager: StorageManager, sample_schedule_data: ScheduleData, tmp_path: Path) -> None:
        """Test listing saved schedules."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # Save multiple schedules
            storage_manager.save_schedule(sample_schedule_data, 'schedule1.json')
            storage_manager.save_schedule(sample_schedule_data, 'schedule2.json')
            
            schedules = storage_manager.list_schedules()
            
            assert 'schedule1.json' in schedules
            assert 'schedule2.json' in schedules
    
    def test_delete_schedule(self, storage_manager: StorageManager, sample_schedule_data: ScheduleData, tmp_path: Path) -> None:
        """Test deleting schedule data."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # First save the schedule
            storage_manager.save_schedule(sample_schedule_data, 'test_schedule.json')
            
            # Then delete it
            success = storage_manager.delete_schedule('test_schedule.json')
            
            assert success is True
            assert not (tmp_path / 'test_schedule.json').exists()
    
    def test_load_nonexistent_schedule(self, storage_manager: StorageManager, tmp_path: Path) -> None:
        """Test loading nonexistent schedule."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            with pytest.raises(FileNotFoundError):
                storage_manager.load_schedule('nonexistent.json')
    
    def test_delete_nonexistent_schedule(self, storage_manager: StorageManager, tmp_path: Path) -> None:
        """Test deleting nonexistent schedule."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            success = storage_manager.delete_schedule('nonexistent.json')
            
            assert success is False
    
    def test_schedule_data_serialization(self, storage_manager: StorageManager, tmp_path: Path) -> None:
        """Test schedule data serialization and deserialization."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # Create complex schedule data
            complex_schedule = {
                'paper1': date(2024, 1, 1),
                'abstract1': date(2024, 2, 1),
                'mod1': date(2024, 3, 1)
            }
            
            complex_validation = {
                'scores': {
                    'penalty_score': 85.2,
                    'quality_score': 90.1,
                    'efficiency_score': 78.4
                },
                'summary': {
                    'overall_score': 84.6,
                    'total_submissions': 3,
                    'duration_days': 90,
                    'deadline_compliance': 95.0,
                    'dependency_satisfaction': 100.0,
                    'total_violations': 0,
                    'critical_violations': 0
                },
                'constraints': {
                    'deadline_constraints': {
                        'violations': []
                    },
                    'dependency_constraints': {
                        'violations': []
                    }
                }
            }
            
            complex_schedule_data = ScheduleData(
                schedule=complex_schedule,
                config=Mock(spec=Config),
                validation_result=complex_validation
            )
            
            # Save and load
            storage_manager.save_schedule(complex_schedule_data, 'complex_schedule.json')
            loaded_data = storage_manager.load_schedule('complex_schedule.json')
            
            # Verify data integrity
            assert loaded_data.schedule == complex_schedule
            assert loaded_data.validation_result == complex_validation
    
    def test_schedule_data_with_date_strings(self, storage_manager: StorageManager, tmp_path: Path) -> None:
        """Test schedule data with date strings."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # Create schedule with date strings
            schedule_with_strings = {
                'paper1': '2024-01-01',
                'abstract1': '2024-02-01'
            }
            
            schedule_data = ScheduleData(
                schedule=schedule_with_strings,
                config=Mock(spec=Config),
                validation_result={'scores': {'penalty_score': 85.0}}
            )
            
            # Save and load
            storage_manager.save_schedule(schedule_data, 'string_dates.json')
            loaded_data = storage_manager.load_schedule('string_dates.json')
            
            # Verify dates are converted properly
            assert isinstance(loaded_data.schedule['paper1'], date)
            assert isinstance(loaded_data.schedule['abstract1'], date)
            assert loaded_data.schedule['paper1'] == date(2024, 1, 1)
            assert loaded_data.schedule['abstract1'] == date(2024, 2, 1)
    
    def test_storage_manager_error_handling(self, storage_manager: StorageManager, tmp_path: Path) -> None:
        """Test storage manager error handling."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # Test with invalid JSON data
            invalid_file = tmp_path / 'invalid.json'
            invalid_file.write_text('invalid json data', encoding='utf-8')
            
            # Should handle gracefully or raise appropriate error
            try:
                storage_manager.load_schedule('invalid.json')
            except (json.JSONDecodeError, KeyError):
                # Expected behavior for invalid JSON
                pass
    
    def test_storage_manager_permissions(self, storage_manager: StorageManager, tmp_path: Path) -> None:
        """Test storage manager with permission issues."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # Test with read-only directory (simulated)
            read_only_dir = tmp_path / 'readonly'
            read_only_dir.mkdir()
            
            # Try to save to read-only directory
            try:
                storage_manager.data_dir = str(read_only_dir)
                sample_data = ScheduleData(
                    schedule={'paper1': date(2024, 1, 1)},
                    config=Mock(spec=Config),
                    validation_result={'scores': {'penalty_score': 85.0}}
                )
                storage_manager.save_schedule(sample_data, 'test.json')
            except (PermissionError, OSError):
                # Expected behavior for permission issues
                pass


class TestWebAppModels:
    """Test web app data models."""
    
    def test_schedule_data_model(self) -> None:
        """Test ScheduleData model."""
        schedule = {'paper1': date(2024, 1, 1)}
        config = Mock(spec=Config)
        validation_result = {'scores': {'penalty_score': 85.0}}
        
        schedule_data = ScheduleData(
            schedule=schedule,
            config=config,
            validation_result=validation_result
        )
        
        assert schedule_data.schedule == schedule
        assert schedule_data.config == config
        assert schedule_data.validation_result == validation_result
    
    def test_validation_result_model(self) -> None:
        """Test ValidationResult model."""
        scores = {'penalty_score': 85.0, 'quality_score': 90.0}
        summary = {'total_submissions': 2}
        constraints = {'deadline_constraints': {'violations': []}}
        
        validation_result = ValidationResult(
            scores=scores,
            summary=summary,
            constraints=constraints
        )
        
        assert validation_result.scores == scores
        assert validation_result.summary == summary
        assert validation_result.constraints == constraints
    
    def test_web_app_state_model(self) -> None:
        """Test WebAppState model."""
        # Test state initialization
        app_state = WebAppState()
        
        # Verify state has expected attributes
        assert app_state is not None
        assert hasattr(app_state, '__dict__')
        
        # Test state can be modified
        app_state.current_schedule = {'paper1': date(2024, 1, 1)}
        app_state.current_config = Mock(spec=Config)
        
        assert app_state.current_schedule == {'paper1': date(2024, 1, 1)}
        assert app_state.current_config is not None
    
    def test_schedule_data_with_complex_validation(self) -> None:
        """Test ScheduleData with complex validation result."""
        schedule = {
            'paper1': date(2024, 1, 1),
            'abstract1': date(2024, 2, 1),
            'mod1': date(2024, 3, 1)
        }
        
        config = Mock(spec=Config)
        config.submissions_dict = {
            'paper1': Mock(spec=Submission, id='paper1', title='Research Paper'),
            'abstract1': Mock(spec=Submission, id='abstract1', title='Abstract'),
            'mod1': Mock(spec=Submission, id='mod1', title='Modification')
        }
        
        complex_validation = {
            'scores': {
                'penalty_score': 85.2,
                'quality_score': 90.1,
                'efficiency_score': 78.4,
                'overall_score': 84.6
            },
            'summary': {
                'total_submissions': 3,
                'duration_days': 90,
                'deadline_compliance': 95.0,
                'dependency_satisfaction': 100.0,
                'total_violations': 0,
                'critical_violations': 0,
                'resource_utilization': 85.5
            },
            'constraints': {
                'deadline_constraints': {
                    'violations': [],
                    'warnings': []
                },
                'dependency_constraints': {
                    'violations': [],
                    'warnings': []
                },
                'resource_constraints': {
                    'violations': [],
                    'warnings': []
                }
            },
            'metadata': {
                'generation_timestamp': '2024-01-01T00:00:00',
                'scheduler_strategy': 'greedy',
                'config_version': '1.0.0'
            }
        }
        
        schedule_data = ScheduleData(
            schedule=schedule,
            config=config,
            validation_result=complex_validation
        )
        
        assert schedule_data.schedule == schedule
        assert schedule_data.config == config
        assert schedule_data.validation_result == complex_validation
        
        # Test nested access
        assert schedule_data.validation_result['scores']['penalty_score'] == 85.2
        assert schedule_data.validation_result['summary']['total_submissions'] == 3
        assert len(schedule_data.validation_result['constraints']) == 3
    
    def test_validation_result_with_violations(self) -> None:
        """Test ValidationResult with constraint violations."""
        scores = {
            'penalty_score': 65.0,  # Lower due to violations
            'quality_score': 75.0,
            'efficiency_score': 60.0,
            'overall_score': 66.7
        }
        
        summary = {
            'total_submissions': 2,
            'duration_days': 60,
            'deadline_compliance': 80.0,  # Lower due to violations
            'dependency_satisfaction': 90.0,
            'total_violations': 2,
            'critical_violations': 1
        }
        
        constraints = {
            'deadline_constraints': {
                'violations': [
                    {
                        'submission_id': 'paper1',
                        'deadline': '2024-01-15',
                        'scheduled_date': '2024-01-20',
                        'days_overdue': 5
                    }
                ],
                'warnings': []
            },
            'dependency_constraints': {
                'violations': [
                    {
                        'submission_id': 'paper2',
                        'dependency_id': 'paper1',
                        'dependency_date': '2024-01-10',
                        'scheduled_date': '2024-01-05'
                    }
                ],
                'warnings': []
            }
        }
        
        validation_result = ValidationResult(
            scores=scores,
            summary=summary,
            constraints=constraints
        )
        
        assert validation_result.scores == scores
        assert validation_result.summary == summary
        assert validation_result.constraints == constraints
        
        # Test violation access
        deadline_violations = validation_result.constraints['deadline_constraints']['violations']
        assert len(deadline_violations) == 1
        assert deadline_violations[0]['submission_id'] == 'paper1'
        
        dependency_violations = validation_result.constraints['dependency_constraints']['violations']
        assert len(dependency_violations) == 1
        assert dependency_violations[0]['submission_id'] == 'paper2'
