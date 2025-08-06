"""Tests for output analytics module."""

from datetime import date
from output.analytics import (
    analyze_schedule_completeness, analyze_schedule_distribution,
    analyze_submission_types, analyze_timeline, analyze_resources
)


class TestAnalyzeScheduleCompleteness:
    """Test schedule completeness analysis."""
    
    def test_empty_schedule(self, config):
        """Test completeness analysis with empty schedule."""
        schedule = {}
        analysis = analyze_schedule_completeness(schedule, config)
        
        assert analysis.scheduled_count == 0
        assert analysis.total_count >= 0
        assert analysis.completion_rate == 0.0
        assert isinstance(analysis.missing_submissions, list)
        assert isinstance(analysis.summary, str)
    
    def test_partial_schedule(self, config):
        """Test completeness analysis with partial schedule."""
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15)
        }
        analysis = analyze_schedule_completeness(schedule, config)
        
        assert analysis.scheduled_count == 2
        assert analysis.total_count >= 2
        assert analysis.completion_rate >= 0.0
        assert isinstance(analysis.missing_submissions, list)
        assert isinstance(analysis.summary, str)
    
    def test_complete_schedule(self, config):
        """Test completeness analysis with complete schedule."""
        # Create a schedule with all submissions
        all_submissions = {sub.id: date(2025, 1, 1) for sub in config.submissions}
        analysis = analyze_schedule_completeness(all_submissions, config)
        
        assert analysis.scheduled_count == len(config.submissions)
        assert analysis.total_count == len(config.submissions)
        assert analysis.completion_rate == 100.0
        assert len(analysis.missing_submissions) == 0
        assert isinstance(analysis.summary, str)


class TestAnalyzeScheduleDistribution:
    """Test schedule distribution analysis."""
    
    def test_empty_schedule(self, config):
        """Test distribution analysis with empty schedule."""
        schedule = {}
        analysis = analyze_schedule_distribution(schedule, config)
        
        assert isinstance(analysis.monthly_distribution, dict)
        assert isinstance(analysis.quarterly_distribution, dict)
        assert isinstance(analysis.yearly_distribution, dict)
        assert isinstance(analysis.summary, str)
    
    def test_single_submission(self, config):
        """Test distribution analysis with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        analysis = analyze_schedule_distribution(schedule, config)
        
        assert isinstance(analysis.monthly_distribution, dict)
        assert isinstance(analysis.quarterly_distribution, dict)
        assert isinstance(analysis.yearly_distribution, dict)
        assert isinstance(analysis.summary, str)
    
    def test_multiple_submissions(self, config):
        """Test distribution analysis with multiple submissions."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 15),
            "paper3": date(2025, 6, 1),
            "paper4": date(2025, 12, 1)
        }
        analysis = analyze_schedule_distribution(schedule, config)
        
        assert isinstance(analysis.monthly_distribution, dict)
        assert isinstance(analysis.quarterly_distribution, dict)
        assert isinstance(analysis.yearly_distribution, dict)
        assert isinstance(analysis.summary, str)
        
        # Should have entries for different months/quarters/years
        assert len(analysis.monthly_distribution) > 0
        assert len(analysis.quarterly_distribution) > 0
        assert len(analysis.yearly_distribution) > 0


class TestAnalyzeSubmissionTypes:
    """Test submission type analysis."""
    
    def test_empty_schedule(self, config):
        """Test type analysis with empty schedule."""
        schedule = {}
        analysis = analyze_submission_types(schedule, config)
        
        assert isinstance(analysis.type_counts, dict)
        assert isinstance(analysis.type_percentages, dict)
        assert isinstance(analysis.summary, str)
    
    def test_single_submission(self, config):
        """Test type analysis with single submission."""
        schedule = {"test-pap": date(2025, 1, 1)}
        analysis = analyze_submission_types(schedule, config)
        
        assert isinstance(analysis.type_counts, dict)
        assert isinstance(analysis.type_percentages, dict)
        assert isinstance(analysis.summary, str)
    
    def test_mixed_submissions(self, config):
        """Test type analysis with mixed submission types."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "abstract1": date(2025, 1, 15),
            "paper2": date(2025, 2, 1)
        }
        analysis = analyze_submission_types(schedule, config)
        
        assert isinstance(analysis.type_counts, dict)
        assert isinstance(analysis.type_percentages, dict)
        assert isinstance(analysis.summary, str)
    
    def test_all_papers(self, config):
        """Test type analysis with all papers."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 2, 1),
            "paper3": date(2025, 3, 1)
        }
        analysis = analyze_submission_types(schedule, config)
        
        assert isinstance(analysis.type_counts, dict)
        assert isinstance(analysis.type_percentages, dict)
        assert isinstance(analysis.summary, str)


class TestAnalyzeTimeline:
    """Test timeline analysis."""
    
    def test_empty_schedule(self, config):
        """Test timeline analysis with empty schedule."""
        schedule = {}
        analysis = analyze_timeline(schedule, config)
        
        assert analysis.start_date is None
        assert analysis.end_date is None
        assert analysis.duration_days == 0
        assert analysis.avg_submissions_per_month >= 0.0
        assert isinstance(analysis.summary, str)
    
    def test_single_submission(self, config):
        """Test timeline analysis with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        analysis = analyze_timeline(schedule, config)
        
        assert analysis.start_date == date(2025, 1, 15)
        assert analysis.end_date == date(2025, 1, 15)
        assert analysis.duration_days == 1
        assert analysis.avg_submissions_per_month >= 0.0
        assert isinstance(analysis.summary, str)
    
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
        assert analysis.duration_days >= 0
        assert analysis.avg_submissions_per_month >= 0.0
        assert isinstance(analysis.summary, str)
    
    def test_spread_out_schedule(self, config):
        """Test timeline analysis with spread out schedule."""
        schedule = {
            "jan": date(2025, 1, 1),
            "mar": date(2025, 3, 1),
            "jun": date(2025, 6, 1),
            "dec": date(2025, 12, 1)
        }
        analysis = analyze_timeline(schedule, config)
        
        assert analysis.start_date == date(2025, 1, 1)
        assert analysis.end_date == date(2025, 12, 1)
        assert analysis.duration_days >= 0
        assert analysis.avg_submissions_per_month >= 0.0
        assert isinstance(analysis.summary, str)


class TestAnalyzeResources:
    """Test resource analysis."""
    
    def test_empty_schedule(self, config):
        """Test resource analysis with empty schedule."""
        schedule = {}
        analysis = analyze_resources(schedule, config)
        
        assert analysis.peak_load == 0
        assert analysis.avg_load == 0.0
        assert isinstance(analysis.utilization_pattern, dict)
        assert isinstance(analysis.summary, str)
    
    def test_single_submission(self, config):
        """Test resource analysis with single submission."""
        schedule = {"test-pap": date(2025, 1, 15)}
        analysis = analyze_resources(schedule, config)
        
        assert analysis.peak_load >= 0
        assert analysis.avg_load >= 0.0
        assert isinstance(analysis.utilization_pattern, dict)
        assert isinstance(analysis.summary, str)
    
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
        assert isinstance(analysis.utilization_pattern, dict)
        assert isinstance(analysis.summary, str)
    
    def test_concurrent_submissions(self, config):
        """Test resource analysis with concurrent submissions."""
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 1),  # Same day
            "test3": date(2025, 1, 1)   # Same day
        }
        analysis = analyze_resources(schedule, config)
        
        assert analysis.peak_load >= 0
        assert analysis.avg_load >= 0.0
        assert isinstance(analysis.utilization_pattern, dict)
        assert isinstance(analysis.summary, str)
    
    def test_spread_out_submissions(self, config):
        """Test resource analysis with spread out submissions."""
        schedule = {
            "jan": date(2025, 1, 1),
            "mar": date(2025, 3, 1),
            "jun": date(2025, 6, 1),
            "dec": date(2025, 12, 1)
        }
        analysis = analyze_resources(schedule, config)
        
        assert analysis.peak_load >= 0
        assert analysis.avg_load >= 0.0
        assert isinstance(analysis.utilization_pattern, dict)
        assert isinstance(analysis.summary, str)
