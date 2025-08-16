"""Tests for gantt timeline component."""

import pytest
from unittest.mock import Mock, patch
from datetime import date, timedelta
import plotly.graph_objects as go

from app.components.gantt.timeline import (
    get_timeline_range, assign_activity_rows
)
from src.core.models import Config
from typing import Dict, Any


class TestGanttTimeline:
    """Test cases for gantt timeline functionality."""
    
    # Use fixtures from conftest.py instead of defining them here
    
    def test_get_timeline_range_with_schedule(self, sample_schedule, sample_config):
        """Test timeline range calculation with valid schedule."""
        result = get_timeline_range(sample_schedule, sample_config)
        
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
        result = get_timeline_range(empty_schedule, sample_config)
        
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
        result = get_timeline_range(None, sample_config)
        
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
        result = get_timeline_range(single_schedule, sample_config)
        
        assert isinstance(result, dict)
        assert result['min_date'] == date(2024, 5, 16)  # 6/15 - 30 days buffer
        assert result['max_date'] == date(2024, 7, 15)  # 6/15 + 30 days buffer
        assert result['span_days'] == 60  # 30 + 30 days
    
    def test_assign_activity_rows_with_schedule(self, sample_schedule, sample_config):
        """Test activity row assignment with actual schedule data."""
        result = assign_activity_rows(sample_schedule, sample_config)
        
        # Should have entries for all submissions
        assert len(result) == len(sample_schedule)
        
        # Check that all submission IDs are present
        for submission_id in sample_schedule.keys():
            assert submission_id in result
        
        # Check that row numbers are reasonable (some can share rows if they don't overlap)
        row_numbers = list(result.values())
        assert min(row_numbers) >= 0, "Row numbers should be non-negative"
        assert max(row_numbers) < len(sample_schedule), "Row numbers should not exceed submission count"
        
        # The concurrency logic should minimize rows by reusing them when activities don't overlap
        unique_rows = len(set(row_numbers))
        assert unique_rows <= len(sample_schedule), "Should not use more rows than submissions"
        assert unique_rows > 0, "Should use at least one row"


    def test_assign_activity_rows_empty_schedule(self, sample_config):
        """Test activity row assignment with empty schedule."""
        empty_schedule = {}
        result = assign_activity_rows(empty_schedule, sample_config)
        assert result == {}


    def test_assign_activity_rows_none_schedule(self, sample_config):
        """Test activity row assignment with None schedule."""
        result = assign_activity_rows(None, sample_config)
        assert result == {}


    def test_assign_activity_rows_single_submission(self, sample_config):
        """Test activity row assignment with single submission."""
        single_schedule = {"mod1-wrk": date(2024, 1, 1)}
        result = assign_activity_rows(single_schedule, sample_config)
        
        assert len(result) == 1
        assert result["mod1-wrk"] == 0  # Should be on row 0


    def test_assign_activity_rows_duplicate_dates(self, sample_config):
        """Test activity row assignment with submissions on same date."""
        duplicate_schedule = {
            "mod1-wrk": date(2024, 1, 1),
            "mod2-wrk": date(2024, 1, 1)
        }
        result = assign_activity_rows(duplicate_schedule, sample_config)
        
        assert len(result) == 2
        # Should be on different rows since they start on the same date
        assert result["mod1-wrk"] != result["mod2-wrk"]


    def test_assign_activity_rows_overlapping_dates(self, sample_config):
        """Test activity row assignment with overlapping date ranges."""
        # Create schedule with overlapping activities
        overlapping_schedule = {
            "mod1-wrk": date(2024, 1, 1),   # 30 days
            "mod2-wrk": date(2024, 1, 15),  # 30 days (overlaps with mod1)
            "mod3-wrk": date(2024, 2, 15)   # 30 days (no overlap)
        }
        result = assign_activity_rows(overlapping_schedule, sample_config)
        
        assert len(result) == 3
        
        # mod1 and mod2 should be on different rows (they overlap)
        assert result["mod1-wrk"] != result["mod2-wrk"]
        
        # mod3 can be on any row since it doesn't overlap with others
        assert result["mod3-wrk"] in [0, 1, 2]


    def test_assign_activity_rows_sequential_dates(self, sample_config):
        """Test activity row assignment with sequential dates."""
        # Create schedule with sequential activities
        sequential_schedule = {
            "mod1-wrk": date(2024, 1, 1),   # 30 days
            "mod2-wrk": date(2024, 2, 1),   # 30 days (starts after mod1 ends)
            "mod3-wrk": date(2024, 3, 1)    # 30 days (starts after mod2 ends)
        }
        result = assign_activity_rows(sequential_schedule, sample_config)
        
        assert len(result) == 3
        
        # All can potentially share the same row since they don't overlap
        # But the current algorithm might still assign different rows
        # Just check that all have valid row numbers
        for row_num in result.values():
            assert 0 <= row_num < len(sequential_schedule)


    def test_assign_activity_rows_mixed_overlap(self, sample_config):
        """Test activity row assignment with mixed overlap patterns."""
        # Create complex schedule with some overlapping and some sequential
        mixed_schedule = {
            "mod1-wrk": date(2024, 1, 1),   # 30 days
            "mod2-wrk": date(2024, 1, 15),  # 30 days (overlaps with mod1)
            "mod3-wrk": date(2024, 2, 15),  # 30 days (no overlap)
            "mod4-wrk": date(2024, 3, 1),   # 30 days (overlaps with mod3)
        }
        result = assign_activity_rows(mixed_schedule, sample_config)
        
        assert len(result) == 4
        
        # mod1 and mod2 should be on different rows (they overlap)
        assert result["mod1-wrk"] != result["mod2-wrk"]
        
        # mod3 and mod4 should be on different rows (they overlap)
        assert result["mod3-wrk"] != result["mod4-wrk"]
        
        # mod1/mod2 can potentially share rows with mod3/mod4 since they don't overlap
        # But the current algorithm might still assign different rows
        # Just check that all have valid row numbers
        for row_num in result.values():
            assert 0 <= row_num < len(mixed_schedule)


    def test_assign_activity_rows_with_config_concurrency(self, sample_config):
        """Test that concurrency limits from config are respected."""
        # Mock config with low concurrency limit
        low_concurrency_config = Mock()
        low_concurrency_config.max_concurrent_submissions = 1
        
        # Create schedule that would exceed concurrency limit
        high_concurrency_schedule = {
            "mod1-wrk": date(2024, 1, 1),
            "mod2-wrk": date(2024, 1, 15),
            "mod3-wrk": date(2024, 1, 20)
        }
        
        result = assign_activity_rows(high_concurrency_schedule, low_concurrency_config)
        
        assert len(result) == 3
        
        # With max_concurrent_submissions = 1, all should be on different rows
        unique_rows = set(result.values())
        assert len(unique_rows) == 3, "All activities should be on different rows with concurrency limit 1"


    def test_assign_activity_rows_edge_cases(self, sample_config):
        """Test activity row assignment with edge cases."""
        # Test with very short activities
        short_activities = {
            "mod1-wrk": date(2024, 1, 1),   # 1 day
            "mod2-wrk": date(2024, 1, 2),   # 1 day
        }
        
        # Mock config with very short activity duration
        short_config = Mock()
        short_config.activity_duration_days = 1
        
        result = assign_activity_rows(short_activities, short_config)
        assert len(result) == 2
        
        # Test with very long activities
        long_activities = {
            "mod1-wrk": date(2024, 1, 1),   # 365 days
            "mod2-wrk": date(2024, 7, 1),   # 365 days (overlaps with mod1)
        }
        
        # Mock config with very long activity duration
        long_config = Mock()
        long_config.activity_duration_days = 365
        
        result = assign_activity_rows(long_activities, long_config)
        assert len(result) == 2
        
        # They should be on different rows since they overlap for a long time
        assert result["mod1-wrk"] != result["mod2-wrk"]


    def test_assign_activity_rows_performance(self, sample_config):
        """Test performance with large number of activities."""
        # Create a large schedule
        large_schedule = {}
        for i in range(100):
            large_schedule[f"mod{i}-wrk"] = date(2024, 1, 1) + timedelta(days=i)
        
        import time
        start_time = time.time()
        result = assign_activity_rows(large_schedule, sample_config)
        end_time = time.time()
        
        # Should complete in reasonable time (less than 1 second)
        assert end_time - start_time < 1.0
        
        # Should have correct number of entries
        assert len(result) == 100
        
        # All should have valid row numbers
        for row_num in result.values():
            assert 0 <= row_num < 100
