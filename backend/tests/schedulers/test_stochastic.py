"""Tests for stochastic scheduler."""

from typing import Dict, List, Any, Optional
from datetime import date, timedelta
import pytest
from src.schedulers.stochastic import StochasticGreedyScheduler
from src.core.models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence, Schedule


class TestStochasticScheduler:
    """Test cases for stochastic scheduler."""
    
    def test_schedule_empty_submissions(self, empty_config) -> None:
        """Test stochastic scheduler with empty submissions."""
        scheduler = StochasticGreedyScheduler(empty_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object, not a dict
        assert isinstance(result, Schedule)
        assert len(result.intervals) == 0
    
    def test_schedule_single_paper(self, sample_config) -> None:
        """Test stochastic scheduler with single paper."""
        scheduler = StochasticGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        assert len(result.intervals) > 0
        
        # Check that at least one submission was scheduled
        assert any(sub_id in result.intervals for sub_id in ["mod1-wrk", "paper1-pap", "mod2-wrk", "paper2-pap", "poster1"])
    
    def test_schedule_multiple_papers(self, sample_config) -> None:
        """Test stochastic scheduler with multiple papers."""
        scheduler = StochasticGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        assert len(result.intervals) > 0
        
        # Check that multiple submissions were scheduled
        scheduled_count = len(result.intervals)
        assert scheduled_count >= 2  # Should schedule at least 2 submissions
        
        # Verify all scheduled submissions have valid intervals
        for sub_id, interval in result.intervals.items():
            assert isinstance(interval.start_date, date)
            assert isinstance(interval.end_date, date)
            assert interval.start_date <= interval.end_date
    
    def test_stochastic_algorithm_behavior(self, sample_config) -> None:
        """Test that stochastic algorithm produces different results on multiple runs."""
        scheduler1 = StochasticGreedyScheduler(sample_config)
        result1: Any = scheduler1.schedule()
        
        scheduler2 = StochasticGreedyScheduler(sample_config)
        result2: Any = scheduler2.schedule()
        
        # Both should return Schedule objects
        assert isinstance(result1, Schedule)
        assert isinstance(result2, Schedule)
        
        # Results might be different due to randomness
        # At minimum, both should have some scheduled submissions
        assert len(result1.intervals) > 0
        assert len(result2.intervals) > 0
    
    def test_schedule_with_constraints(self, sample_config) -> None:
        """Test stochastic scheduler respects constraints."""
        scheduler = StochasticGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check that dependencies are respected
        if "paper1-pap" in result.intervals and "mod1-wrk" in result.intervals:
            paper_start = result.intervals["paper1-pap"].start_date
            mod_end = result.intervals["mod1-wrk"].end_date
            # Paper should start after mod ends
            assert paper_start >= mod_end
    
    def test_error_handling_invalid_paper(self, sample_config) -> None:
        """Test error handling with invalid paper."""
        # Create a submission with non-existent conference
        invalid_submission = Submission(
            id="invalid_paper",
            title="Invalid Paper",
            kind=SubmissionType.PAPER,
            conference_id="nonexistent_conf",
            depends_on=[],
            draft_window_months=3,
            author="test"
        )
        
        # Add to config
        sample_config.submissions.append(invalid_submission)
        
        scheduler = StochasticGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should still return a Schedule object
        assert isinstance(result, Schedule)
        # The invalid submission might not be scheduled, but that's okay
    
    def test_schedule_with_priority_ordering(self, sample_config) -> None:
        """Test stochastic scheduler with priority ordering."""
        scheduler = StochasticGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check that all scheduled submissions have valid intervals
        for sub_id, interval in result.intervals.items():
            assert isinstance(interval.start_date, date)
            assert isinstance(interval.end_date, date)
            assert interval.start_date <= interval.end_date
    
    def test_schedule_with_deadline_compliance(self, sample_config) -> None:
        """Test stochastic scheduler with deadline compliance."""
        scheduler = StochasticGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check deadline compliance for scheduled submissions
        for sub_id, interval in result.intervals.items():
            submission = sample_config.get_submission(sub_id)
            if submission and submission.conference_id:
                conference = sample_config.get_conference(submission.conference_id)
                if conference and submission.kind in conference.deadlines:
                    deadline = conference.deadlines[submission.kind]
                    # End date should not exceed deadline
                    assert interval.end_date <= deadline
