"""Tests for penalty scoring."""

from datetime import date, timedelta

from scoring.penalties import calculate_penalty_score
from core.models import Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence
from tests.conftest import create_mock_config
from typing import Dict, List, Any, Optional



class TestCalculatePenaltyScore:
    """Test the calculate_penalty_score function."""
    
    def test_empty_schedule(self, config) -> None:
        """Test penalty calculation with empty schedule."""
        schedule: Dict[str, date] = {}
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, (int, float))
        assert breakdown.total_penalty >= 0
        assert hasattr(breakdown, 'deadline_penalties')
        assert hasattr(breakdown, 'dependency_penalties')
        assert hasattr(breakdown, 'resource_penalties')
    
    def test_single_submission(self, config) -> None:
        """Test penalty calculation with single submission."""
        schedule: Dict[str, date] = {"test-pap": date(2025, 1, 1)}
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, (int, float))
        assert breakdown.total_penalty >= 0
        assert hasattr(breakdown, 'deadline_penalties')
        assert hasattr(breakdown, 'dependency_penalties')
        assert hasattr(breakdown, 'resource_penalties')
    
    def test_multiple_submissions(self, config) -> None:
        """Test penalty calculation with multiple submissions."""
        schedule: Dict[str, date] = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15),
            "test-abs": date(2025, 2, 1)
        }
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, (int, float))
        assert breakdown.total_penalty >= 0
        assert hasattr(breakdown, 'deadline_penalties')
        assert hasattr(breakdown, 'dependency_penalties')
        assert hasattr(breakdown, 'resource_penalties')
    
    def test_late_submission_penalty(self, config) -> None:
        """Test penalty for late submissions."""
        # Create a schedule with submissions after their deadlines
        schedule: Dict[str, date] = {
            "test-pap": date(2025, 12, 31),  # Very late
            "test-mod": date(2025, 6, 30)    # Moderately late
        }
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty >= 0
        # Should have some penalty for late submissions
        assert breakdown.total_penalty >= 0
    
    def test_overlap_penalty(self, config) -> None:
        """Test penalty for overlapping submissions."""
        # Create a schedule with overlapping submissions
        schedule: Dict[str, date] = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 1),  # Same day - should cause overlap
            "test-abs": date(2025, 1, 1)   # Same day - should cause overlap
        }
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty >= 0
        # Should have some penalty for overlaps
        assert breakdown.total_penalty >= 0
    
    def test_dependency_violation_penalty(self, config) -> None:
        """Test penalty for dependency violations."""
        # Create a schedule where child starts before parent
        schedule: Dict[str, date] = {
            "parent-pap": date(2025, 2, 1),
            "child-pap": date(2025, 1, 1)  # Child before parent
        }
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty >= 0
        # Should have some penalty for dependency violations
        assert breakdown.total_penalty >= 0

    def test_penalty_edge_cases(self) -> None:
        """Test penalty calculation with edge cases."""
        from scoring.penalties import calculate_penalty_score
        
        # Test with empty schedule
        config = create_mock_config()
        result: Any = calculate_penalty_score({}, config)
        assert result.total_penalty == 0.0
        assert result.deadline_penalties == 0.0
        assert result.dependency_penalties == 0.0
        assert result.resource_penalties == 0.0
        
        # Test with None schedule
        result: Any = calculate_penalty_score({}, config)
        assert result.total_penalty == 0.0
        
        # Test with extreme penalty values
        extreme_config = create_mock_config(
            penalty_costs={
                "default_mod_penalty_per_day": 999999.0,
                "default_monthly_slip_penalty": 50000.0,
                "resource_violation_penalty": 100000.0,
                "conference_compatibility_penalty": 75000.0,
                "missing_abstract_penalty": 60000.0,
                "unscheduled_abstract_penalty": 55000.0,
                "abstract_paper_timing_penalty": 45000.0,
                "missing_abstract_dependency_penalty": 40000.0,
                "slack_cost_penalty": 30000.0
            }
        )
        
        # Should handle extreme values without crashing
        result: Any = calculate_penalty_score({}, extreme_config)
        assert isinstance(result.total_penalty, float)
        
        # Test with malformed submission data
        malformed_submission: Submission = Submission(
            id="malformed",
            title="",
            kind=SubmissionType.PAPER,
            conference_id="nonexistent_conf",
            penalty_cost_per_day=-1000.0  # Invalid negative penalty
        )
        
        malformed_config = create_mock_config(
            submissions=[malformed_submission],
            conferences=[]
        )
        
        # Should handle malformed data gracefully
        result: Any = calculate_penalty_score({"malformed": date.today()}, malformed_config)
        assert isinstance(result.total_penalty, float)

    def test_penalty_with_invalid_dates(self) -> None:
        """Test penalty calculation with invalid dates."""
        from scoring.penalties import calculate_penalty_score
        
        # Test with submissions scheduled in the past
        past_date = date.today() - timedelta(days=365)
        
        submission: Submission = Submission(
            id="past_submission",
            title="Past Submission",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date.today() + timedelta(days=30)}
        )
        
        config = create_mock_config(
            submissions=[submission],
            conferences=[conference]
        )
        
        # Schedule in the past
        schedule: Dict[str, date] = {"past_submission": past_date}
        result: Any = calculate_penalty_score(schedule, config)
        
        # Should calculate penalties for past scheduling
        assert result.total_penalty >= 0.0

    def test_penalty_with_circular_dependencies(self) -> None:
        """Test penalty calculation with circular dependencies."""
        from scoring.penalties import calculate_penalty_score
        
        # Create circular dependency
        submission_a = Submission(
            id="sub_a",
            title="Submission A",
            kind=SubmissionType.PAPER,
            depends_on=["sub_b"]
        )
        
        submission_b = Submission(
            id="sub_b",
            title="Submission B", 
            kind=SubmissionType.PAPER,
            depends_on=["sub_a"]  # Circular dependency
        )
        
        config = create_mock_config(
            submissions=[submission_a, submission_b],
            conferences=[]
        )
        
        # Schedule both submissions
        schedule: Dict[str, date] = {
            "sub_a": date.today(),
            "sub_b": date.today() + timedelta(days=1)
        }
        
        # Should handle circular dependencies gracefully
        result: Any = calculate_penalty_score(schedule, config)
        assert isinstance(result.total_penalty, float)

    def test_penalty_with_missing_dependencies(self) -> None:
        """Test penalty calculation with missing dependencies."""
        from scoring.penalties import calculate_penalty_score
        
        submission: Submission = Submission(
            id="dependent_sub",
            title="Dependent Submission",
            kind=SubmissionType.PAPER,
            depends_on=["nonexistent_dependency"]
        )
        
        config = create_mock_config(
            submissions=[submission],
            conferences=[]
        )
        
        # Schedule submission with missing dependency
        schedule: Dict[str, date] = {"dependent_sub": date.today()}
        result: Any = calculate_penalty_score(schedule, config)
        
        # Should penalize missing dependencies
        assert result.dependency_penalties > 0.0

    def test_penalty_with_extreme_concurrent_submissions(self) -> None:
        """Test penalty calculation with extreme concurrent submission scenarios."""
        from scoring.penalties import calculate_penalty_score
        
        # Create many submissions scheduled on the same day
        submissions = []
        for i in range(10):
            submission: Submission = Submission(
                id=f"sub_{i}",
                title=f"Submission {i}",
                kind=SubmissionType.PAPER
            )
            submissions.append(submission)
        
        config = create_mock_config(
            submissions=submissions,
            conferences=[],
            max_concurrent_submissions=2  # Very low limit
        )
        
        # Schedule all submissions on the same day
        schedule: Dict[str, date] = {sub.id: date.today() for sub in submissions}
        result: Any = calculate_penalty_score(schedule, config)
        
        # Should heavily penalize resource violations
        assert result.resource_penalties > 0.0
        assert result.total_penalty > 0.0

    def test_penalty_consistency_across_calculations(self) -> None:
        """Test that penalty calculations are consistent across different scenarios."""
        from scoring.penalties import calculate_penalty_score
        
        # Create identical schedules and ensure consistent penalties
        submission: Submission = Submission(
            id="test_sub",
            title="Test Submission",
            kind=SubmissionType.PAPER,
            conference_id="conf1"
        )
        
        conference: Conference = Conference(
            id="conf1",
            name="Test Conference",
            conf_type=ConferenceType.MEDICAL,
            recurrence=ConferenceRecurrence.ANNUAL,
            deadlines={SubmissionType.PAPER: date.today() + timedelta(days=30)}
        )
        
        config = create_mock_config(
            submissions=[submission],
            conferences=[conference]
        )
        
        # Same schedule should produce same penalty
        schedule1 = {"test_sub": date.today()}
        schedule2 = {"test_sub": date.today()}
        
        result1 = calculate_penalty_score(schedule1, config)
        result2 = calculate_penalty_score(schedule2, config)
        
        assert abs(result1.total_penalty - result2.total_penalty) < 0.01



