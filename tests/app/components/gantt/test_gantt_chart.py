"""Tests for the new function-based gantt chart components."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Optional, Any

from app.components.gantt.chart import create_gantt_chart
from app.components.gantt.timeline import get_timeline_range, get_title_text
from app.components.gantt.activities import add_activity_bars, add_dependency_arrows
from app.components.gantt.backgrounds import add_background_elements
from src.core.models import Submission, SubmissionType, Config


class TestGanttChartCreation:
    """Test the main gantt chart creation function."""
    
    def test_create_gantt_chart_success(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test successful gantt chart creation."""
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert hasattr(fig.layout, 'title') and fig.layout.title is not None
        assert hasattr(fig.layout.title, 'text') and fig.layout.title.text is not None
        assert "Paper Submission Timeline" in fig.layout.title.text
        assert hasattr(fig.layout, 'height') and fig.layout.height > 400  # Should have dynamic height
    
    def test_create_gantt_chart_empty_schedule(self, sample_config: Config) -> None:
        """Test gantt chart creation with empty schedule."""
        fig = create_gantt_chart({}, sample_config)
        
        assert isinstance(fig, go.Figure)
        assert hasattr(fig.layout, 'title') and fig.layout.title is not None
        assert "No Schedule Data Available" in fig.layout.title.text
    
    def test_create_gantt_chart_with_forced_timeline(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test gantt chart creation with forced timeline."""
        forced_timeline = {
            "force_timeline_range": True,
            "timeline_start": date(2025, 7, 1),
            "timeline_end": date(2026, 2, 1)
        }
        
        fig = create_gantt_chart(sample_schedule, sample_config, forced_timeline)
        
        assert isinstance(fig, go.Figure)
        # Check that forced timeline is respected
        assert hasattr(fig.layout, 'xaxis') and fig.layout.xaxis is not None
        assert hasattr(fig.layout.xaxis, 'range') and fig.layout.xaxis.range is not None
        assert fig.layout.xaxis.range[0] == date(2025, 7, 1)
        assert fig.layout.xaxis.range[1] == date(2026, 2, 1)
    
    def test_create_gantt_chart_invalid_inputs(self, sample_config: Config) -> None:
        """Test gantt chart creation with invalid inputs."""
        # Test with invalid schedule type
        with pytest.raises(TypeError):
            create_gantt_chart("invalid", sample_config)  # type: ignore
        
        # Test with invalid config type
        with pytest.raises(TypeError):
            create_gantt_chart({}, "invalid")  # type: ignore
    
    def test_create_gantt_chart_error_handling(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test error handling during chart creation."""
        # Mock an error in timeline calculation
        with patch('app.components.gantt.timeline.get_timeline_range', side_effect=Exception("Test error")):
            fig = create_gantt_chart(sample_schedule, sample_config)
            
            # Should return error chart instead of crashing
            assert isinstance(fig, go.Figure)
            assert hasattr(fig.layout, 'title') and fig.layout.title is not None
            assert "Error creating chart" in fig.layout.title.text


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
    
    def test_get_working_days_filter(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test working days filter generation."""
        from app.components.gantt.timeline import get_working_days_filter
        
        timeline_range = get_timeline_range(sample_schedule, sample_config)
        working_days = get_working_days_filter(timeline_range)
        
        assert isinstance(working_days, list)
        # Should have days from timeline_start to max_date (including buffer)
        expected_days = (timeline_range["max_date"] - timeline_range["timeline_start"]).days + 1
        assert len(working_days) == expected_days


class TestActivitiesFunctions:
    """Test activity-related functions."""
    
    def test_add_activity_bars(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test adding activity bars to chart."""
        fig = go.Figure()
        timeline_range = get_timeline_range(sample_schedule, sample_config)
        
        # Mock concurrency calculation
        concurrency_map = {"mod1-wrk": 1, "paper1-pap": 2, "mod2-wrk": 1, "paper2-pap": 2}
        
        add_activity_bars(fig, sample_schedule, sample_config, concurrency_map, timeline_range["timeline_start"])
        
        # Check that bars were added (as shapes)
        assert fig.layout.shapes is not None
        assert len(fig.layout.shapes) > 0
        # Should have one shape per submission
        assert len(fig.layout.shapes) == len(sample_schedule)
    
    def test_add_dependency_arrows(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test adding dependency arrows to chart."""
        fig = go.Figure()
        timeline_range = get_timeline_range(sample_schedule, sample_config)
        
        # Mock concurrency calculation
        concurrency_map = {"mod1-wrk": 1, "paper1-pap": 2, "mod2-wrk": 1, "paper2-pap": 2}
        
        add_dependency_arrows(fig, sample_schedule, sample_config, concurrency_map, timeline_range["timeline_start"])
        
        # Check that arrows were added (as data traces)
        assert len(fig.data) > 0


class TestBackgroundsFunctions:
    """Test background-related functions."""
    
    def test_add_background_elements(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test adding background elements to chart."""
        fig = go.Figure()
        timeline_range = get_timeline_range(sample_schedule, sample_config)
        
        add_background_elements(fig, sample_config, timeline_range["timeline_start"], 
                              timeline_range["max_date"], timeline_range["max_concurrency"])
        
        # Check that background elements were added
        assert fig.layout.shapes is not None
        assert len(fig.layout.shapes) > 0


class TestGanttChartIntegration:
    """Test integration between all gantt chart components."""
    
    def test_full_chart_creation_flow(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test the complete chart creation flow."""
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        # Verify all components are present
        assert isinstance(fig, go.Figure)
        assert fig.layout.title is not None
        assert fig.layout.title.text is not None
        assert fig.layout.shapes is not None
        assert len(fig.layout.shapes) > 0  # Should have activity bars and backgrounds
        assert fig.layout.xaxis is not None  # Should have timeline
        assert fig.layout.yaxis is not None  # Should have y-axis
    
    def test_chart_with_blackout_periods(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test chart creation with blackout periods enabled."""
        # Enable blackout periods
        sample_config.scheduling_options["enable_blackout_periods"] = True
        sample_config.blackout_dates = [date(2025, 12, 25), date(2025, 12, 26)]
        
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        # Should have blackout period shapes
        assert fig.layout.shapes is not None
        assert len(fig.layout.shapes) > 0
    
    def test_chart_with_working_days_only(self, sample_schedule: Dict[str, date], sample_config: Config) -> None:
        """Test chart creation with working days only enabled."""
        # Enable working days only
        sample_config.scheduling_options["enable_working_days_only"] = True
        
        fig = create_gantt_chart(sample_schedule, sample_config)
        
        # Should have working days background
        assert fig.layout.shapes is not None
        assert len(fig.layout.shapes) > 0
