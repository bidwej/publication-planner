"""
Tests for web application endpoints and API functionality.
"""

import json
import tempfile
import threading
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import dash
import pytest

from app.main import create_dashboard_app, create_timeline_app
from app.models import WebAppState
from app.storage import ScheduleStorage
from core.config import load_config
from core.constraints import validate_schedule_comprehensive
from core.models import Config, Conference, SchedulerStrategy, Submission, SubmissionType
from schedulers.base import BaseScheduler


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
        file_path = Path(self.data_dir) / filename
        Path(file_path).write_text(json.dumps({
            'schedule': schedule_data.schedule,
            'config': str(schedule_data.config),
            'validation_result': schedule_data.validation_result
        }), encoding='utf-8')
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


class TestWebAppEndpoints:
    """Integration tests for web application endpoints."""
    
    @pytest.fixture
    def app(self) -> dash.Dash:
        """Create test app instance."""
        app = create_dashboard_app()
        return app
    
    @pytest.fixture
    def client(self, app: dash.Dash):
        """Create test client."""
        return app.server.test_client()
    
    @pytest.fixture
    def sample_config(self) -> Mock:
        """Create sample configuration for testing."""
        config = Mock(spec=Config)
        config.submissions_dict = {
            'paper1': Mock(spec=Submission,
                          id='paper1',
                          title='Research Paper',
                          kind=SubmissionType.PAPER,
                          engineering=True,
                          conference_id='conf1',
                          get_duration_days=lambda cfg: 60),
            'abstract1': Mock(spec=Submission,
                             id='abstract1',
                             title='Conference Abstract',
                             kind=SubmissionType.ABSTRACT,
                             engineering=False,
                             conference_id='conf2',
                             get_duration_days=lambda cfg: 0)
        }
        config.conferences_dict = {
            'conf1': Mock(spec=Conference, name='IEEE Conference'),
            'conf2': Mock(spec=Conference, name='ACM Conference')
        }
        return config
    
    @pytest.fixture
    def sample_schedule_data(self, sample_config: Mock) -> ScheduleData:
        """Create sample schedule data."""
        return ScheduleData(
            schedule={
                'paper1': date(2024, 1, 1),
                'abstract1': date(2024, 2, 1)
            },
            config=sample_config,
            validation_result={
                'scores': {
                    'penalty_score': 85.2,
                    'quality_score': 90.1,
                    'efficiency_score': 78.4
                },
                'summary': {
                    'overall_score': 84.6,
                    'total_submissions': 2,
                    'duration_days': 60,
                    'deadline_compliance': 95.0,
                    'dependency_satisfaction': 100.0,
                    'total_violations': 0,
                    'critical_violations': 0
                },
                'constraints': {
                    'deadline_constraints': {
                        'violations': []
                    }
                }
            }
        )
    
    def test_home_page_loads(self, client) -> None:
        """Test that home page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Paper Planner' in response.data
    
    def test_schedule_generation_endpoint(self, client, sample_config: Mock) -> None:
        """Test schedule generation endpoint."""
        with patch('app.main.load_config', return_value=sample_config):
            with patch('app.main.generate_schedule') as mock_generate:
                mock_generate.return_value = {
                    'schedule': {'paper1': date(2024, 1, 1)},
                    'validation_result': {'scores': {'penalty_score': 85.0}}
                }
                
                response = client.post('/generate', json={
                    'strategy': 'optimal',
                    'constraints': {}
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'schedule' in data
                assert 'validation_result' in data
    
    def test_schedule_generation_with_invalid_data(self, client) -> None:
        """Test schedule generation with invalid input data."""
        response = client.post('/generate', json={
            'strategy': 'invalid_strategy',
            'constraints': {}
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_schedule_generation_without_config(self, client) -> None:
        """Test schedule generation when config is not available."""
        with patch('app.main.load_config', side_effect=FileNotFoundError):
            response = client.post('/generate', json={
                'strategy': 'optimal',
                'constraints': {}
            })
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
    
    def test_chart_generation_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test chart generation endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/charts/gantt')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'chart_data' in data
    
    def test_chart_generation_without_schedule(self, client) -> None:
        """Test chart generation when no schedule is available."""
        with patch('app.main.get_current_schedule_data', return_value=None):
            response = client.get('/api/charts/gantt')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_metrics_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test metrics endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/metrics')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'scores' in data
            assert 'summary' in data
    
    def test_table_data_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test table data endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/tables/schedule')
            
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) > 0
    
    def test_export_schedule_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test schedule export endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/export/schedule')
            
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'application/json'
            data = response.get_json()
            assert 'schedule' in data
    
    def test_export_schedule_csv_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test schedule export as CSV endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/export/schedule.csv')
            
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'text/csv'
            assert b'ID,Title,Type' in response.data
    
    def test_save_schedule_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test save schedule endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            with patch('app.storage.StorageManager.save_schedule') as mock_save:
                mock_save.return_value = 'schedule_2024_01_01.json'
                
                response = client.post('/api/save', json={
                    'filename': 'test_schedule.json'
                })
                
                assert response.status_code == 200
                data = response.get_json()
                assert 'filename' in data
    
    def test_load_schedule_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test load schedule endpoint."""
        with patch('app.storage.StorageManager.load_schedule', return_value=sample_schedule_data):
            response = client.post('/api/load', json={
                'filename': 'test_schedule.json'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'schedule' in data
    
    def test_load_schedule_file_not_found(self, client) -> None:
        """Test load schedule when file is not found."""
        with patch('app.storage.StorageManager.load_schedule', side_effect=FileNotFoundError):
            response = client.post('/api/load', json={
                'filename': 'nonexistent.json'
            })
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_list_saved_schedules_endpoint(self, client) -> None:
        """Test list saved schedules endpoint."""
        with patch('app.storage.StorageManager.list_schedules', return_value=[
            'schedule_2024_01_01.json',
            'schedule_2024_02_01.json'
        ]):
            response = client.get('/api/schedules')
            
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) == 2
    
    def test_delete_schedule_endpoint(self, client) -> None:
        """Test delete schedule endpoint."""
        with patch('app.storage.StorageManager.delete_schedule') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete('/api/schedules/test_schedule.json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'success' in data
    
    def test_validation_endpoint(self, client, sample_schedule_data: ScheduleData) -> None:
        """Test validation endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.post('/api/validate', json={
                'schedule': {'paper1': '2024-01-01'}
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'validation_result' in data
    
    def test_config_endpoint(self, client, sample_config: Mock) -> None:
        """Test config endpoint."""
        with patch('app.main.load_config', return_value=sample_config):
            response = client.get('/api/config')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'submissions' in data
            assert 'conferences' in data
    
    def test_error_handling_404(self, client) -> None:
        """Test 404 error handling."""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
    
    def test_error_handling_500(self, client) -> None:
        """Test 500 error handling."""
        with patch('app.main.load_config', side_effect=Exception('Test error')):
            response = client.get('/api/config')
            assert response.status_code == 500
    
    def test_cors_headers(self, client) -> None:
        """Test CORS headers are present."""
        response = client.get('/')
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_static_files_served(self, client) -> None:
        """Test that static files are served correctly."""
        response = client.get('/static/css/style.css')
        # Should either return 200 (if file exists) or 404 (if not)
        assert response.status_code in [200, 404]


class TestWebAppErrorHandling:
    """Test web app error handling."""
    
    @pytest.fixture
    def app(self) -> dash.Dash:
        """Create test app with error handling."""
        app = create_dashboard_app()
        return app
    
    @pytest.fixture
    def client(self, app: dash.Dash):
        """Create test client."""
        return app.server.test_client()
    
    def test_invalid_json_request(self, client) -> None:
        """Test handling of invalid JSON requests."""
        response = client.post('/generate', 
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_missing_required_fields(self, client) -> None:
        """Test handling of missing required fields."""
        response = client.post('/generate', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_date_format(self, client) -> None:
        """Test handling of invalid date formats."""
        response = client.post('/api/validate', json={
            'schedule': {'paper1': 'invalid-date'}
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_large_file_upload(self, client) -> None:
        """Test handling of large file uploads."""
        large_data = {'data': 'x' * 1000000}  # 1MB of data
        
        response = client.post('/api/save', json=large_data)
        
        # Should either handle gracefully or return appropriate error
        assert response.status_code in [200, 400, 413]
    
    def test_concurrent_requests(self, client) -> None:
        """Test handling of concurrent requests."""
        results: list[int] = []
        
        def make_request() -> None:
            response = client.get('/')
            results.append(response.status_code)
        
        threads = [threading.Thread(target=make_request) for _ in range(5)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        assert all(status == 200 for status in results)
        assert len(results) == 5
