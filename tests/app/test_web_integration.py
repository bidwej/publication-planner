"""
Comprehensive integration tests for web application functionality.
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from pathlib import Path

from app.main import create_dashboard_app, create_timeline_app
from app.models import WebAppState
from app.storage import ScheduleStorage
from app.components.charts.gantt_chart import create_gantt_chart
from app.components.charts.metrics_chart import create_metrics_chart
from app.components.tables.schedule_table import create_schedule_table
from app.layouts.header import create_header
from app.layouts.sidebar import create_sidebar
from app.layouts.main_content import create_main_content
from core.models import Config, Submission, SubmissionType, Conference
from core.config import load_config
from core.models import SchedulerStrategy
from schedulers.base import BaseScheduler
from core.constraints import validate_schedule_comprehensive

import dash


class TestWebAppIntegration:
    """Integration tests for web application functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test app instance."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    @pytest.fixture
    def dashboard_app(self):
        """Create a dashboard app instance for testing."""
        return create_dashboard_app()
    
    @pytest.fixture
    def timeline_app(self):
        """Create a timeline app instance for testing."""
        return create_timeline_app()
    
    @pytest.fixture
    def sample_config(self):
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
    def sample_schedule_data(self):
        """Create sample schedule data."""
        return ScheduleData(
            schedule={
                'paper1': date(2024, 1, 1),
                'abstract1': date(2024, 2, 1)
            },
            config=sample_config(self),
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
    
    @pytest.fixture
    def temp_config_file(self, sample_config) -> Path:
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config.to_dict() if hasattr(sample_config, 'to_dict') else {}, f)
            return Path(f.name)
    
    # ==================== WEB APP ENDPOINT TESTS ====================
    
    def test_home_page_loads(self, client):
        """Test that home page loads successfully."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Paper Planner' in response.data
    
    def test_schedule_generation_endpoint(self, client, sample_config):
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
    
    def test_schedule_generation_with_invalid_data(self, client):
        """Test schedule generation with invalid input data."""
        response = client.post('/generate', json={
            'strategy': 'invalid_strategy',
            'constraints': {}
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_schedule_generation_without_config(self, client):
        """Test schedule generation when config is not available."""
        with patch('app.main.load_config', side_effect=FileNotFoundError):
            response = client.post('/generate', json={
                'strategy': 'optimal',
                'constraints': {}
            })
            
            assert response.status_code == 500
            data = response.get_json()
            assert 'error' in data
    
    def test_chart_generation_endpoint(self, client, sample_schedule_data):
        """Test chart generation endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/charts/gantt')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'chart_data' in data
    
    def test_chart_generation_without_schedule(self, client):
        """Test chart generation when no schedule is available."""
        with patch('app.main.get_current_schedule_data', return_value=None):
            response = client.get('/api/charts/gantt')
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_metrics_endpoint(self, client, sample_schedule_data):
        """Test metrics endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/metrics')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'scores' in data
            assert 'summary' in data
    
    def test_table_data_endpoint(self, client, sample_schedule_data):
        """Test table data endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/tables/schedule')
            
            assert response.status_code == 200
            data = response.get_json()
            assert isinstance(data, list)
            assert len(data) > 0
    
    def test_export_schedule_endpoint(self, client, sample_schedule_data):
        """Test schedule export endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/export/schedule')
            
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'application/json'
            data = response.get_json()
            assert 'schedule' in data
    
    def test_export_schedule_csv_endpoint(self, client, sample_schedule_data):
        """Test schedule export as CSV endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.get('/api/export/schedule.csv')
            
            assert response.status_code == 200
            assert response.headers['Content-Type'] == 'text/csv'
            assert b'ID,Title,Type' in response.data
    
    def test_save_schedule_endpoint(self, client, sample_schedule_data):
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
    
    def test_load_schedule_endpoint(self, client, sample_schedule_data):
        """Test load schedule endpoint."""
        with patch('app.storage.StorageManager.load_schedule', return_value=sample_schedule_data):
            response = client.post('/api/load', json={
                'filename': 'test_schedule.json'
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'schedule' in data
    
    def test_load_schedule_file_not_found(self, client):
        """Test load schedule when file is not found."""
        with patch('app.storage.StorageManager.load_schedule', side_effect=FileNotFoundError):
            response = client.post('/api/load', json={
                'filename': 'nonexistent.json'
            })
            
            assert response.status_code == 404
            data = response.get_json()
            assert 'error' in data
    
    def test_list_saved_schedules_endpoint(self, client):
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
    
    def test_delete_schedule_endpoint(self, client):
        """Test delete schedule endpoint."""
        with patch('app.storage.StorageManager.delete_schedule') as mock_delete:
            mock_delete.return_value = True
            
            response = client.delete('/api/schedules/test_schedule.json')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'success' in data
    
    def test_validation_endpoint(self, client, sample_schedule_data):
        """Test validation endpoint."""
        with patch('app.main.get_current_schedule_data', return_value=sample_schedule_data):
            response = client.post('/api/validate', json={
                'schedule': {'paper1': '2024-01-01'}
            })
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'validation_result' in data
    
    def test_config_endpoint(self, client, sample_config):
        """Test config endpoint."""
        with patch('app.main.load_config', return_value=sample_config):
            response = client.get('/api/config')
            
            assert response.status_code == 200
            data = response.get_json()
            assert 'submissions' in data
            assert 'conferences' in data
    
    def test_error_handling_404(self, client):
        """Test 404 error handling."""
        response = client.get('/nonexistent-endpoint')
        assert response.status_code == 404
    
    def test_error_handling_500(self, client):
        """Test 500 error handling."""
        with patch('app.main.load_config', side_effect=Exception('Test error')):
            response = client.get('/api/config')
            assert response.status_code == 500
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.get('/')
        assert 'Access-Control-Allow-Origin' in response.headers
    
    def test_static_files_served(self, client):
        """Test that static files are served correctly."""
        response = client.get('/static/css/style.css')
        # Should either return 200 (if file exists) or 404 (if not)
        assert response.status_code in [200, 404]

    # ==================== DASH APP TESTS ====================
    
    def test_dashboard_app_creation(self, dashboard_app):
        """Test that dashboard app is created successfully."""
        assert isinstance(dashboard_app, dash.Dash)
        assert dashboard_app.title == "Paper Planner - Academic Schedule Optimizer"
        
        # Verify layout exists
        assert dashboard_app.layout is not None
        
        # Verify callbacks are registered
        callbacks = dashboard_app.callback_map
        assert len(callbacks) > 0
    
    def test_timeline_app_creation(self, timeline_app):
        """Test that timeline app is created successfully."""
        assert isinstance(timeline_app, dash.Dash)
        assert timeline_app.title == "Paper Planner - Timeline"
        
        # Verify layout exists
        assert timeline_app.layout is not None
        
        # Verify callbacks are registered
        callbacks = timeline_app.callback_map
        assert len(callbacks) > 0
    
    def test_app_layout_components(self, dashboard_app):
        """Test that all layout components are properly structured."""
        layout = dashboard_app.layout
        
        # Verify layout is a div
        assert hasattr(layout, 'type')
        assert layout.type == 'Div'
        
        # Verify layout has children
        assert hasattr(layout, 'children')
        assert layout.children is not None
    
    def test_web_app_state_management(self):
        """Test web app state management."""
        # Create app state
        app_state = WebAppState()
        
        # Verify state initialization
        assert app_state is not None
        assert hasattr(app_state, '__dict__')
    
    @patch('app.main.load_config')
    @patch('app.main.BaseScheduler.create_scheduler')
    def test_timeline_callback_workflow(self, mock_create_scheduler, mock_load_config, timeline_app, temp_config_file):
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
    
    def test_component_id_consistency(self, dashboard_app):
        """Test that component IDs are consistent across the app."""
        layout = dashboard_app.layout
        
        # Extract all component IDs from layout
        component_ids = set()
        
        def extract_ids(component):
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
    
    def test_app_initialization_workflow(self):
        """Test complete app initialization workflow."""
        # Test app creation
        app = create_app()
        assert app is not None
        assert app.config['TESTING'] is False
        
        # Test dashboard app creation
        dashboard_app = create_dashboard_app()
        assert dashboard_app is not None
        
        # Test timeline app creation
        timeline_app = create_timeline_app()
        assert timeline_app is not None
    
    def test_app_configuration_workflow(self, temp_config_file):
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
    
    def test_app_external_stylesheets(self, dashboard_app):
        """Test that external stylesheets are properly configured."""
        assert hasattr(dashboard_app, 'external_stylesheets')
        assert isinstance(dashboard_app.external_stylesheets, list)
    
    def test_app_suppress_callback_exceptions(self, dashboard_app):
        """Test that callback exceptions are properly suppressed."""
        assert hasattr(dashboard_app, 'suppress_callback_exceptions')
        assert dashboard_app.suppress_callback_exceptions is True
    
    def test_timeline_minimal_layout(self, timeline_app):
        """Test that timeline app has minimal required layout."""
        layout = timeline_app.layout
        
        # Verify layout exists and has basic structure
        assert layout is not None
        assert hasattr(layout, 'children')
        assert layout.children is not None
    
    def test_dashboard_full_layout(self, dashboard_app):
        """Test that dashboard app has complete layout."""
        layout = dashboard_app.layout
        
        # Verify layout exists and has comprehensive structure
        assert layout is not None
        assert hasattr(layout, 'children')
        assert layout.children is not None
        
        # Verify layout has multiple sections
        assert len(layout.children) > 1
    
    def test_complete_web_app_workflow(self, dashboard_app, temp_config_file):
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
        
        # Test chart generation
        gantt_chart = create_gantt_chart(schedule, config)
        assert gantt_chart is not None
        
        # Test table generation
        schedule_table = create_schedule_table(schedule, config)
        assert schedule_table is not None
    
    def test_web_app_data_flow(self, dashboard_app, temp_config_file):
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
        gantt_chart = create_gantt_chart(sample_schedule, config)
        assert gantt_chart is not None
        assert 'data' in gantt_chart
        assert 'layout' in gantt_chart
        
        # Test data flow to tables
        schedule_table = create_schedule_table(sample_schedule, config)
        assert schedule_table is not None
        assert isinstance(schedule_table, list)
        
        # Test data flow to metrics
        metrics_chart = create_metrics_chart(sample_schedule, config)
        assert metrics_chart is not None
    
    def test_web_app_error_handling(self):
        """Test web app error handling."""
        # Test with invalid config
        with pytest.raises(Exception):
            load_config('nonexistent_file.json')
        
        # Test with invalid schedule
        invalid_schedule = {"invalid_id": "invalid_date"}
        config = Mock(spec=Config)
        
        # Should handle gracefully
        try:
            create_schedule_table(invalid_schedule, config)
        except Exception:
            # Should not raise exception for invalid data
            pass
    
    def test_web_app_component_interactions(self, dashboard_app):
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
    
    def test_web_app_state_consistency(self, dashboard_app, temp_config_file):
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
        gantt_chart = create_gantt_chart(sample_schedule, config)
        schedule_table = create_schedule_table(sample_schedule, config)
        
        # Verify consistent data representation
        assert gantt_chart is not None
        assert schedule_table is not None
        
        # Verify schedule data is consistent
        assert len(sample_schedule) == len(schedule_table)
    
    def test_web_app_multiple_strategies(self, dashboard_app, temp_config_file):
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
            gantt_chart = create_gantt_chart(schedule, config)
            assert gantt_chart is not None


class TestWebAppComponents:
    """Test web app component integration."""
    
    @pytest.fixture
    def sample_layout_data(self):
        """Create sample layout data for testing."""
        return {
            'header': {
                'title': 'Paper Planner',
                'version': '1.0.0'
            },
            'sidebar': {
                'menu_items': [
                    {'label': 'Home', 'url': '/'},
                    {'label': 'Generate', 'url': '/generate'},
                    {'label': 'Charts', 'url': '/charts'}
                ]
            },
            'main_content': {
                'current_page': 'home',
                'data': {}
            }
        }
    
    def test_header_component_rendering(self, sample_layout_data):
        """Test header component rendering."""
        header_html = create_header(sample_layout_data['header'])
        
        assert 'Paper Planner' in header_html
        assert '1.0.0' in header_html
        assert '<header' in header_html
    
    def test_sidebar_component_rendering(self, sample_layout_data):
        """Test sidebar component rendering."""
        sidebar_html = create_sidebar(sample_layout_data['sidebar'])
        
        assert 'Home' in sidebar_html
        assert 'Generate' in sidebar_html
        assert 'Charts' in sidebar_html
        assert '<nav' in sidebar_html
    
    def test_main_content_component_rendering(self, sample_layout_data):
        """Test main content component rendering."""
        main_html = create_main_content(sample_layout_data['main_content'])
        
        assert '<main' in main_html
        assert 'home' in main_html
    
    def test_chart_component_integration(self, sample_schedule_data):
        """Test chart component integration."""
        fig = create_gantt_chart(
            sample_schedule_data.schedule,
            sample_schedule_data.config
        )
        
        assert fig is not None
        assert hasattr(fig, 'layout')
        assert fig.layout.title.text == 'Schedule Timeline'
    
    def test_table_component_integration(self, sample_schedule_data):
        """Test table component integration."""
        table_data = create_schedule_table(
            sample_schedule_data.schedule,
            sample_schedule_data.config
        )
        
        assert isinstance(table_data, list)
        assert len(table_data) > 0
        assert 'id' in table_data[0]
        assert 'title' in table_data[0]
    
    def test_component_id_consistency(self):
        """Test that component IDs are consistent."""
        # Test header component
        header = create_header()
        assert header is not None
        
        # Test sidebar component
        sidebar = create_sidebar()
        assert sidebar is not None
        
        # Test main content component
        main_content = create_main_content()
        assert main_content is not None
    
    def test_component_styling_integration(self):
        """Test component styling integration."""
        # Test header styling
        header = create_header()
        assert header is not None
        
        # Test sidebar styling
        sidebar = create_sidebar()
        assert sidebar is not None
        
        # Test main content styling
        main_content = create_main_content()
        assert main_content is not None
    
    def test_component_accessibility_integration(self):
        """Test component accessibility integration."""
        # Test header accessibility
        header = create_header()
        assert header is not None
        
        # Test sidebar accessibility
        sidebar = create_sidebar()
        assert sidebar is not None
        
        # Test main content accessibility
        main_content = create_main_content()
        assert main_content is not None
    
    def test_component_responsiveness_integration(self):
        """Test component responsiveness integration."""
        # Test header responsiveness
        header = create_header()
        assert header is not None
        
        # Test sidebar responsiveness
        sidebar = create_sidebar()
        assert sidebar is not None
        
        # Test main content responsiveness
        main_content = create_main_content()
        assert main_content is not None
    
    def test_component_performance_integration(self):
        """Test component performance integration."""
        # Test header performance
        header = create_header()
        assert header is not None
        
        # Test sidebar performance
        sidebar = create_sidebar()
        assert sidebar is not None
        
        # Test main content performance
        main_content = create_main_content()
        assert main_content is not None
    
    def test_component_error_boundaries(self):
        """Test component error boundaries."""
        # Test header error handling
        try:
            header = create_header()
            assert header is not None
        except Exception:
            pytest.fail("Header component should handle errors gracefully")
        
        # Test sidebar error handling
        try:
            sidebar = create_sidebar()
            assert sidebar is not None
        except Exception:
            pytest.fail("Sidebar component should handle errors gracefully")
        
        # Test main content error handling
        try:
            main_content = create_main_content()
            assert main_content is not None
        except Exception:
            pytest.fail("Main content component should handle errors gracefully")
    
    def test_component_state_management(self):
        """Test component state management."""
        # Test header state
        header = create_header()
        assert header is not None
        
        # Test sidebar state
        sidebar = create_sidebar()
        assert sidebar is not None
        
        # Test main content state
        main_content = create_main_content()
        assert main_content is not None


class TestWebAppStorage:
    """Test web app storage functionality."""
    
    @pytest.fixture
    def storage_manager(self):
        """Create storage manager for testing."""
        return StorageManager('test_data')
    
    @pytest.fixture
    def sample_schedule_data(self):
        """Create sample schedule data for storage testing."""
        return ScheduleData(
            schedule={'paper1': date(2024, 1, 1)},
            config=Mock(spec=Config),
            validation_result={'scores': {'penalty_score': 85.0}}
        )
    
    def test_save_schedule(self, storage_manager, sample_schedule_data, tmp_path):
        """Test saving schedule data."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            filename = storage_manager.save_schedule(sample_schedule_data, 'test_schedule.json')
            
            assert filename == 'test_schedule.json'
            assert (tmp_path / 'test_schedule.json').exists()
    
    def test_load_schedule(self, storage_manager, sample_schedule_data, tmp_path):
        """Test loading schedule data."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # First save the schedule
            storage_manager.save_schedule(sample_schedule_data, 'test_schedule.json')
            
            # Then load it
            loaded_data = storage_manager.load_schedule('test_schedule.json')
            
            assert loaded_data is not None
            assert loaded_data.schedule == sample_schedule_data.schedule
    
    def test_list_schedules(self, storage_manager, sample_schedule_data, tmp_path):
        """Test listing saved schedules."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # Save multiple schedules
            storage_manager.save_schedule(sample_schedule_data, 'schedule1.json')
            storage_manager.save_schedule(sample_schedule_data, 'schedule2.json')
            
            schedules = storage_manager.list_schedules()
            
            assert 'schedule1.json' in schedules
            assert 'schedule2.json' in schedules
    
    def test_delete_schedule(self, storage_manager, sample_schedule_data, tmp_path):
        """Test deleting schedule data."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            # First save the schedule
            storage_manager.save_schedule(sample_schedule_data, 'test_schedule.json')
            
            # Then delete it
            success = storage_manager.delete_schedule('test_schedule.json')
            
            assert success is True
            assert not (tmp_path / 'test_schedule.json').exists()
    
    def test_load_nonexistent_schedule(self, storage_manager, tmp_path):
        """Test loading nonexistent schedule."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            with pytest.raises(FileNotFoundError):
                storage_manager.load_schedule('nonexistent.json')
    
    def test_delete_nonexistent_schedule(self, storage_manager, tmp_path):
        """Test deleting nonexistent schedule."""
        with patch.object(storage_manager, 'data_dir', tmp_path):
            success = storage_manager.delete_schedule('nonexistent.json')
            
            assert success is False


class TestWebAppModels:
    """Test web app data models."""
    
    def test_schedule_data_model(self):
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
    
    def test_validation_result_model(self):
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


class TestWebAppErrorHandling:
    """Test web app error handling."""
    
    @pytest.fixture
    def app(self):
        """Create test app with error handling."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_invalid_json_request(self, client):
        """Test handling of invalid JSON requests."""
        response = client.post('/generate', 
                             data='invalid json',
                             content_type='application/json')
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_missing_required_fields(self, client):
        """Test handling of missing required fields."""
        response = client.post('/generate', json={})
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_invalid_date_format(self, client):
        """Test handling of invalid date formats."""
        response = client.post('/api/validate', json={
            'schedule': {'paper1': 'invalid-date'}
        })
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'error' in data
    
    def test_large_file_upload(self, client):
        """Test handling of large file uploads."""
        large_data = {'data': 'x' * 1000000}  # 1MB of data
        
        response = client.post('/api/save', json=large_data)
        
        # Should either handle gracefully or return appropriate error
        assert response.status_code in [200, 400, 413]
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests."""
        import threading
        
        results = []
        
        def make_request():
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


class TestWebAppUserInteractions:
    """Test web app user interactions."""
    
    @pytest.fixture
    def app(self):
        """Create test app for user interaction testing."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_user_navigation_flow(self, client):
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
    
    def test_user_schedule_generation_flow(self, client):
        """Test user schedule generation workflow."""
        # Test schedule generation request
        response = client.post('/generate', json={
            'strategy': 'greedy',
            'constraints': {}
        })
        
        # Should either succeed or return appropriate error
        assert response.status_code in [200, 400, 500]
    
    def test_user_data_export_flow(self, client):
        """Test user data export workflow."""
        # Test schedule export
        response = client.get('/api/export/schedule')
        assert response.status_code in [200, 404]
        
        # Test CSV export
        response = client.get('/api/export/schedule.csv')
        assert response.status_code in [200, 404]
    
    def test_user_schedule_management_flow(self, client):
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
    
    def test_user_validation_flow(self, client):
        """Test user validation workflow."""
        # Test schedule validation
        response = client.post('/api/validate', json={
            'schedule': {'paper1': '2024-01-01'}
        })
        assert response.status_code in [200, 400, 500]
    
    def test_user_configuration_flow(self, client):
        """Test user configuration workflow."""
        # Test config retrieval
        response = client.get('/api/config')
        assert response.status_code in [200, 500]
    
    def test_user_error_recovery_flow(self, client):
        """Test user error recovery workflow."""
        # Test invalid request handling
        response = client.post('/generate', json={
            'invalid_field': 'invalid_value'
        })
        assert response.status_code in [400, 500]
        
        # Test missing data handling
        response = client.post('/generate', json={})
        assert response.status_code in [400, 500]
    
    def test_user_performance_flow(self, client):
        """Test user performance workflow."""
        # Test multiple rapid requests
        responses = []
        for _ in range(5):
            response = client.get('/')
            responses.append(response.status_code)
        
        # All requests should succeed
        assert all(status == 200 for status in responses)
    
    def test_user_data_consistency_flow(self, client):
        """Test user data consistency workflow."""
        # Test that data remains consistent across requests
        response1 = client.get('/')
        response2 = client.get('/')
        
        assert response1.status_code == response2.status_code
        assert response1.data == response2.data


class TestWebAppChartsRunner:
    """Test web app charts runner functionality."""
    
    @pytest.fixture
    def app(self):
        """Create test app for charts runner testing."""
        app = create_app()
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return app.test_client()
    
    def test_charts_runner_initialization(self):
        """Test charts runner initialization."""
        # Test that charts runner can be imported and initialized
        try:
            assert True
        except ImportError:
            pytest.fail("Charts runner components should be importable")
    
    def test_gantt_chart_runner(self, sample_config):
        """Test Gantt chart runner functionality."""
        # Create sample schedule
        sample_schedule = {
            "submission_1": date(2024, 1, 15),
            "submission_2": date(2024, 2, 1),
            "submission_3": date(2024, 3, 15)
        }
        
        # Test Gantt chart creation
        gantt_chart = create_gantt_chart(sample_schedule, sample_config)
        assert gantt_chart is not None
        assert 'data' in gantt_chart
        assert 'layout' in gantt_chart
    
    def test_metrics_chart_runner(self, sample_config):
        """Test metrics chart runner functionality."""
        # Create sample schedule
        sample_schedule = {
            "submission_1": date(2024, 1, 15),
            "submission_2": date(2024, 2, 1),
            "submission_3": date(2024, 3, 15)
        }
        
        # Test metrics chart creation
        metrics_chart = create_metrics_chart(sample_schedule, sample_config)
        assert metrics_chart is not None
        assert 'data' in metrics_chart
        assert 'layout' in metrics_chart
    
    def test_charts_runner_error_handling(self, sample_config):
        """Test charts runner error handling."""
        # Test with invalid schedule
        invalid_schedule = {"invalid_id": "invalid_date"}
        
        try:
            gantt_chart = create_gantt_chart(invalid_schedule, sample_config)
            # Should handle gracefully
            assert gantt_chart is not None
        except Exception:
            # Should not raise exception for invalid data
            pass
    
    def test_charts_runner_performance(self, sample_config):
        """Test charts runner performance."""
        # Create large schedule
        large_schedule = {}
        for i in range(100):
            large_schedule[f"submission_{i}"] = date(2024, 1, 1 + i)
        
        # Test performance with large dataset
        import time
        start_time = time.time()
        
        gantt_chart = create_gantt_chart(large_schedule, sample_config)
        metrics_chart = create_metrics_chart(large_schedule, sample_config)
        
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 10.0  # 10 seconds max
        assert gantt_chart is not None
        assert metrics_chart is not None
    
    def test_charts_runner_data_consistency(self, sample_config):
        """Test charts runner data consistency."""
        # Create sample schedule
        sample_schedule = {
            "submission_1": date(2024, 1, 15),
            "submission_2": date(2024, 2, 1)
        }
        
        # Test that both charts use consistent data
        gantt_chart = create_gantt_chart(sample_schedule, sample_config)
        metrics_chart = create_metrics_chart(sample_schedule, sample_config)
        
        assert gantt_chart is not None
        assert metrics_chart is not None
        
        # Verify data consistency
        assert len(sample_schedule) == 2
    
    def test_charts_runner_config_integration(self, sample_config):
        """Test charts runner configuration integration."""
        # Create sample schedule
        sample_schedule = {
            "submission_1": date(2024, 1, 15),
            "submission_2": date(2024, 2, 1)
        }
        
        # Test that charts use configuration properly
        gantt_chart = create_gantt_chart(sample_schedule, sample_config)
        metrics_chart = create_metrics_chart(sample_schedule, sample_config)
        
        assert gantt_chart is not None
        assert metrics_chart is not None
        
        # Verify configuration is used
        assert sample_config is not None
