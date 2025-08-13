"""Tests for the new function-based gantt chart components."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional, Any

from app.components.gantt.chart import create_gantt_chart
from app.components.gantt.timeline import get_timeline_range, get_title_text, get_concurrency_map, add_background_elements
from app.components.gantt.activity import add_activity_bars, add_dependency_arrows
from src.core.models import Submission, SubmissionType, Config, ScheduleState, SchedulerStrategy


class TestGanttChartCreation:
    """Test the main gantt chart creation function."""
    
    def test_create_gantt_chart_success(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test successful gantt chart creation."""
        schedule_state = ScheduleState(
            schedule=sample_schedule,
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            metadata={'source': 'test'},
            timestamp='2024-01-01T00:00:00'
        )
        fig = create_gantt_chart(schedule_state)
        
        assert isinstance(fig, go.Figure)
        assert hasattr(fig.layout, 'title') and fig.layout.title is not None
        assert hasattr(fig.layout.title, 'text') and fig.layout.title.text is not None
        assert "Paper Submission Timeline" in fig.layout.title.text
        assert hasattr(fig.layout, 'height') and fig.layout.height > 400  # Should have dynamic height
    
    def test_create_gantt_chart_empty_schedule(self, sample_config: Config) -> None:
        """Test gantt chart creation with empty schedule."""
        schedule_state = ScheduleState(
            schedule={},
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            metadata={'source': 'test'},
            timestamp='2024-01-01T00:00:00'
        )
        fig = create_gantt_chart(schedule_state)
        
        assert isinstance(fig, go.Figure)
        assert hasattr(fig.layout, 'title') and fig.layout.title is not None
        assert "No Schedule Data Available" in fig.layout.title.text
    
    def test_create_gantt_chart_invalid_inputs(self, sample_config: Config) -> None:
        """Test gantt chart creation with invalid inputs."""
        # Test with invalid schedule state type
        with pytest.raises(TypeError):
            create_gantt_chart("invalid")  # type: ignore
        
        # Test with None
        with pytest.raises(AttributeError):
            create_gantt_chart(None)  # type: ignore
    
    def test_create_gantt_chart_error_handling(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test error handling during chart creation."""
        schedule_state = ScheduleState(
            schedule=sample_schedule,
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            metadata={'source': 'test'},
            timestamp='2024-01-01T00:00:00'
        )
        
        # Mock an error in timeline calculation
        with patch('app.components.gantt.timeline.get_timeline_range', side_effect=Exception("Test error")):
            fig = create_gantt_chart(schedule_state)
            
            # Should return error chart instead of crashing
            assert isinstance(fig, go.Figure)
            assert hasattr(fig.layout, 'title') and fig.layout.title is not None
            assert "Chart Creation Failed" in fig.layout.title.text


class TestTimelineFunctions:
    """Test timeline-related functions."""
    
    def test_get_timeline_range(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test timeline range calculation."""
        timeline_range = get_timeline_range(sample_schedule, sample_config)
        
        assert "min_date" in timeline_range
        assert "max_date" in timeline_range
        assert "timeline_start" in timeline_range
        assert "max_concurrency" in timeline_range
        # Account for 30-day buffer added for visualization
        assert timeline_range["min_date"] == date(2024, 11, 1)  # 30 days before earliest schedule date
        assert timeline_range["max_date"] == date(2025, 3, 3)   # 30 days after latest schedule date
    
    def test_get_title_text(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test title text generation."""
        timeline_range = get_timeline_range(sample_schedule, sample_config)
        title = get_title_text(timeline_range)
        
        assert "Paper Submission Timeline" in title
        assert "2024" in title  # Should include year range


class TestConcurrencyFunctions:
    """Test concurrency-related functions."""
    
    def test_get_concurrency_map(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test concurrency map generation."""
        concurrency_map = get_concurrency_map(sample_schedule, sample_config)
        
        assert isinstance(concurrency_map, dict)
        assert len(concurrency_map) == len(sample_schedule)
        
        # Check that each submission gets a unique row
        rows = list(concurrency_map.values())
        assert len(set(rows)) == len(rows)  # All rows should be unique
        
        # Check that rows are sequential starting from 0
        assert min(rows) == 0
        assert max(rows) == len(rows) - 1


class TestActivitiesFunctions:
    """Test activity-related functions."""
    
    def test_add_activity_bars(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test adding activity bars to the chart."""
        fig = go.Figure()
        concurrency_map = get_concurrency_map(sample_schedule, sample_config)
        
        add_activity_bars(fig, sample_schedule, sample_config, concurrency_map)
        
        # Check that shapes were added (activity bars)
        assert len(fig.layout.shapes) > 0
        
        # Check that annotations were added (labels)
        assert len(fig.layout.annotations) > 0
    
    def test_add_dependency_arrows(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test adding dependency arrows to the chart."""
        fig = go.Figure()
        concurrency_map = get_concurrency_map(sample_schedule, sample_config)
        
        add_dependency_arrows(fig, sample_schedule, sample_config, concurrency_map)
        
        # Check that traces were added (dependency arrows)
        # Note: arrows are added as traces, not shapes
        assert len(fig.data) > 0


class TestBackgroundsFunctions:
    """Test background-related functions."""
    
    def test_add_background_elements(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test adding background elements to the chart."""
        fig = go.Figure()
        
        # Configure layout first so backgrounds can read dimensions
        timeline_range = get_timeline_range(sample_schedule, sample_config)
        fig.update_layout(
            xaxis={'range': [timeline_range['min_date'], timeline_range['max_date']]},
            yaxis={'range': [-0.5, timeline_range['max_concurrency'] + 0.5]}
        )
        
        add_background_elements(fig)
        
        # Check that shapes were added (background elements)
        assert len(fig.layout.shapes) > 0
        
        # Check that annotations were added (month labels)
        assert len(fig.layout.annotations) > 0


class TestGanttChartIntegration:
    """Test full gantt chart integration."""
    
    def test_full_chart_creation_flow(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test the complete chart creation flow."""
        schedule_state = ScheduleState(
            schedule=sample_schedule,
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            metadata={'source': 'test'},
            timestamp='2024-01-01T00:00:00'
        )
        
        fig = create_gantt_chart(schedule_state)
        
        # Verify the complete chart structure
        assert isinstance(fig, go.Figure)
        assert hasattr(fig.layout, 'title')
        assert hasattr(fig.layout, 'xaxis')
        assert hasattr(fig.layout, 'yaxis')
        assert hasattr(fig.layout, 'height')
        
        # Check that all components were added
        assert len(fig.layout.shapes) > 0  # Backgrounds and activities
        assert len(fig.layout.annotations) > 0  # Labels and month markers
        assert len(fig.data) > 0  # Dependency arrows
    
    def test_chart_with_blackout_periods(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test chart creation with blackout periods."""
        schedule_state = ScheduleState(
            schedule=sample_schedule,
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            metadata={'source': 'test'},
            timestamp='2024-01-01T00:00:00'
        )
        
        fig = create_gantt_chart(schedule_state)
        
        # Verify background elements were added
        assert len(fig.layout.shapes) > 0
        assert len(fig.layout.annotations) > 0
    
    def test_chart_with_working_days_only(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test chart creation with working days only."""
        schedule_state = ScheduleState(
            schedule=sample_schedule,
            config=sample_config,
            strategy=SchedulerStrategy.GREEDY,
            metadata={'source': 'test'},
            timestamp='2024-01-01T00:00:00'
        )
        
        fig = create_gantt_chart(schedule_state)
        
        # Verify the chart was created successfully
        assert isinstance(fig, go.Figure)
        assert hasattr(fig.layout, 'title')
