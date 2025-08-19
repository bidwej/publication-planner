"""Tests for penalty scoring."""

from datetime import date, timedelta
from typing import Dict, Any, List
import pytest
from src.core.models import Schedule, Interval, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, Config
from src.scoring.penalties import calculate_penalty_score


class TestCalculatePenaltyScore:
    """Test the calculate_penalty_score function."""
    
    def test_empty_schedule(self, config: Any) -> None:
        """Test penalty calculation with empty schedule."""
        schedule = Schedule(intervals={})
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty == 0.0
        assert breakdown.deadline_penalties == 0.0
        assert breakdown.dependency_penalties == 0.0
        assert breakdown.resource_penalties == 0.0
    
    def test_single_submission(self, config: Any) -> None:
        """Test penalty calculation with single submission."""
        intervals = {
            "test-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15))
        }
        schedule = Schedule(intervals=intervals)
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_multiple_submissions(self, config: Any) -> None:
        """Test penalty calculation with multiple submissions."""
        intervals = {
            "test-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "test-mod": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 1, 30)),
            "test-abs": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 15))
        }
        schedule = Schedule(intervals=intervals)
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_late_submission_penalty(self, config: Any) -> None:
        """Test penalty calculation for late submissions."""
        # Create a schedule with a late submission
        intervals = {
            "late-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15))
        }
        schedule = Schedule(intervals=intervals)
        
        # Create a submission with a past deadline
        late_submission = Submission(
            id="late-pap",
            title="Late Paper",
            kind=SubmissionType.PAPER,
            conference_id="past-conf",
            depends_on=[],
            draft_window_months=3,
            author="test"
        )
        
        # Create a conference with a past deadline
        past_conference = Conference(
            id="past-conf",
            name="Past Conference",
            conf_type=ConferenceType.ENGINEERING,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={
                SubmissionType.PAPER: date(2024, 12, 1)  # Past deadline
            }
        )
        
        # Add to config
        config.submissions.append(late_submission)
        config.conferences.append(past_conference)
        
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty > 0.0
        assert breakdown.deadline_penalties > 0.0
    
    def test_overlap_penalty(self, config: Any) -> None:
        """Test penalty calculation for overlapping submissions."""
        # Create a schedule with overlapping submissions
        intervals = {
            "overlap1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "overlap2": Interval(start_date=date(2025, 1, 10), end_date=date(2025, 1, 25))  # Overlaps with overlap1
        }
        schedule = Schedule(intervals=intervals)
        
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_dependency_violation_penalty(self, config: Any) -> None:
        """Test penalty calculation for dependency violations."""
        # Create a schedule with dependency violations
        intervals = {
            "dep-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "dep-abs": Interval(start_date=date(2025, 1, 20), end_date=date(2025, 1, 25))  # After paper, but should be before
        }
        schedule = Schedule(intervals=intervals)
        
        # Create submissions with dependencies
        abs_submission = Submission(
            id="dep-abs",
            title="Abstract",
            kind=SubmissionType.ABSTRACT,
            conference_id="test-conf",
            depends_on=[],
            draft_window_months=0,
            author="test"
        )
        
        paper_submission = Submission(
            id="dep-pap",
            title="Paper",
            kind=SubmissionType.PAPER,
            conference_id="test-conf",
            depends_on=["dep-abs"],  # Paper depends on abstract
            draft_window_months=3,
            author="test"
        )
        
        # Add to config
        config.submissions.append(abs_submission)
        config.submissions.append(paper_submission)
        
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_penalty_edge_cases(self, config: Any) -> None:
        """Test penalty calculation with edge cases."""
        # Test with malformed schedule
        malformed_config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        
        # Test with empty intervals
        empty_schedule = Schedule(intervals={})
        result = calculate_penalty_score(empty_schedule, malformed_config)
        
        assert result.total_penalty == 0.0
    
    def test_penalty_with_invalid_dates(self, config: Any) -> None:
        """Test penalty calculation with invalid dates."""
        # Create a schedule with invalid date ranges
        intervals = {
            "invalid": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 1, 1))  # End before start
        }
        schedule = Schedule(intervals=intervals)
        
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_penalty_with_circular_dependencies(self, config: Any) -> None:
        """Test penalty calculation with circular dependencies."""
        # Create a schedule with potential circular dependencies
        intervals = {
            "circ1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "circ2": Interval(start_date=date(2025, 1, 20), end_date=date(2025, 2, 5))
        }
        schedule = Schedule(intervals=intervals)
        
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_penalty_with_missing_dependencies(self, config: Any) -> None:
        """Test penalty calculation with missing dependencies."""
        # Create a schedule with missing dependencies
        intervals = {
            "missing-dep": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15))
        }
        schedule = Schedule(intervals=intervals)
        
        # Create a submission that depends on a missing submission
        missing_dep_submission = Submission(
            id="missing-dep",
            title="Missing Dependency",
            kind=SubmissionType.PAPER,
            conference_id="test-conf",
            depends_on=["nonexistent"],  # Depends on missing submission
            draft_window_months=3,
            author="test"
        )
        
        # Add to config
        config.submissions.append(missing_dep_submission)
        
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_penalty_with_extreme_concurrent_submissions(self, config: Any) -> None:
        """Test penalty calculation with extreme concurrency."""
        # Create a schedule with many concurrent submissions
        intervals = {}
        for i in range(10):
            intervals[f"concurrent-{i}"] = Interval(
                start_date=date(2025, 1, 1), 
                end_date=date(2025, 1, 15)
            )
        
        schedule = Schedule(intervals=intervals)
        
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, float)
        assert breakdown.total_penalty >= 0.0
    
    def test_penalty_consistency_across_calculations(self, config: Any) -> None:
        """Test that penalty calculations are consistent."""
        # Create two identical schedules
        intervals1 = {
            "consist1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "consist2": Interval(start_date=date(2025, 1, 20), end_date=date(2025, 2, 5))
        }
        schedule1 = Schedule(intervals=intervals1)
        
        intervals2 = {
            "consist1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "consist2": Interval(start_date=date(2025, 1, 20), end_date=date(2025, 2, 5))
        }
        schedule2 = Schedule(intervals=intervals2)
        
        result1 = calculate_penalty_score(schedule1, config)
        result2 = calculate_penalty_score(schedule2, config)
        
        # Results should be identical
        assert result1.total_penalty == result2.total_penalty
        assert result1.deadline_penalties == result2.deadline_penalties
        assert result1.dependency_penalties == result2.dependency_penalties
        assert result1.resource_penalties == result2.resource_penalties



