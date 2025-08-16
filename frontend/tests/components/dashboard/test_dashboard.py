"""Tests for dashboard chart component."""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import plotly.graph_objects as go

from app.components.dashboard.chart import (
    generate_timeline_chart, _create_error_chart
)
from app.components.dashboard.layout import create_dashboard_layout, create_timeline_layout
from src.core.models import Config, ScheduleState, SchedulerStrategy
from typing import Dict, List, Any, Optional
from dash import html, dcc


class TestDashboardChart:
    """Test cases for dashboard chart functionality."""
    
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
                start_date=datetime(2024, 5, 1),
                end_date=datetime(2024, 6, 1),
                author="ed",
                depends_on=[]
            ),
            Mock(
                id="paper2", 
                start_date=datetime(2024, 7, 1),
                end_date=datetime(2024, 8, 1),
                author="pccp",
                depends_on=["paper1"]
            )
        ]
    
    @pytest.fixture
    def sample_schedule_state(self, sample_config, sample_schedule):
        """Sample schedule state for testing."""
        return ScheduleState(
            schedule=sample_schedule,
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            timestamp=datetime.now().isoformat()
        )
    
    def test_generate_timeline_chart_success(self, sample_config, sample_schedule, sample_schedule_state):
        """Test successful timeline chart generation."""
        with patch('app.components.dashboard.chart.load_config', return_value=sample_config), \
             patch('app.components.dashboard.chart.GreedyScheduler') as mock_scheduler, \
             patch('app.components.dashboard.chart.create_gantt_chart') as mock_create_gantt:
            
            # Mock scheduler
            mock_scheduler_instance = Mock()
            mock_scheduler_instance.schedule.return_value = sample_schedule
            mock_scheduler.return_value = mock_scheduler_instance
            
            # Mock gantt chart creation
            mock_figure = Mock()
            mock_create_gantt.return_value = mock_figure
            
            # Test
            result = generate_timeline_chart()
            
            assert result == mock_figure
            mock_scheduler_instance.schedule.assert_called_once()
            mock_create_gantt.assert_called_once_with(sample_schedule_state)
    
    def test_generate_timeline_chart_no_schedule(self, sample_config):
        """Test timeline chart generation when no schedule is generated."""
        with patch('app.components.dashboard.chart.load_config', return_value=sample_config), \
             patch('app.components.dashboard.chart.GreedyScheduler') as mock_scheduler, \
             patch('app.components.dashboard.chart._create_error_chart') as mock_error_chart:
            
            # Mock scheduler returning no schedule
            mock_scheduler_instance = Mock()
            mock_scheduler_instance.schedule.return_value = None
            mock_scheduler.return_value = mock_scheduler_instance
            
            # Mock error chart
            mock_error_figure = Mock()
            mock_error_chart.return_value = mock_error_figure
            
            # Test
            result = generate_timeline_chart()
            
            assert result == mock_error_figure
            mock_error_chart.assert_called_with("No schedule could be generated")
    
    def test_generate_timeline_chart_import_error(self):
        """Test timeline chart generation with import error."""
        with patch('app.components.dashboard.chart.load_config', side_effect=ImportError("Test import error")), \
             patch('app.components.dashboard.chart._create_error_chart') as mock_error_chart:
            
            # Mock error chart
            mock_error_figure = Mock()
            mock_error_chart.return_value = mock_error_figure
            
            # Test
            result = generate_timeline_chart()
            
            assert result == mock_error_figure
            mock_error_chart.assert_called_with("Import error: Test import error")
    
    def test_create_error_chart(self):
        """Test error chart creation."""
        error_msg = "Test error message"
        result = _create_error_chart(error_msg)
        
        assert isinstance(result, go.Figure)
        assert result.layout.title.text == "Paper Planner Timeline - Error"
        assert result.layout.height == 400


class TestDashboardLayout:
    """Test cases for dashboard layout functionality."""
    
    @patch('app.components.dashboard.layout.generate_timeline_chart')
    def test_create_dashboard_layout_structure(self, mock_generate_chart):
        """Test that dashboard layout has correct structure."""
        mock_figure = Mock()
        mock_generate_chart.return_value = mock_figure
        
        layout = create_dashboard_layout()
        
        # Should be a div container
        assert isinstance(layout, html.Div)
        assert layout.id is None  # No specific ID
        
        # Should have 3 children: header, info panels, and chart
        assert len(layout.children) == 3
        
        # First child should be header
        header = layout.children[0]
        assert isinstance(header, html.Div)
        assert len(header.children) == 2  # H1 and P
        
        # Second child should be info panels
        info_panels = layout.children[1]
        assert isinstance(info_panels, html.Div)
        assert len(info_panels.children) == 2  # Two info panels
        
        # Third child should be graph
        chart = layout.children[2]
        assert isinstance(chart, dcc.Graph)
        assert chart.id == 'timeline-chart'
    
    @patch('app.components.dashboard.layout.generate_timeline_chart')
    def test_create_timeline_layout_structure(self, mock_generate_chart):
        """Test that timeline layout has correct structure."""
        mock_figure = Mock()
        mock_generate_chart.return_value = mock_figure
        
        layout = create_timeline_layout()
        
        # Should be a div container
        assert isinstance(layout, html.Div)
        assert layout.id is None  # No specific ID
        
        # Should have 2 children: header and chart
        assert len(layout.children) == 2
        
        # First child should be header
        header = layout.children[0]
        assert isinstance(header, html.H1)
        assert "Paper Planner - Timeline" in header.children
        
        # Second child should be graph
        chart = layout.children[1]
        assert isinstance(chart, dcc.Graph)
        assert chart.id == 'timeline-chart'
    
    @patch('app.components.dashboard.layout.generate_timeline_chart')
    def test_create_dashboard_layout_styling(self, mock_generate_chart):
        """Test that dashboard layout has correct styling."""
        mock_figure = Mock()
        mock_generate_chart.return_value = mock_figure
        
        layout = create_dashboard_layout()
        
        # Container styling
        expected_style = {
            'height': '100vh',
            'width': '100%',
            'margin': 0,
            'padding': '20px'
        }
        assert layout.style == expected_style
    
    @patch('app.components.dashboard.layout.generate_timeline_chart')
    def test_create_timeline_layout_styling(self, mock_generate_chart):
        """Test that timeline layout has correct styling."""
        mock_figure = Mock()
        mock_generate_chart.return_value = mock_figure
        
        layout = create_timeline_layout()
        
        # Container styling
        expected_style = {
            'height': '100vh',
            'width': '100%',
            'margin': 0,
            'padding': '20px'
        }
        assert layout.style == expected_style
        
        # Header styling
        header = layout.children[0]
        expected_header_style = {
            'textAlign': 'center',
            'color': '#333',
            'marginBottom': '20px'
        }
        assert header.style == expected_header_style
        
        # Chart styling
        chart = layout.children[1]
        expected_chart_style = {
            'height': '80vh',
            'width': '100%'
        }
        assert chart.style == expected_chart_style
