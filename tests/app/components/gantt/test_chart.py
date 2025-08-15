"""Tests for gantt chart component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date, datetime
import plotly.graph_objects as go

from app.components.gantt.chart import create_gantt_chart, _configure_chart_layout
from app.components.gantt.chart import _create_empty_chart, _create_error_chart
from src.core.models import ScheduleState, Config, SchedulerStrategy
from typing import Dict, Any


class TestGanttChart:
    """Test cases for gantt chart functionality."""
    
    # Use fixtures from conftest.py instead of defining them here
    
    def test_create_gantt_chart_success(self, sample_schedule_state):
        """Test successful gantt chart creation."""
        fig = create_gantt_chart(sample_schedule_state)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title is not None
        assert "Paper Submission Timeline" in fig.layout.title.text
    
    def test_create_gantt_chart_empty_schedule(self, sample_config):
        """Test gantt chart creation with empty schedule."""
        empty_state = ScheduleState(
            schedule={},
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            metadata={'source': 'test'},
            timestamp=datetime.now().isoformat()
        )
        
        fig = create_gantt_chart(empty_state)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Schedule Data Available'
    
    def test_create_gantt_chart_none_schedule_state(self):
        """Test gantt chart creation with None schedule state."""
        fig = create_gantt_chart(None)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Schedule Data Available'
    
    def test_create_gantt_chart_invalid_schedule_state(self):
        """Test gantt chart creation with invalid schedule state."""
        invalid_state = Mock()
        invalid_state.schedule = None
        
        fig = create_gantt_chart(invalid_state)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Schedule Data Available'
    
    @patch('app.components.gantt.chart.get_chart_dimensions')
    def test_create_gantt_chart_with_timeline_range(self, mock_get_chart_dimensions, sample_schedule_state):
        """Test gantt chart creation with timeline range."""
        mock_timeline = {
            'min_date': date(2024, 4, 1),
            'max_date': date(2024, 8, 1),
            'timeline_start': date(2024, 4, 1),
            'span_days': 120,
            'max_concurrency': 3
        }
        mock_get_chart_dimensions.return_value = mock_timeline
        
        fig = create_gantt_chart(sample_schedule_state)
        
        assert isinstance(fig, go.Figure)
        mock_get_chart_dimensions.assert_called_once()
    
    @patch('app.components.gantt.chart.get_chart_dimensions')
    @patch('app.components.gantt.chart.add_background_elements')
    @patch('app.components.gantt.chart.add_activity_bars')
    @patch('app.components.gantt.chart.add_dependency_arrows')
    def test_create_gantt_chart_calls_components(self, mock_add_deps, mock_add_activities, 
                                               mock_add_background, mock_get_chart_dimensions, sample_schedule_state):
        """Test that gantt chart creation calls all required components."""
        mock_timeline = {
            'min_date': date(2024, 4, 1),
            'max_date': date(2024, 8, 1),
            'timeline_start': date(2024, 4, 1),
            'span_days': 120,
            'max_concurrency': 3
        }
        mock_get_chart_dimensions.return_value = mock_timeline
        
        fig = create_gantt_chart(sample_schedule_state)
        
        mock_get_chart_dimensions.assert_called_once()
        mock_add_background.assert_called_once()
        mock_add_activities.assert_called_once()
        mock_add_deps.assert_called_once()
    
    def test_create_gantt_chart_exception_handling(self, sample_schedule_state):
        """Test gantt chart creation handles exceptions gracefully."""
        with patch('app.components.gantt.chart.get_chart_dimensions', side_effect=Exception("Test error")):
            fig = create_gantt_chart(sample_schedule_state)
            
            assert isinstance(fig, go.Figure)
            assert fig.layout is not None
            assert fig.layout.title.text == 'Chart Creation Failed'
    
    def test_configure_chart_layout(self, sample_schedule_state):
        """Test chart layout configuration."""
        fig = go.Figure()
        timeline_range = {
            'min_date': date(2024, 4, 1),
            'max_date': date(2024, 8, 1),
            'timeline_start': date(2024, 4, 1),
            'span_days': 120,
            'max_concurrency': 3
        }
        
        _configure_chart_layout(fig, timeline_range)
        
        assert fig.layout is not None
        assert fig.layout.title is not None
        assert "Paper Submission Timeline" in fig.layout.title.text
        assert fig.layout.height == 400 + 3 * 30  # 400 + max_concurrency * 30
        assert fig.layout.xaxis.type == 'date'
        assert fig.layout.yaxis.title.text == 'Activities'
    
    def test_create_empty_chart(self):
        """Test empty chart creation."""
        fig = _create_empty_chart()
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'No Schedule Data Available'
        assert fig.layout.height == 400
        assert fig.layout.plot_bgcolor == 'white'
        assert fig.layout.paper_bgcolor == 'white'
    
    def test_create_error_chart(self):
        """Test error chart creation."""
        error_message = "Test error message"
        fig = _create_error_chart(error_message)
        
        assert isinstance(fig, go.Figure)
        assert fig.layout is not None
        assert fig.layout.title.text == 'Chart Creation Failed'
        assert fig.layout.height == 400
        assert fig.layout.plot_bgcolor == 'white'
        assert fig.layout.paper_bgcolor == 'white'
        
        # Check that error annotation is added
        annotations = fig.layout.annotations
        assert len(annotations) == 1
        assert annotations[0].text == error_message
        assert annotations[0].font.color == '#e74c3c'
    
    def test_chart_layout_properties(self, sample_schedule_state):
        """Test that created chart has expected layout properties."""
        fig = create_gantt_chart(sample_schedule_state)
        
        assert fig.layout is not None
        assert fig.layout.title is not None
        assert fig.layout.xaxis is not None
        assert fig.layout.yaxis is not None
        assert fig.layout.plot_bgcolor == 'white'
        assert fig.layout.paper_bgcolor == 'white'
        assert fig.layout.showlegend is False
    
    def test_chart_height_calculation(self, sample_schedule_state):
        """Test that chart height is calculated correctly based on concurrency."""
        with patch('app.components.gantt.chart.get_chart_dimensions') as mock_get_chart_dimensions:
            mock_get_chart_dimensions.return_value = {
                'min_date': date(2024, 4, 1),
                'max_date': date(2024, 8, 1),
                'timeline_start': date(2024, 4, 1),
                'span_days': 120,
                'max_concurrency': 5
            }
            
            fig = create_gantt_chart(sample_schedule_state)
            
            # Height should be 400 + (5 * 30) = 550
            assert fig.layout.height == 550
