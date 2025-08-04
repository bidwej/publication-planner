"""Tests for makespan calculation metrics."""

import pytest
from datetime import date, timedelta
from metrics.makespan import calculate_makespan, calculate_parallel_makespan, get_makespan_breakdown
from core.types import SubmissionType


class TestCalculateMakespan:
    """Test the calculate_makespan function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test makespan calculation with empty schedule."""
        makespan = calculate_makespan(empty_schedule, config)
        assert makespan == 0
    
    def test_single_submission(self, config):
        """Test makespan calculation with single submission."""
        schedule = {"test-pap": date(2025, 1, 1)}
        makespan = calculate_makespan(schedule, config)
        assert makespan >= 0
    
    def test_multiple_submissions(self, config):
        """Test makespan calculation with multiple submissions."""
        # Create a test schedule with multiple submissions
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 15),
            "test3": date(2025, 1, 30)
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "test1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "test2": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})(),
            "test3": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        makespan = calculate_makespan(schedule, config)
        assert makespan > 0
        assert isinstance(makespan, int)
    
    def test_makespan_with_paper_duration(self, config):
        """Test makespan calculation considering paper duration."""
        # Create a schedule with papers that have duration
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 15),
            "abstract1": date(2025, 1, 1)
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "paper1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "paper2": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "abstract1": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})()
        }
        
        makespan = calculate_makespan(schedule, config)
        assert makespan > 0
        
        # Makespan should account for paper duration
        # If papers have 60 days duration, makespan should be at least 60 days
        if config.min_paper_lead_time_days > 0:
            assert makespan >= config.min_paper_lead_time_days
    
    def test_makespan_date_range(self, config):
        """Test that makespan represents actual date range."""
        # Create a test schedule
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 15),
            "test3": date(2025, 1, 30)
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "test1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "test2": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})(),
            "test3": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        makespan = calculate_makespan(schedule, config)
        
        # Get actual date range
        start_date = min(schedule.values())
        end_dates = []
        
        for submission_id, start in schedule.items():
            submission = config.submissions_dict.get(submission_id)
            if submission and submission.kind == SubmissionType.PAPER:
                end_date = start + timedelta(days=config.min_paper_lead_time_days)
            else:
                end_date = start
            end_dates.append(end_date)
        
        actual_makespan = (max(end_dates) - start_date).days
        assert makespan == actual_makespan


class TestCalculateParallelMakespan:
    """Test the calculate_parallel_makespan function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test parallel makespan with empty schedule."""
        parallel_makespan = calculate_parallel_makespan(empty_schedule, config)
        assert parallel_makespan == 0
    
    def test_single_submission(self, config):
        """Test parallel makespan with single submission."""
        schedule = {"test-pap": date(2025, 1, 1)}
        parallel_makespan = calculate_parallel_makespan(schedule, config)
        assert parallel_makespan >= 0
    
    def test_multiple_submissions(self, config):
        """Test parallel makespan calculation with multiple submissions."""
        # Create a test schedule with multiple submissions
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 15),
            "test3": date(2025, 1, 30)
        }
        
        # Mock submissions_dict for testing with papers that have duration
        config.submissions_dict = {
            "test1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "test2": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})(),
            "test3": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        parallel_makespan = calculate_parallel_makespan(schedule, config)
        # Should be positive since we have papers with duration
        assert parallel_makespan > 0
        assert isinstance(parallel_makespan, int)
    
    def test_parallel_vs_sequential_makespan(self, config):
        """Test that parallel makespan is less than or equal to sequential."""
        # Create a test schedule
        schedule = {
            "test1": date(2025, 1, 1),
            "test2": date(2025, 1, 15),
            "test3": date(2025, 1, 30)
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "test1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "test2": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})(),
            "test3": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        sequential_makespan = calculate_makespan(schedule, config)
        parallel_makespan = calculate_parallel_makespan(schedule, config)
        
        # Parallel makespan should be less than or equal to sequential
        assert parallel_makespan <= sequential_makespan
    
    def test_parallel_makespan_with_concurrency(self, config):
        """Test parallel makespan with concurrency constraints."""
        # Create a schedule with overlapping submissions
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 1),  # Same start date
            "paper3": date(2025, 1, 1)   # Same start date
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "paper1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "paper2": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "paper3": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        parallel_makespan = calculate_parallel_makespan(schedule, config)
        assert parallel_makespan > 0
        
        # With 3 papers starting on same day, parallel makespan should be reasonable
        # The calculation is: total_papers / max_daily_load
        # With 3 papers and max_load of 3, we get 3/3 = 1
        # But we should have some minimum duration
        assert parallel_makespan >= 1


class TestGetMakespanBreakdown:
    """Test the get_makespan_breakdown function."""
    
    def test_empty_schedule(self, empty_schedule, config):
        """Test breakdown with empty schedule."""
        breakdown = get_makespan_breakdown(empty_schedule, config)
        assert breakdown["abstracts"] == 0
        assert breakdown["papers"] == 0
        assert breakdown["total"] == 0
    
    def test_schedule_with_abstracts_only(self, config):
        """Test breakdown with only abstracts."""
        schedule = {
            "abstract1": date(2025, 1, 1),
            "abstract2": date(2025, 1, 15)
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "abstract1": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})(),
            "abstract2": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})()
        }
        
        breakdown = get_makespan_breakdown(schedule, config)
        assert breakdown["abstracts"] == 14  # 15 - 1 = 14 days
        assert breakdown["papers"] == 0
        assert breakdown["total"] == 14
    
    def test_schedule_with_papers_only(self, config):
        """Test breakdown with only papers."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 15)
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "paper1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "paper2": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        breakdown = get_makespan_breakdown(schedule, config)
        assert breakdown["abstracts"] == 0
        assert breakdown["papers"] >= 14  # Should account for paper duration
        assert breakdown["total"] >= 14
    
    def test_schedule_with_mixed_submissions(self, config):
        """Test breakdown with mixed abstracts and papers."""
        schedule = {
            "abstract1": date(2025, 1, 1),
            "paper1": date(2025, 1, 15),
            "abstract2": date(2025, 1, 30)
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "abstract1": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})(),
            "paper1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "abstract2": type('obj', (object,), {'kind': SubmissionType.ABSTRACT})()
        }
        
        breakdown = get_makespan_breakdown(schedule, config)
        assert breakdown["abstracts"] >= 29  # 30 - 1 = 29 days
        assert breakdown["papers"] >= 0  # Paper duration
        assert breakdown["total"] >= 29
    
    def test_breakdown_consistency(self, sample_schedule, config):
        """Test that breakdown is consistent with total makespan."""
        if not sample_schedule:
            pytest.skip("No sample schedule available")
        
        breakdown = get_makespan_breakdown(sample_schedule, config)
        total_makespan = calculate_makespan(sample_schedule, config)
        
        # Total should match the breakdown total
        assert breakdown["total"] == total_makespan
        
        # Individual components should be reasonable
        assert breakdown["abstracts"] >= 0
        assert breakdown["papers"] >= 0
        
        # Total should be at least as large as the largest component
        max_component = max(breakdown["abstracts"], breakdown["papers"])
        assert breakdown["total"] >= max_component


class TestMakespanEdgeCases:
    """Test edge cases for makespan calculations."""
    
    def test_submission_not_in_config(self, config):
        """Test makespan calculation with submission not in config."""
        schedule = {"unknown-submission": date(2025, 1, 1)}
        makespan = calculate_makespan(schedule, config)
        assert makespan == 0  # Should handle gracefully
    
    def test_very_long_schedule(self, config):
        """Test makespan calculation with very long schedule."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2026, 12, 31)  # Very far in future
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "paper1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "paper2": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        makespan = calculate_makespan(schedule, config)
        assert makespan > 365  # Should be over a year
        
        parallel_makespan = calculate_parallel_makespan(schedule, config)
        assert parallel_makespan > 0
    
    def test_overlapping_submissions(self, config):
        """Test makespan calculation with overlapping submissions."""
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 1),  # Same start
            "paper3": date(2025, 1, 1)   # Same start
        }
        
        # Mock submissions_dict for testing
        config.submissions_dict = {
            "paper1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "paper2": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
            "paper3": type('obj', (object,), {'kind': SubmissionType.PAPER})()
        }
        
        makespan = calculate_makespan(schedule, config)
        parallel_makespan = calculate_parallel_makespan(schedule, config)
        
        assert makespan > 0
        assert parallel_makespan > 0
        assert parallel_makespan <= makespan
    
    def test_zero_duration_papers(self, config):
        """Test makespan calculation with zero duration papers."""
        # Temporarily set paper duration to 0
        original_duration = config.min_paper_lead_time_days
        config.min_paper_lead_time_days = 0
        
        try:
            schedule = {
                "paper1": date(2025, 1, 1),
                "paper2": date(2025, 1, 15)
            }
            
            # Mock submissions_dict for testing
            config.submissions_dict = {
                "paper1": type('obj', (object,), {'kind': SubmissionType.PAPER})(),
                "paper2": type('obj', (object,), {'kind': SubmissionType.PAPER})()
            }
            
            makespan = calculate_makespan(schedule, config)
            assert makespan == 14  # 15 - 1 = 14 days
            
            breakdown = get_makespan_breakdown(schedule, config)
            assert breakdown["papers"] == 14
        finally:
            config.min_paper_lead_time_days = original_duration 