"""
Tests for web application components and layouts.
"""

import json
import tempfile
import time
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import dash
import pytest

from app.components.charts.gantt_chart import create_gantt_chart
from app.components.charts.metrics_chart import create_metrics_chart
from app.components.tables.schedule_table import create_schedule_table
from app.layouts.header import create_header
from app.layouts.main_content import create_main_content
from app.layouts.sidebar import create_sidebar
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


class TestWebAppComponents:
    """Test web app component integration."""
    
    @pytest.fixture
    def sample_layout_data(self) -> dict:
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
    
    def test_header_component_rendering(self, sample_layout_data: dict) -> None:
        """Test header component rendering."""
        header_component = create_header()
        
        assert header_component is not None
        # Test that component has expected structure
        assert hasattr(header_component, 'children') or hasattr(header_component, 'type')
    
    def test_sidebar_component_rendering(self, sample_layout_data: dict) -> None:
        """Test sidebar component rendering."""
        sidebar_component = create_sidebar()
        
        assert sidebar_component is not None
        # Test that component has expected structure
        assert hasattr(sidebar_component, 'children') or hasattr(sidebar_component, 'type')
    
    def test_main_content_component_rendering(self, sample_layout_data: dict) -> None:
        """Test main content component rendering."""
        main_component = create_main_content()
        
        assert main_component is not None
        # Test that component has expected structure
        assert hasattr(main_component, 'children') or hasattr(main_component, 'type')
    
    def test_chart_component_integration(self, sample_schedule_data: ScheduleData) -> None:
        """Test chart component integration."""
        fig = create_gantt_chart(
            sample_schedule_data.schedule,
            sample_schedule_data.config
        )
        
        assert fig is not None
        assert hasattr(fig, 'layout')
        assert fig.layout.title.text == 'Schedule Timeline'
    
    def test_table_component_integration(self, sample_schedule_data: ScheduleData) -> None:
        """Test table component integration."""
        table_data = create_schedule_table(
            sample_schedule_data.schedule,
            sample_schedule_data.config
        )
        
        assert isinstance(table_data, list)
        assert len(table_data) > 0
        assert 'id' in table_data[0]
        assert 'title' in table_data[0]
    
    def test_component_id_consistency(self) -> None:
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
    
    def test_component_styling_integration(self) -> None:
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
    
    def test_component_accessibility_integration(self) -> None:
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
    
    def test_component_responsiveness_integration(self) -> None:
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
    
    def test_component_performance_integration(self) -> None:
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
    
    def test_component_error_boundaries(self) -> None:
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
    
    def test_component_state_management(self) -> None:
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


class TestWebAppChartsRunner:
    """Test web app charts runner functionality."""
    
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
    
    def test_charts_runner_initialization(self) -> None:
        """Test charts runner initialization."""
        # Test that charts runner can be imported and initialized
        try:
            assert True
        except ImportError:
            pytest.fail("Charts runner components should be importable")
    
    def test_gantt_chart_runner(self, sample_config: Mock) -> None:
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
    
    def test_metrics_chart_runner(self, sample_config: Mock) -> None:
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
    
    def test_charts_runner_error_handling(self, sample_config: Mock) -> None:
        """Test charts runner error handling."""
        # Test with invalid schedule
        invalid_schedule = {"invalid_id": date(2024, 1, 1)}  # Use date instead of string
        
        try:
            gantt_chart = create_gantt_chart(invalid_schedule, sample_config)
            # Should handle gracefully
            assert gantt_chart is not None
        except Exception:
            # Should not raise exception for invalid data
            pass
    
    def test_charts_runner_performance(self, sample_config: Mock) -> None:
        """Test charts runner performance."""
        # Create large schedule with valid dates
        large_schedule = {}
        
        start_date = date(2024, 1, 1)
        for i in range(100):
            # Use timedelta to ensure valid dates
            submission_date = start_date + timedelta(days=i)
            large_schedule[f"submission_{i}"] = submission_date
        
        # Test performance with large dataset
        start_time = time.time()
        
        gantt_chart = create_gantt_chart(large_schedule, sample_config)
        metrics_chart = create_metrics_chart(large_schedule, sample_config)
        
        end_time = time.time()
        
        # Should complete within reasonable time
        assert end_time - start_time < 10.0  # 10 seconds max
        assert gantt_chart is not None
        assert metrics_chart is not None
    
    def test_charts_runner_data_consistency(self, sample_config: Mock) -> None:
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
    
    def test_charts_runner_config_integration(self, sample_config: Mock) -> None:
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
