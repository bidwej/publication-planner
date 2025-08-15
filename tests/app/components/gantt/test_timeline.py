"""Tests for gantt timeline component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
import plotly.graph_objects as go

from app.components.gantt.timeline import (
    get_chart_dimensions, get_title_text, get_concurrency_map, 
    add_background_elements
)
from src.core.models import Config
from typing import Dict, Any


class TestGanttTimeline:
    """Test cases for gantt timeline functionality."""
    
    # Use fixtures from conftest.py instead of defining them here
    
    def test_get_timeline_range_with_schedule(self, sample_schedule, sample_config):
        """Test timeline range calculation with valid schedule."""
        result = get_chart_dimensions(sample_schedule, sample_config)
        
        assert isinstance(result, dict)
        assert 'min_date' in result
        assert 'max_date' in result
        assert 'timeline_start' in result
        assert 'span_days' in result
        assert 'max_concurrency' in result
        
        # Check date calculations based on actual sample schedule
        # sample_schedule: mod1-wrk: 2024-12-01, paper1-pap: 2025-01-15, mod2-wrk: 2025-01-01, paper2-pap: 2025-02-01
        # min_date should be 2024-12-01 - 30 days = 2024-11-01
        # max_date should be 2025-02-01 + 30 days = 2025-03-03
        expected_min = date(2024, 11, 1)  # 2024-12-01 - 30 days buffer
        expected_max = date(2025, 3, 3)   # 2025-02-01 + 30 days buffer
        
        assert result['min_date'] == expected_min
        assert result['max_date'] == expected_max
        assert result['span_days'] > 0
        
        # Check buffer application
        expected_start = date(2024, 12, 1) - timedelta(days=30)  # mod1-wrk - 30 days
        assert result['timeline_start'] == expected_start
    
    def test_get_timeline_range_empty_schedule(self, sample_config):
        """Test timeline range calculation with empty schedule."""
        empty_schedule = {}
        result = get_chart_dimensions(empty_schedule, sample_config)
        
        assert isinstance(result, dict)
        assert 'min_date' in result
        assert 'max_date' in result
        assert 'timeline_start' in result
        assert 'span_days' in result
        assert 'max_concurrency' in result
        
        # Should use default dates
        today = date.today()
        assert result['min_date'] == today
        assert result['max_date'] == today + timedelta(days=365)
        assert result['span_days'] == 365
        assert result['max_concurrency'] == 0
    
    def test_get_timeline_range_none_schedule(self, sample_config):
        """Test timeline range calculation with None schedule."""
        result = get_chart_dimensions(None, sample_config)
        
        assert isinstance(result, dict)
        assert 'min_date' in result
        assert 'max_date' in result
        assert 'timeline_start' in result
        assert 'span_days' in result
        assert 'max_concurrency' in result
        
        # Should use default dates
        today = date.today()
        assert result['min_date'] == today
        assert result['max_date'] == today + timedelta(days=365)
        assert result['span_days'] == 365
        assert result['max_concurrency'] == 0
    
    def test_get_timeline_range_single_date(self, sample_config):
        """Test timeline range calculation with single date."""
        single_schedule = {"paper1": date(2024, 6, 15)}
        result = get_chart_dimensions(single_schedule, sample_config)
        
        assert isinstance(result, dict)
        assert result['min_date'] == date(2024, 5, 16)  # 6/15 - 30 days buffer
        assert result['max_date'] == date(2024, 7, 15)  # 6/15 + 30 days buffer
        assert result['span_days'] == 60  # 30 + 30 days
    
    def test_get_title_text_same_year(self):
        """Test title text generation for same year."""
        timeline_range = {
            'min_date': date(2024, 4, 1),
            'max_date': date(2024, 8, 1)
        }
        
        title = get_title_text(timeline_range)
        
        assert isinstance(title, str)
        assert "Paper Submission Timeline" in title
        assert "Apr 2024" in title
        assert "Aug 2024" in title
        assert title == "Paper Submission Timeline: Apr 2024 - Aug 2024"
    
    def test_get_title_text_different_years(self):
        """Test title text generation for different years."""
        timeline_range = {
            'min_date': date(2024, 12, 1),
            'max_date': date(2025, 2, 1)
        }
        
        title = get_title_text(timeline_range)
        
        assert isinstance(title, str)
        assert "Paper Submission Timeline" in title
        assert "Dec 2024" in title
        assert "Feb 2025" in title
        assert title == "Paper Submission Timeline: Dec 2024 - Feb 2025"
    
    def test_get_title_text_edge_cases(self):
        """Test title text generation with edge cases."""
        # Same month
        timeline_range = {
            'min_date': date(2024, 6, 1),
            'max_date': date(2024, 6, 30)
        }
        title = get_title_text(timeline_range)
        assert "Jun 2024" in title
        
        # Year boundary
        timeline_range = {
            'min_date': date(2024, 12, 31),
            'max_date': date(2025, 1, 1)
        }
        title = get_title_text(timeline_range)
        assert "Dec 2024" in title
        assert "Jan 2025" in title
    
    def test_get_concurrency_map_with_schedule(self, sample_schedule):
        """Test concurrency map generation with valid schedule."""
        result = get_concurrency_map(sample_schedule)
        
        assert isinstance(result, dict)
        assert len(result) == 4  # sample_schedule has 4 items
        
        # Check that all submission IDs are present
        assert "mod1-wrk" in result
        assert "paper1-pap" in result
        assert "mod2-wrk" in result
        assert "paper2-pap" in result
        
        # Check row assignments (should be 0, 1, 2, 3 based on sorted dates)
        # sample_schedule: mod1-wrk: 2024-12-01, mod2-wrk: 2025-01-01, paper2-pap: 2025-02-01, paper1-pap: 2025-01-15
        # Sorted by date: mod1-wrk (2024-12-01), mod2-wrk (2025-01-01), paper1-pap (2025-01-15), paper2-pap (2025-02-01)
        assert result["mod1-wrk"] == 0   # 2024-12-01 (earliest)
        assert result["mod2-wrk"] == 1   # 2025-01-01
        assert result["paper1-pap"] == 2 # 2025-01-15
        assert result["paper2-pap"] == 3 # 2025-02-01 (latest)
    
    def test_get_concurrency_map_empty_schedule(self):
        """Test concurrency map generation with empty schedule."""
        empty_schedule = {}
        result = get_concurrency_map(empty_schedule)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_get_concurrency_map_none_schedule(self):
        """Test concurrency map generation with None schedule."""
        result = get_concurrency_map(None)
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_get_concurrency_map_single_submission(self):
        """Test concurrency map generation with single submission."""
        single_schedule = {"paper1": date(2024, 6, 15)}
        result = get_concurrency_map(single_schedule)
        
        assert isinstance(result, dict)
        assert len(result) == 1
        assert result["paper1"] == 0
    
    def test_get_concurrency_map_duplicate_dates(self):
        """Test concurrency map generation with duplicate dates."""
        duplicate_schedule = {
            "paper1": date(2024, 6, 15),
            "paper2": date(2024, 6, 15),
            "paper3": date(2024, 6, 20)
        }
        result = get_concurrency_map(duplicate_schedule)
        
        assert isinstance(result, dict)
        assert len(result) == 3
        
        # Should still assign sequential rows
        assert result["paper1"] == 0
        assert result["paper2"] == 1
        assert result["paper3"] == 2
    
    @patch('app.components.gantt.timeline._add_working_days_background')
    @patch('app.components.gantt.timeline._add_monthly_markers')
    def test_add_background_elements_success(self, mock_add_monthly, mock_add_working_days, sample_config):
        """Test successful background elements addition."""
        fig = go.Figure()
        
        # Set up figure layout with x and y axis ranges
        fig.update_layout(
            xaxis=dict(range=['2024-04-01', '2024-08-01']),
            yaxis=dict(range=[-0.5, 2.5])
        )
        
        add_background_elements(fig)
        
        # Check that background functions were called
        mock_add_working_days.assert_called_once()
        mock_add_monthly.assert_called_once()
        
        # Check that the functions were called with the correct arguments
        # The first call should be to _add_working_days_background
        args = mock_add_working_days.call_args[0]
        assert args[0] == fig  # figure
        assert args[1] == '2024-04-01'  # start_date (string)
        assert args[2] == '2024-08-01'  # end_date (string)
        assert args[3] == -0.5  # y_min
        assert args[4] == 2.5   # y_max
    
    def test_add_background_elements_no_x_range(self):
        """Test background elements addition with no x-axis range."""
        fig = go.Figure()
        # No x-axis range set
        
        # Should not raise exception, just print warning
        add_background_elements(fig)
        
        # Figure should remain unchanged
        assert fig.layout is not None
    
    def test_add_background_elements_no_y_range(self):
        """Test background elements addition with no y-axis range."""
        fig = go.Figure()
        fig.update_layout(xaxis=dict(range=['2024-04-01', '2024-08-01']))
        # No y-axis range set
        
        # Should not raise exception, just print warning
        add_background_elements(fig)
        
        # Figure should remain unchanged
        assert fig.layout is not None
    
    def test_timeline_range_buffer_calculation(self, sample_schedule, sample_config):
        """Test that timeline buffer is calculated correctly."""
        result = get_chart_dimensions(sample_schedule, sample_config)
        
        # Buffer should be 30 days
        buffer_days = 30
        
        # Check start date buffer
        earliest_date = min(sample_schedule.values())
        expected_start = earliest_date - timedelta(days=buffer_days)
        assert result['timeline_start'] == expected_start
        
        # Check end date buffer
        latest_date = max(sample_schedule.values())
        expected_end = latest_date + timedelta(days=buffer_days)
        assert result['max_date'] == expected_end
    
    def test_timeline_span_calculation(self, sample_schedule, sample_config):
        """Test that timeline span is calculated correctly."""
        result = get_chart_dimensions(sample_schedule, sample_config)
        
        # Span should be the difference between max and min dates
        expected_span = (result['max_date'] - result['min_date']).days
        assert result['span_days'] == expected_span
        
        # Span should be positive
        assert result['span_days'] > 0
    
    @patch('app.components.gantt.timeline.validate_resources_constraints')
    def test_max_concurrency_from_validation(self, mock_validate, sample_schedule, sample_config):
        """Test that max concurrency comes from resource validation."""
        mock_result = Mock()
        mock_result.max_observed = 5
        mock_validate.return_value = mock_result
        
        result = get_chart_dimensions(sample_schedule, sample_config)
        
        assert result['max_concurrency'] == 5
        mock_validate.assert_called_once_with(sample_schedule, sample_config)
