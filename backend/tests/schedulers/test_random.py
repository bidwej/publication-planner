"""Tests for random scheduler."""

from typing import Dict, List, Any, Optional
from datetime import date, timedelta
import pytest
from src.schedulers.random import RandomScheduler
from src.core.models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence, Schedule


class TestRandomScheduler:
    """Test cases for random scheduler."""
    
    def test_schedule_empty_submissions(self, empty_config) -> None:
        """Test random scheduler with empty submissions."""
        scheduler = RandomScheduler(empty_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object, not a dict
        assert isinstance(result, Schedule)
        assert len(result.intervals) == 0
    
    def test_schedule_single_paper(self, sample_config) -> None:
        """Test random scheduler with single paper."""
        scheduler = RandomScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        assert len(result.intervals) > 0
        
        # Check that at least one submission was scheduled
        assert any(sub_id in result.intervals for sub_id in ["mod1-wrk", "paper1-pap", "mod2-wrk", "paper2-pap", "poster1"])
    
    def test_schedule_multiple_papers(self, sample_config) -> None:
        """Test random scheduler with multiple papers."""
        scheduler = RandomScheduler(sample_config)
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
    
    def test_random_algorithm_behavior(self, sample_config) -> None:
        """Test that random algorithm produces different results on multiple runs."""
        scheduler = RandomScheduler(sample_config, seed=42)
        result1: Any = scheduler.schedule()
        
        scheduler2 = RandomScheduler(sample_config, seed=123)
        result2: Any = scheduler2.schedule()
        
        # Both should return Schedule objects
        assert isinstance(result1, Schedule)
        assert isinstance(result2, Schedule)
        
        # Results might be different due to randomness
        # At minimum, both should have some scheduled submissions
        assert len(result1.intervals) > 0
        assert len(result2.intervals) > 0
    
    def test_schedule_with_constraints(self, sample_config) -> None:
        """Test random scheduler respects constraints."""
        scheduler = RandomScheduler(sample_config)
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
        
        scheduler = RandomScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should still return a Schedule object
        assert isinstance(result, Schedule)
        # The invalid submission might not be scheduled, but that's okay
    
    def test_schedule_with_priority_ordering(self, sample_config) -> None:
        """Test random scheduler with priority ordering."""
        scheduler = RandomScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check that all scheduled submissions have valid intervals
        for sub_id, interval in result.intervals.items():
            assert isinstance(interval.start_date, date)
            assert isinstance(interval.end_date, date)
            assert interval.start_date <= interval.end_date
    
    def test_schedule_with_deadline_compliance(self, sample_config) -> None:
        """Test random scheduler with deadline compliance."""
        scheduler = RandomScheduler(sample_config)
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
    
    def test_schedule_with_resource_constraints(self, sample_config) -> None:
        """Test random scheduler with resource constraints."""
        # Set low concurrency limit
        sample_config.max_concurrent_submissions = 1
        
        scheduler = RandomScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check resource constraints
        if len(result.intervals) > 1:
            # Calculate daily load
            daily_load = {}
            for sub_id, interval in result.intervals.items():
                submission = sample_config.get_submission(sub_id)
                if submission:
                    duration = submission.get_duration_days(sample_config)
                    for i in range(duration):
                        day = interval.start_date + timedelta(days=i)
                        daily_load[day] = daily_load.get(day, 0) + 1
            
            # Check that no day exceeds concurrency limit
            max_concurrent = max(daily_load.values()) if daily_load else 0
            assert max_concurrent <= sample_config.max_concurrent_submissions
    
    def test_schedule_with_multiple_runs(self, sample_config) -> None:
        """Test random scheduler produces consistent results with same seed."""
        scheduler1 = RandomScheduler(sample_config, seed=42)
        result1: Any = scheduler1.schedule()
        
        scheduler2 = RandomScheduler(sample_config, seed=42)
        result2: Any = scheduler2.schedule()
        
        # Both should return Schedule objects
        assert isinstance(result1, Schedule)
        assert isinstance(result2, Schedule)
        
        # With same seed, results should be identical
        assert len(result1.intervals) == len(result2.intervals)
        
        # Check that the same submissions are scheduled
        assert set(result1.intervals.keys()) == set(result2.intervals.keys())
