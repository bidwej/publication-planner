"""Tests for analytics functions."""

import pytest
from datetime import date, timedelta
from src.core.models import SubmissionType
from src.output.analytics import analyze_schedule_completeness, analyze_schedule_distribution, analyze_submission_types, analyze_timeline, analyze_resources


class TestAnalyzeScheduleCompleteness:
    """Test the analyze_schedule_completeness function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test completeness analysis with empty schedule."""
        analysis = analyze_schedule_completeness(empty_schedule, config)
        assert analysis.scheduled_count == 0
        assert analysis.total_count >= 0  # Could be 0 if no submissions in config
        assert analysis.completion_rate == 0.0
        assert len(analysis.missing_submissions) >= 0  # Could be 0 if no submissions
    
    def test_complete_schedule(self, sample_schedule, config):
        """Test completeness analysis with complete schedule."""
        analysis = analyze_schedule_completeness(sample_schedule, config)
        assert analysis.scheduled_count > 0
        assert analysis.total_count > 0
        assert analysis.completion_rate > 0.0
        assert analysis.completion_rate <= 100.0
    
    def test_partial_schedule(self, config):
        """Test completeness analysis with partial schedule."""
        # Create a partial schedule
        schedule = {"test-pap": date(2025, 1, 1)}
        analysis = analyze_schedule_completeness(schedule, config)
        assert analysis.scheduled_count == 1
        assert analysis.total_count > 1
        assert analysis.completion_rate < 100.0
        assert len(analysis.missing_submissions) > 0


class TestAnalyzeScheduleDistribution:
    """Test the analyze_schedule_distribution function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test distribution analysis with empty schedule."""
        analysis = analyze_schedule_distribution(empty_schedule, config)
        assert len(analysis.monthly_distribution) == 0
        assert len(analysis.quarterly_distribution) == 0
        assert len(analysis.yearly_distribution) == 0
    
    def test_single_submission(self, config):
        """Test distribution analysis with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        analysis = analyze_schedule_distribution(schedule, config)
        assert len(analysis.monthly_distribution) == 1
        assert "2025-01" in analysis.monthly_distribution
        assert analysis.monthly_distribution["2025-01"] == 1
    
    def test_multiple_submissions(self, config):
        """Test distribution analysis with multiple submissions."""
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 15),
            "test3": date(2025, 2, 1)
        }
        analysis = analyze_schedule_distribution(schedule, config)
        assert len(analysis.monthly_distribution) == 2
        assert analysis.monthly_distribution["2025-01"] == 2
        assert analysis.monthly_distribution["2025-02"] == 1


class TestAnalyzeSubmissionTypes:
    """Test the analyze_submission_types function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test type analysis with empty schedule."""
        analysis = analyze_submission_types(empty_schedule, config)
        assert len(analysis.type_counts) == 0
        assert len(analysis.type_percentages) == 0
    
    def test_mixed_submissions(self, config):
        """Test type analysis with mixed submission types."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "abstract1": date(2025, 1, 15),
            "paper2": date(2025, 2, 1)
        }
        analysis = analyze_submission_types(schedule, config)
        assert len(analysis.type_counts) > 0
        assert len(analysis.type_percentages) > 0


class TestAnalyzeTimeline:
    """Test the analyze_timeline function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test timeline analysis with empty schedule."""
        analysis = analyze_timeline(empty_schedule, config)
        assert analysis.start_date is None
        assert analysis.end_date is None
        assert analysis.duration_days == 0
    
    def test_single_submission(self, config):
        """Test timeline analysis with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        analysis = analyze_timeline(schedule, config)
        assert analysis.start_date == date(2025, 1, 15)
        assert analysis.end_date == date(2025, 1, 15)
        assert analysis.duration_days == 0
    
    def test_multiple_submissions(self, config):
        """Test timeline analysis with multiple submissions."""
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 15),
            "test3": date(2025, 2, 1)
        }
        analysis = analyze_timeline(schedule, config)
        assert analysis.start_date == date(2025, 1, 1)
        assert analysis.end_date == date(2025, 2, 1)
        assert analysis.duration_days == 31


class TestAnalyzeResources:
    """Test the analyze_resources function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test resource analysis with empty schedule."""
        analysis = analyze_resources(empty_schedule, config)
        assert analysis.peak_load == 0
        assert analysis.avg_load == 0.0
    
    def test_single_submission(self, config):
        """Test resource analysis with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        analysis = analyze_resources(schedule, config)
        assert analysis.peak_load >= 0
        assert analysis.avg_load >= 0.0
    
    def test_multiple_submissions(self, config):
        """Test resource analysis with multiple submissions."""
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 15),
            "test3": date(2025, 2, 1)
        }
        analysis = analyze_resources(schedule, config)
        assert analysis.peak_load >= 0
        assert analysis.avg_load >= 0.0
        assert len(analysis.utilization_pattern) > 0 