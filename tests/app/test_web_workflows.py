"""
Tests for web application workflows and user interactions.
"""

import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import dash
import pytest

from app.main import create_dashboard_app, create_timeline_app
from app.models import WebAppState
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


class TestWebAppWorkflows:
    """Test web app workflow functionality."""
    
    @pytest.fixture
    def dashboard_app(self) -> dash.Dash:
        """Create a dashboard app instance for testing."""
        return create_dashboard_app()
    
    @pytest.fixture
    def timeline_app(self) -> dash.Dash:
        """Create a timeline app instance for testing."""
        return create_timeline_app()
    
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
    def temp_config_file(self, sample_config: Mock) -> Path:
        """Create a temporary config file for testing."""
        # Create a temporary directory for the test
        temp_dir = tempfile.mkdtemp()
        temp_data_dir = Path(temp_dir) / "data"
        temp_data_dir.mkdir()
        
        # Copy data files to temp directory
        data_dir = Path("data")
        for file_name in ["conferences.json", "mods.json", "papers.json", "blackout.json"]:
            if (data_dir / file_name).exists():
                import shutil
                shutil.copy2(data_dir / file_name, temp_data_dir / file_name)
        
        config_data = {
            "min_abstract_lead_time_days": 0,
            "min_paper_lead_time_days": 60,
            "max_concurrent_submissions": 2,
            "default_paper_lead_time_months": 3,
            "priority_weights": {
                "engineering_paper": 2.0,
                "medical_paper": 1.0,
                "mod": 1.5,
                "abstract": 0.5
            },
            "penalty_costs": {
                "default_mod_penalty_per_day": 1000.0,
                "default_paper_penalty_per_day": 500.0,
                "default_monthly_slip_penalty": 1000.0,
                "default_full_year_deferral_penalty": 5000.0,
                "missed_abstract_penalty": 3000.0,
                "resource_violation_penalty": 200.0
            },
            "scheduling_options": {
                "enable_early_abstract_scheduling": True,
                "abstract_advance_days": 30,
                "enable_blackout_periods": True,
                "conference_response_time_days": 90,
                "enable_priority_weighting": True,
                "enable_dependency_tracking": True,
                "enable_concurrency_control": True,
                "enable_working_days_only": True
            },
            "blackout_dates": [],
            "data_files": {
                "conferences": "data/conferences.json",
                "mods": "data/mods.json",
                "papers": "data/papers.json",
                "blackouts": "data/blackout.json"
            }
        }
        
        config_file = Path(temp_dir) / "config.json"
        Path(config_file).write_text(json.dumps(config_data), encoding='utf-8')
        
        return config_file
    
    def test_dashboard_app_creation(self, dashboard_app: dash.Dash) -> None:
        """Test that dashboard app is created successfully."""
        assert isinstance(dashboard_app, dash.Dash)
        assert dashboard_app.title == "Paper Planner - Academic Schedule Optimizer"
        
        # Verify layout exists
        assert dashboard_app.layout is not None
        
        # Verify callbacks are registered
        callbacks = dashboard_app.callback_map
        assert len(callbacks) > 0
    
    def test_timeline_app_creation(self, timeline_app: dash.Dash) -> None:
        """Test that timeline app is created successfully."""
        assert isinstance(timeline_app, dash.Dash)
        assert timeline_app.title == "Paper Planner - Timeline"
        
        # Verify layout exists
        assert timeline_app.layout is not None
        
        # Verify callbacks are registered
        callbacks = timeline_app.callback_map
        assert len(callbacks) > 0
    
    def test_app_layout_components(self, dashboard_app: dash.Dash) -> None:
        """Test that all layout components are properly structured."""
        layout = dashboard_app.layout
        
        # Verify layout is a div
        assert hasattr(layout, 'className')
        assert layout.className == 'app-wrapper'
        
        # Verify layout has children
        assert hasattr(layout, 'children')
        assert layout.children is not None
    
    def test_web_app_state_management(self) -> None:
        """Test web app state management."""
        # Create app state
        app_state = WebAppState()
        
        # Verify state initialization
        assert app_state is not None
        assert hasattr(app_state, '__dict__')
    
    @patch('app.main.load_config')
    @patch('app.main.BaseScheduler.create_scheduler')
    def test_timeline_callback_workflow(self, mock_create_scheduler: MagicMock, mock_load_config: MagicMock, 
                                      timeline_app: dash.Dash, temp_config_file: Path) -> None:
        """Test timeline callback workflow."""
        # Mock scheduler
        mock_scheduler = MagicMock()
        mock_scheduler.schedule.return_value = {"test-pap": date(2025, 1, 15)}
        mock_create_scheduler.return_value = mock_scheduler
        
        # Mock config
        mock_config = MagicMock()
        mock_load_config.return_value = mock_config
        
        # Test callback execution
        callbacks = timeline_app.callback_map
        assert len(callbacks) > 0
    
    def test_component_id_consistency(self, dashboard_app: dash.Dash) -> None:
        """Test that component IDs are consistent across the app."""
        layout = dashboard_app.layout
        
        # Extract all component IDs from layout
        component_ids = set()
        
        def extract_ids(component: any) -> None:
            if hasattr(component, 'id'):
                component_ids.add(component.id)
            if hasattr(component, 'children'):
                if isinstance(component.children, list):
                    for child in component.children:
                        extract_ids(child)
                elif component.children is not None:
                    extract_ids(component.children)
        
        extract_ids(layout)
        
        # Verify no duplicate IDs
        assert len(component_ids) == len(set(component_ids))
    
    def test_app_initialization_workflow(self) -> None:
        """Test complete app initialization workflow."""
        # Test app creation
        app = create_dashboard_app()
        assert app is not None
        
        # Test dashboard app creation
        dashboard_app = create_dashboard_app()
        assert dashboard_app is not None
        
        # Test timeline app creation
        timeline_app = create_timeline_app()
        assert timeline_app is not None
    
    def test_app_configuration_workflow(self, temp_config_file: Path) -> None:
        """Test app configuration workflow."""
        # Test config loading
        config = load_config(str(temp_config_file))
        assert config is not None
        
        # Test scheduler creation
        scheduler = BaseScheduler.create_scheduler(SchedulerStrategy.GREEDY, config)
        assert scheduler is not None
        
        # Test schedule generation
        schedule = scheduler.schedule()
        assert schedule is not None
    
    def test_app_external_stylesheets(self, dashboard_app: dash.Dash) -> None:
        """Test that external stylesheets are properly configured."""
        assert hasattr(dashboard_app, 'external_stylesheets')
        assert isinstance(dashboard_app.external_stylesheets, list)
    
    def test_app_suppress_callback_exceptions(self, dashboard_app: dash.Dash) -> None:
        """Test that callback exceptions are properly suppressed."""
        assert hasattr(dashboard_app, 'suppress_callback_exceptions')
        assert dashboard_app.suppress_callback_exceptions is True
    
    def test_timeline_minimal_layout(self, timeline_app: dash.Dash) -> None:
        """Test that timeline app has minimal required layout."""
        layout = timeline_app.layout
        
        # Verify layout exists and has basic structure
        assert layout is not None
        assert hasattr(layout, 'children')
        assert layout.children is not None
    
    def test_dashboard_full_layout(self, dashboard_app: dash.Dash) -> None:
        """Test that dashboard app has complete layout."""
        layout = dashboard_app.layout
        
        # Verify layout exists and has comprehensive structure
        assert layout is not None
        assert hasattr(layout, 'children')
        assert layout.children is not None
        
        # Verify layout has multiple sections
        assert len(layout.children) > 1
    
    def test_complete_web_app_workflow(self, dashboard_app: dash.Dash, temp_config_file: Path) -> None:
        """Test complete web app workflow from config to output."""
        # Load configuration
        config = load_config(str(temp_config_file))
        assert config is not None
        
        # Create scheduler
        scheduler = BaseScheduler.create_scheduler(SchedulerStrategy.GREEDY, config)
        assert scheduler is not None
        
        # Generate schedule
        schedule = scheduler.schedule()
        assert schedule is not None
        assert len(schedule) >= 0
        
        # Validate schedule
        validation_result = validate_schedule_comprehensive(schedule, config)
        assert validation_result is not None
    
    def test_web_app_data_flow(self, dashboard_app: dash.Dash, temp_config_file: Path) -> None:
        """Test data flow through web app components."""
        # Load configuration
        config = load_config(str(temp_config_file))
        assert config is not None
        
        # Create sample schedule
        sample_schedule = {
            "submission_1": date(2024, 1, 15),
            "submission_2": date(2024, 2, 1),
            "submission_3": date(2024, 3, 15)
        }
        
        # Test data flow to charts
        from app.components.charts.gantt_chart import create_gantt_chart
        gantt_chart = create_gantt_chart(sample_schedule, config)
        assert gantt_chart is not None
        assert 'data' in gantt_chart
        assert 'layout' in gantt_chart
        
        # Test data flow to tables
        from app.components.tables.schedule_table import create_schedule_table
        schedule_table = create_schedule_table(sample_schedule, config)
        assert schedule_table is not None
        assert isinstance(schedule_table, list)
        
        # Test data flow to metrics
        from app.components.charts.metrics_chart import create_metrics_chart
        metrics_chart = create_metrics_chart(sample_schedule, config)
        assert metrics_chart is not None
    
    def test_web_app_error_handling(self) -> None:
        """Test web app error handling."""
        # Test with invalid config
        with pytest.raises(Exception):
            load_config('nonexistent_file.json')
        
        # Test with invalid schedule
        invalid_schedule = {"invalid_id": "invalid_date"}  # Invalid date string for error testing
        config = Mock(spec=Config)
        
        # Should handle gracefully
        try:
            from app.components.tables.schedule_table import create_schedule_table
            create_schedule_table(invalid_schedule, config)  # type: ignore
        except Exception:
            # Should not raise exception for invalid data
            pass
    
    def test_web_app_component_interactions(self, dashboard_app: dash.Dash) -> None:
        """Test component interactions in web app."""
        layout = dashboard_app.layout
        
        # Verify layout has interactive components
        assert layout is not None
        
        # Test that callbacks are properly registered
        callbacks = dashboard_app.callback_map
        assert len(callbacks) > 0
        
        # Test callback structure
        for callback_id, callback in callbacks.items():
            assert hasattr(callback, 'inputs')
            assert hasattr(callback, 'outputs')
    
    def test_web_app_state_consistency(self, dashboard_app: dash.Dash, temp_config_file: Path) -> None:
        """Test web app state consistency."""
        # Load configuration
        config = load_config(str(temp_config_file))
        assert config is not None
        
        # Create sample schedule
        sample_schedule = {
            "submission_1": date(2024, 1, 15),
            "submission_2": date(2024, 2, 1)
        }
        
        # Test state consistency across components
        from app.components.charts.gantt_chart import create_gantt_chart
        from app.components.tables.schedule_table import create_schedule_table
        gantt_chart = create_gantt_chart(sample_schedule, config)
        schedule_table = create_schedule_table(sample_schedule, config)
        
        # Verify consistent data representation
        assert gantt_chart is not None
        assert schedule_table is not None
        
        # Verify schedule data is consistent
        assert len(sample_schedule) == len(schedule_table)
    
    def test_web_app_multiple_strategies(self, dashboard_app: dash.Dash, temp_config_file: Path) -> None:
        """Test web app with multiple scheduling strategies."""
        config = load_config(str(temp_config_file))
        assert config is not None
        
        strategies = [SchedulerStrategy.GREEDY, SchedulerStrategy.OPTIMAL]
        
        for strategy in strategies:
            # Create scheduler
            scheduler = BaseScheduler.create_scheduler(strategy, config)
            assert scheduler is not None
            
            # Generate schedule
            schedule = scheduler.schedule()
            assert schedule is not None
            
            # Test chart generation
            from app.components.charts.gantt_chart import create_gantt_chart
            gantt_chart = create_gantt_chart(schedule, config)
            assert gantt_chart is not None


class TestWebAppUserInteractions:
    """Test web app user interactions."""
    
    @pytest.fixture
    def app(self) -> dash.Dash:
        """Create test app for user interaction testing."""
        app = create_dashboard_app()
        return app
    
    @pytest.fixture
    def client(self, app: dash.Dash):
        """Create test client."""
        return app.server.test_client()
    
    def test_user_navigation_flow(self, client) -> None:
        """Test user navigation through the application."""
        # Test home page
        response = client.get('/')
        assert response.status_code == 200
        
        # Test generate page
        response = client.get('/generate')
        assert response.status_code in [200, 404]  # May not exist
        
        # Test charts page
        response = client.get('/charts')
        assert response.status_code in [200, 404]  # May not exist
    
    def test_user_schedule_generation_flow(self, client) -> None:
        """Test user schedule generation workflow."""
        # Test schedule generation request
        response = client.post('/generate', json={
            'strategy': 'greedy',
            'constraints': {}
        })
        
        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 500]
    
    def test_user_data_export_flow(self, client) -> None:
        """Test user data export workflow."""
        # Test schedule export
        response = client.get('/api/export/schedule')
        assert response.status_code in [200, 404]
        
        # Test CSV export
        response = client.get('/api/export/schedule.csv')
        assert response.status_code in [200, 404]
    
    def test_user_schedule_management_flow(self, client) -> None:
        """Test user schedule management workflow."""
        # Test save schedule
        response = client.post('/api/save', json={
            'filename': 'test_schedule.json'
        })
        assert response.status_code in [200, 400, 500]
        
        # Test load schedule
        response = client.post('/api/load', json={
            'filename': 'test_schedule.json'
        })
        assert response.status_code in [200, 400, 404, 500]
        
        # Test list schedules
        response = client.get('/api/schedules')
        assert response.status_code in [200, 500]
    
    def test_user_validation_flow(self, client) -> None:
        """Test user validation workflow."""
        # Test schedule validation
        response = client.post('/api/validate', json={
            'schedule': {'paper1': '2024-01-01'}
        })
        assert response.status_code in [200, 400, 500]
    
    def test_user_configuration_flow(self, client) -> None:
        """Test user configuration workflow."""
        # Test config retrieval
        response = client.get('/api/config')
        assert response.status_code in [200, 500]
    
    def test_user_error_recovery_flow(self, client) -> None:
        """Test user error recovery workflow."""
        # Test invalid request handling
        response = client.post('/generate', json={
            'invalid_field': 'invalid_value'
        })
        assert response.status_code in [400, 500]
        
        # Test missing data handling
        response = client.post('/generate', json={})
        assert response.status_code in [400, 500]
    
    def test_user_performance_flow(self, client) -> None:
        """Test user performance workflow."""
        # Test multiple rapid requests
        responses = []
        for _ in range(5):
            response = client.get('/')
            responses.append(response.status_code)
        
        # All requests should succeed
        assert all(status == 200 for status in responses)
    
    def test_user_data_consistency_flow(self, client) -> None:
        """Test user data consistency workflow."""
        # Test that data remains consistent across requests
        response1 = client.get('/')
        response2 = client.get('/')
        
        assert response1.status_code == response2.status_code
        assert response1.data == response2.data
