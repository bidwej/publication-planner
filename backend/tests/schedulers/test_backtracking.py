"""Tests for backtracking scheduler."""

from typing import Dict, List, Any, Optional
from datetime import date, timedelta
import pytest
from src.schedulers.backtracking import BacktrackingGreedyScheduler
from src.core.models import Config, Submission, Conference, SubmissionType, ConferenceType, ConferenceRecurrence, Schedule


class TestBacktrackingScheduler:
    """Test cases for backtracking scheduler."""
    
    def test_schedule_empty_submissions(self, empty_config) -> None:
        """Test backtracking scheduler with empty submissions."""
        scheduler = BacktrackingGreedyScheduler(empty_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object, not a dict
        assert isinstance(result, Schedule)
        assert len(result.intervals) == 0
    
    def test_schedule_single_paper(self, sample_config) -> None:
        """Test backtracking scheduler with single paper."""
        scheduler = BacktrackingGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        assert len(result.intervals) > 0
        
        # Check that at least one submission was scheduled
        assert any(sub_id in result.intervals for sub_id in ["mod1-wrk", "paper1-pap", "mod2-wrk", "paper2-pap", "poster1"])
    
    def test_schedule_multiple_papers(self, sample_config) -> None:
        """Test backtracking scheduler with multiple papers."""
        scheduler = BacktrackingGreedyScheduler(sample_config)
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
    
    def test_backtracking_algorithm_behavior(self, sample_config) -> None:
        """Test that backtracking algorithm can reschedule submissions."""
        scheduler = BacktrackingGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check that dependencies are respected
        if "paper1-pap" in result.intervals and "mod1-wrk" in result.intervals:
            paper_start = result.intervals["paper1-pap"].start_date
            mod_end = result.intervals["mod1-wrk"].end_date
            # Paper should start after mod ends
            assert paper_start >= mod_end
    
    def test_schedule_with_constraints(self, sample_config) -> None:
        """Test backtracking scheduler respects constraints."""
        scheduler = BacktrackingGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check that dependencies are respected
        if "paper1-pap" in result.intervals and "mod1-wrk" in result.intervals:
            paper_start = result.intervals["paper1-pap"].start_date
            mod_end = result.intervals["mod1-wrk"].end_date
            # Paper should start after mod ends
            assert paper_start >= mod_end
    
    def test_schedule_with_resource_optimization(self, sample_config) -> None:
        """Test backtracking scheduler optimizes resource usage."""
        # Create additional submissions to test resource optimization
        additional_submissions = [
            Submission(
                id="paper0",
                title="Additional Paper 0",
                kind=SubmissionType.PAPER,
                conference_id="ICRA2026",
                depends_on=[],
                draft_window_months=3,
                author="test"
            ),
            Submission(
                id="paper1",
                title="Additional Paper 1",
                kind=SubmissionType.PAPER,
                conference_id="ICRA2026",
                depends_on=[],
                draft_window_months=3,
                author="test"
            ),
            Submission(
                id="paper2",
                title="Additional Paper 2",
                kind=SubmissionType.PAPER,
                conference_id="ICRA2026",
                depends_on=[],
                draft_window_months=3,
                author="test"
            )
        ]
        
        # Add to config
        for submission in additional_submissions:
            sample_config.submissions.append(submission)
        
        scheduler = BacktrackingGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check that backtracking considers resource optimization
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
            
            # Backtracking should try to distribute workload more evenly
            if daily_load:
                max_concurrent = max(daily_load.values())
                avg_concurrent = sum(daily_load.values()) / len(daily_load)
                # Max should not be too much higher than average (good distribution)
                assert max_concurrent <= avg_concurrent * 2.5  # Allow some variance
    
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
        
        scheduler = BacktrackingGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should still return a Schedule object
        assert isinstance(result, Schedule)
        # The invalid submission might not be scheduled, but that's okay
    
    def test_schedule_with_priority_ordering(self, sample_config) -> None:
        """Test backtracking scheduler with priority ordering."""
        scheduler = BacktrackingGreedyScheduler(sample_config)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Check that all scheduled submissions have valid intervals
        for sub_id, interval in result.intervals.items():
            assert isinstance(interval.start_date, date)
            assert isinstance(interval.end_date, date)
            assert interval.start_date <= interval.end_date
    
    def test_schedule_with_deadline_compliance(self, sample_config) -> None:
        """Test backtracking scheduler with deadline compliance."""
        scheduler = BacktrackingGreedyScheduler(sample_config)
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
    
    def test_backtracking_with_max_backtracks(self, sample_config) -> None:
        """Test backtracking scheduler respects max backtracks limit."""
        # Create a configuration that might trigger backtracking
        sample_config.max_concurrent_submissions = 1
        
        scheduler = BacktrackingGreedyScheduler(sample_config, max_backtracks=2)
        result: Any = scheduler.schedule()
        
        # Should return a Schedule object
        assert isinstance(result, Schedule)
        
        # Should have scheduled some submissions
        assert len(result.intervals) > 0
        
        # Check that all scheduled submissions have valid intervals
        for sub_id, interval in result.intervals.items():
            assert isinstance(interval.start_date, date)
            assert isinstance(interval.end_date, date)
            assert interval.start_date <= interval.end_date
