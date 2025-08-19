"""Tests for schedule analytics functions."""

from datetime import date
from pathlib import Path
from typing import Dict, List, Any

import pytest

from src.core.models import Config, ScheduleMetrics, Schedule, Interval
from src.analytics import generate_schedule_summary


class TestGenerateScheduleSummary:
    """Test the generate_schedule_summary function."""

    def test_generate_schedule_summary_empty(self, empty_schedule, empty_config) -> None:
        """Test generate schedule summary with empty schedule."""
        result = generate_schedule_summary(empty_schedule, empty_config)
        
        assert isinstance(result, ScheduleMetrics)
        assert result.scheduled_count == 0
        assert result.submission_count == 0
        assert result.completion_rate == 0.0
        assert result.makespan == 0
        assert result.total_penalty == 0.0
        assert result.quality_score == 0.0
        assert result.efficiency_score == 0.0

    def test_generate_schedule_summary_with_papers(self, sample_schedule, sample_config) -> None:
        """Test generate schedule summary with papers."""
        # Convert the old schedule format to new Schedule format
        schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2024, 12, 1), end_date=date(2024, 12, 31)),
            "paper1-pap": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 4, 15)),
            "mod2-wrk": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 31)),
            "paper2-pap": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 5, 1)),
            "poster1": Interval(start_date=date(2025, 1, 30), end_date=date(2025, 2, 28))
        })
        
        result = generate_schedule_summary(schedule, sample_config)
        
        assert isinstance(result, ScheduleMetrics)
        assert result.scheduled_count == 5
        assert result.submission_count == 5
        assert result.completion_rate == 100.0
        assert result.makespan > 0
        assert result.total_penalty >= 0.0
        assert result.quality_score >= 0.0
        assert result.efficiency_score >= 0.0

    def test_generate_schedule_summary_partial(self, sample_config) -> None:
        """Test generate schedule summary with partial schedule."""
        # Create a partial schedule with only some submissions
        schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2024, 12, 1), end_date=date(2024, 12, 31)),
            "paper1-pap": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 4, 15))
        })
        
        result = generate_schedule_summary(schedule, sample_config)
        
        assert isinstance(result, ScheduleMetrics)
        assert result.scheduled_count == 2
        assert result.submission_count == 5  # Total submissions in config
        assert result.completion_rate == 40.0  # 2/5 = 40%
        assert result.makespan > 0
        assert len(result.missing_submissions) == 3  # 3 missing submissions

    def test_generate_schedule_summary_metrics_structure(self, sample_schedule, sample_config) -> None:
        """Test that the generated metrics have the correct structure."""
        # Convert to new Schedule format
        schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2024, 12, 1), end_date=date(2024, 12, 31)),
            "paper1-pap": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 4, 15))
        })
        
        result = generate_schedule_summary(schedule, sample_config)
        
        # Check all required fields exist
        assert hasattr(result, 'makespan')
        assert hasattr(result, 'total_penalty')
        assert hasattr(result, 'compliance_rate')
        assert hasattr(result, 'quality_score')
        assert hasattr(result, 'avg_utilization')
        assert hasattr(result, 'peak_utilization')
        assert hasattr(result, 'utilization_rate')
        assert hasattr(result, 'efficiency_score')
        assert hasattr(result, 'duration_days')
        assert hasattr(result, 'avg_daily_load')
        assert hasattr(result, 'timeline_efficiency')
        assert hasattr(result, 'monthly_distribution')
        assert hasattr(result, 'quarterly_distribution')
        assert hasattr(result, 'yearly_distribution')
        assert hasattr(result, 'submission_count')
        assert hasattr(result, 'scheduled_count')
        assert hasattr(result, 'completion_rate')
        assert hasattr(result, 'type_counts')
        assert hasattr(result, 'type_percentages')
        assert hasattr(result, 'missing_submissions')
        assert hasattr(result, 'start_date')
        assert hasattr(result, 'end_date')

    def test_generate_schedule_summary_distribution_data(self, sample_config) -> None:
        """Test that distribution data is properly calculated."""
        schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2024, 12, 1), end_date=date(2024, 12, 31)),
            "paper1-pap": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 4, 15)),
            "mod2-wrk": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 28))
        })
        
        result = generate_schedule_summary(schedule, sample_config)
        
        # Check monthly distribution
        assert "2024-12" in result.monthly_distribution
        assert "2025-01" in result.monthly_distribution
        assert "2025-02" in result.monthly_distribution
        assert result.monthly_distribution["2024-12"] == 1  # mod1-wrk
        assert result.monthly_distribution["2025-01"] == 1  # paper1-pap
        assert result.monthly_distribution["2025-02"] == 2  # mod2-wrk + paper1-pap (ongoing)
        
        # Check quarterly distribution
        assert "2024-Q4" in result.quarterly_distribution
        assert "2025-Q1" in result.quarterly_distribution
        
        # Check yearly distribution
        assert "2024" in result.yearly_distribution
        assert "2025" in result.yearly_distribution

    def test_generate_schedule_summary_type_breakdown(self, sample_config) -> None:
        """Test that submission type breakdown is properly calculated."""
        schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2024, 12, 1), end_date=date(2024, 12, 31)),
            "paper1-pap": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 4, 15)),
            "poster1": Interval(start_date=date(2025, 1, 30), end_date=date(2025, 2, 28))
        })
        
        result = generate_schedule_summary(schedule, sample_config)
        
        # Check type counts
        assert result.type_counts["abstract"] == 1  # mod1-wrk
        assert result.type_counts["paper"] == 1     # paper1-pap
        assert result.type_counts["poster"] == 1    # poster1
        
        # Check type percentages
        total = 3
        assert result.type_percentages["abstract"] == pytest.approx(33.33, abs=0.01)
        assert result.type_percentages["paper"] == pytest.approx(33.33, abs=0.01)
        assert result.type_percentages["poster"] == pytest.approx(33.33, abs=0.01)

    def test_generate_schedule_summary_missing_submissions(self, sample_config) -> None:
        """Test that missing submissions are properly identified."""
        schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2024, 12, 1), end_date=date(2024, 12, 31))
        })
        
        result = generate_schedule_summary(schedule, sample_config)
        
        # Should have 4 missing submissions (5 total - 1 scheduled)
        assert len(result.missing_submissions) == 4
        
        # Check that missing submissions have required fields
        for missing in result.missing_submissions:
            assert "id" in missing
            assert "title" in missing
            assert "kind" in missing
            assert "conference_id" in missing
        
        # Check specific missing submissions
        missing_ids = [m["id"] for m in result.missing_submissions]
        assert "paper1-pap" in missing_ids
        assert "mod2-wrk" in missing_ids
        assert "paper2-pap" in missing_ids
        assert "poster1" in missing_ids
