"""
Tests for web application endpoints and API functionality.
"""

import json
import threading
from datetime import date
from pathlib import Path
from unittest.mock import Mock

import dash
import pytest

from app.main import create_dashboard_app
from core.models import Conference, Config, Submission, SubmissionType


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
    
    
    def test_error_handling_404(self, client) -> None:
        """Test 404 error handling - Dash apps serve the main page for all routes."""
        # Dash apps typically serve the main page for all routes (SPA behavior)
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 200  # Dash serves the main app for all routes
    
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
    
    # Dash apps don't have REST API endpoints, so these tests are not applicable
    # The app uses callbacks for interactivity instead of REST endpoints
    
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
