"""Tests for metrics chart component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
import plotly.graph_objects as go

from app.components.metrics.chart import (
    generate_metrics_chart, _create_error_chart
)
from src.core.models import Config
from typing import Dict, List, Any, Optional


class TestMetricsChart:
    """Test cases for metrics chart functionality."""
    
    @pytest.fixture
    def sample_config(self):
        """Sample config for testing."""
        return Config(
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3,
            submissions=[],
            conferences=[],
            blackout_dates=[],
            scheduling_options={"enable_early_abstract_scheduling": False},
            priority_weights={
                "engineering_paper": 2.0,
                "medical_paper": 1.0,
                "mod": 1.5,
                "abstract": 0.5
            },
            penalty_costs={"default_mod_penalty_per_day": 1000},
            data_files={
                "conferences": "conferences.json",
                "mods": "mods.json",
                "papers": "papers.json"
            }
        )
    
    @pytest.fixture
    def sample_schedule(self):
        """Sample schedule data for testing."""
        return [
            Mock(
                id="paper1",
                start_date=date(2024, 5, 1),
                end_date=date(2024, 6, 1),
                author="ed",
                depends_on=[]
            ),
            Mock(
                id="paper2", 
                start_date=date(2024, 7, 1),
                end_date=date(2024, 8, 1),
                author="pccp",
                depends_on=["paper1"]
            )
        ]
    
    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis data for testing."""
        return {
            "efficiency": 85.0,
            "utilization": 78.0,
            "timeline": 92.0,
            "quality": 88.0
        }
    
    def test_create_metrics_chart_success(self, sample_config, sample_schedule, sample_analysis):
        """Test successful metrics chart generation."""
        # Mock the dependencies
        with patch('app.components.metrics.chart.load_config', return_value=sample_config), \
             patch('app.components.metrics.chart.GreedyScheduler') as mock_scheduler, \
             patch('app.components.metrics.chart.ScheduleAnalysis') as mock_analysis:
            
            # Set up mocks
            mock_scheduler_instance = Mock()
            mock_scheduler.return_value = mock_scheduler_instance
            mock_scheduler_instance.schedule.return_value = sample_schedule
            
            mock_analysis_instance = Mock()
            mock_analysis.return_value = mock_analysis_instance
            mock_analysis_instance.analyze.return_value = sample_analysis
            
            # Call the function
            result = generate_metrics_chart()
            
            # Verify result
            assert result is not None
            assert isinstance(result, go.Figure)
            assert result.layout.title.text == "Paper Planner Metrics Dashboard"
            
            # Verify subplots were added
            assert len(result.data) > 0
    
    def test_generate_metrics_chart_no_schedule(self, sample_config):
        """Test metrics chart generation when no schedule is generated."""
        with patch('app.components.metrics.chart.load_config', return_value=sample_config), \
             patch('app.components.metrics.chart.GreedyScheduler') as mock_scheduler, \
             patch('app.components.metrics.chart._create_error_chart') as mock_error_chart:
            
            # Mock scheduler returning no schedule
            mock_scheduler_instance = Mock()
            mock_scheduler_instance.schedule.return_value = None
            mock_scheduler.return_value = mock_scheduler_instance
            
            # Mock error chart
            mock_error_figure = Mock()
            mock_error_chart.return_value = mock_error_figure
            
            # Test
            result = generate_metrics_chart()
            
            assert result == mock_error_figure
            mock_error_chart.assert_called_with("No schedule could be generated for metrics")
    
    def test_generate_metrics_chart_import_error(self):
        """Test metrics chart generation with import error."""
        with patch('app.components.metrics.chart.load_config', side_effect=ImportError("Test import error")), \
             patch('app.components.metrics.chart._create_error_chart') as mock_error_chart:
            
            # Mock error chart
            mock_error_figure = Mock()
            mock_error_chart.return_value = mock_error_figure
            
            # Test
            result = generate_metrics_chart()
            
            assert result == mock_error_figure
            mock_error_chart.assert_called_with("Import error: Test import error")
    
    def test_create_error_chart(self):
        """Test error chart creation."""
        error_msg = "Test error message"
        result = _create_error_chart(error_msg)
        
        assert isinstance(result, go.Figure)
        assert result.layout.title.text == "Paper Planner Metrics - Error"
        assert result.layout.height == 400


class TestMetricsFigureCreation:
    """Test cases for metrics figure creation methods."""
    
    @pytest.fixture
    def sample_schedule(self):
        """Sample schedule for testing figure creation."""
        return [
            Mock(
                id="item1",
                start_date=date(2024, 5, 1),
                end_date=date(2024, 6, 1),
                author="ed",
                depends_on=[]
            ),
            Mock(
                id="item2",
                start_date=date(2024, 6, 1),
                end_date=date(2024, 7, 1),
                author="pccp",
                depends_on=["item1"]
            )
        ]
    
    @pytest.fixture
    def sample_analysis(self):
        """Sample analysis for testing figure creation."""
        return {
            "efficiency": 85.0,
            "utilization": 78.0,
            "timeline": 92.0,
            "quality": 88.0
        }
    
    def test_create_metrics_figure_structure(self, sample_schedule, sample_analysis):
        """Test that metrics figure has correct structure."""
        with patch('app.components.metrics.chart._add_timeline_subplot') as mock_timeline, \
             patch('app.components.metrics.chart._add_resource_subplot') as mock_resource, \
             patch('app.components.metrics.chart._add_dependency_subplot') as mock_dependency, \
             patch('app.components.metrics.chart._add_performance_subplot') as mock_performance:
            
            from app.components.metrics.chart import _create_metrics_figure
            
            result = _create_metrics_figure(sample_analysis, sample_schedule)
            
            # Verify subplot calls
            mock_timeline.assert_called_once_with(result, sample_schedule, row=1, col=1)
            mock_resource.assert_called_once_with(result, sample_schedule, row=1, col=2)
            mock_dependency.assert_called_once_with(result, sample_schedule, row=2, col=1)
            mock_performance.assert_called_once_with(result, sample_analysis, row=2, col=2)
            
            # Verify figure properties
            assert result.layout.height == 800
            assert result.layout.title.text == "Paper Planner Metrics Dashboard"
            assert result.layout.showlegend is True
