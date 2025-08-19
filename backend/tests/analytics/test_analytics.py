"""Tests for analytics functions."""

from datetime import date
from src.analytics import generate_schedule_summary
from typing import Dict, List, Any, Optional
from src.core.models import Schedule, Config, ScheduleMetrics, Interval


class TestGenerateScheduleSummary:
    """Test the generate_schedule_summary function."""
    
    def test_empty_schedule(self, empty_schedule, config) -> None:
        """Test summary generation with empty schedule."""
        metrics = generate_schedule_summary(empty_schedule, config)
        assert isinstance(metrics, ScheduleMetrics)
        assert metrics.scheduled_count == 0
        assert metrics.submission_count >= 0  # Could be 0 if no submissions in config
        assert metrics.completion_rate == 0.0
        assert len(metrics.missing_submissions) >= 0  # Could be 0 if no submissions
    
    def test_complete_schedule(self, sample_schedule, config) -> None:
        """Test summary generation with complete schedule."""
        metrics = generate_schedule_summary(sample_schedule, config)
        assert isinstance(metrics, ScheduleMetrics)
        assert metrics.scheduled_count > 0
        assert metrics.submission_count > 0
        assert metrics.completion_rate > 0.0
        assert metrics.completion_rate <= 100.0
    
    def test_partial_schedule(self, config) -> None:
        """Test summary generation with partial schedule."""
        # Create a partial schedule
        schedule = Schedule(intervals={
            "test-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31))
        })
        metrics = generate_schedule_summary(schedule, config)
        assert isinstance(metrics, ScheduleMetrics)
        assert metrics.scheduled_count == 1
        assert metrics.submission_count > 1
        assert metrics.completion_rate < 100.0
        assert len(metrics.missing_submissions) > 0


class TestScheduleMetricsStructure:
    """Test the ScheduleMetrics model structure."""
    
    def test_metrics_fields(self, sample_schedule, config) -> None:
        """Test that ScheduleMetrics has all expected fields."""
        metrics = generate_schedule_summary(sample_schedule, config)
        
        # Core performance metrics
        assert hasattr(metrics, 'makespan')
        assert hasattr(metrics, 'total_penalty')
        assert hasattr(metrics, 'compliance_rate')
        assert hasattr(metrics, 'quality_score')
        
        # Resource utilization metrics
        assert hasattr(metrics, 'avg_utilization')
        assert hasattr(metrics, 'peak_utilization')
        assert hasattr(metrics, 'utilization_rate')
        assert hasattr(metrics, 'efficiency_score')
        
        # Timeline metrics
        assert hasattr(metrics, 'duration_days')
        assert hasattr(metrics, 'avg_daily_load')
        assert hasattr(metrics, 'timeline_efficiency')
        
        # Distribution data
        assert hasattr(metrics, 'monthly_distribution')
        assert hasattr(metrics, 'quarterly_distribution')
        assert hasattr(metrics, 'yearly_distribution')
        
        # Submission breakdown
        assert hasattr(metrics, 'submission_count')
        assert hasattr(metrics, 'scheduled_count')
        assert hasattr(metrics, 'completion_rate')
        assert hasattr(metrics, 'type_counts')
        assert hasattr(metrics, 'type_percentages')
        
        # Missing items
        assert hasattr(metrics, 'missing_submissions')
        
        # Dates
        assert hasattr(metrics, 'start_date')
        assert hasattr(metrics, 'end_date')
    
    def test_metrics_data_types(self, sample_schedule, config) -> None:
        """Test that ScheduleMetrics fields have correct data types."""
        metrics = generate_schedule_summary(sample_schedule, config)
        
        # Check numeric types
        assert isinstance(metrics.makespan, int)
        assert isinstance(metrics.total_penalty, float)
        assert isinstance(metrics.compliance_rate, float)
        assert isinstance(metrics.quality_score, float)
        assert isinstance(metrics.avg_utilization, float)
        assert isinstance(metrics.peak_utilization, int)
        assert isinstance(metrics.utilization_rate, float)
        assert isinstance(metrics.efficiency_score, float)
        assert isinstance(metrics.duration_days, int)
        assert isinstance(metrics.avg_daily_load, float)
        assert isinstance(metrics.timeline_efficiency, float)
        assert isinstance(metrics.submission_count, int)
        assert isinstance(metrics.scheduled_count, int)
        assert isinstance(metrics.completion_rate, float)
        
        # Check dict types
        assert isinstance(metrics.monthly_distribution, dict)
        assert isinstance(metrics.quarterly_distribution, dict)
        assert isinstance(metrics.yearly_distribution, dict)
        assert isinstance(metrics.type_counts, dict)
        assert isinstance(metrics.type_percentages, dict)
        
        # Check list types
        assert isinstance(metrics.missing_submissions, list)
        
        # Check optional date types
        if metrics.start_date is not None:
            assert isinstance(metrics.start_date, date)
        if metrics.end_date is not None:
            assert isinstance(metrics.end_date, date) 
