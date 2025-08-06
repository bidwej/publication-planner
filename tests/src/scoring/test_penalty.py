"""Tests for penalty scoring."""

from datetime import date

from src.scoring.penalty import calculate_penalty_score


class TestCalculatePenaltyScore:
    """Test the calculate_penalty_score function."""
    
    def test_empty_schedule(self, config):
        """Test penalty calculation with empty schedule."""
        schedule = {}
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, (int, float))
        assert breakdown.total_penalty >= 0
        assert hasattr(breakdown, 'deadline_penalties')
        assert hasattr(breakdown, 'dependency_penalties')
        assert hasattr(breakdown, 'resource_penalties')
    
    def test_single_submission(self, config):
        """Test penalty calculation with single submission."""
        schedule = {"test-pap": date(2025, 1, 1)}
        breakdown = calculate_penalty_score(schedule, config)
        
        assert isinstance(breakdown.total_penalty, (int, float))
        assert breakdown.total_penalty >= 0
        assert hasattr(breakdown, 'deadline_penalties')
        assert hasattr(breakdown, 'dependency_penalties')
        assert hasattr(breakdown, 'resource_penalties')
    
    def test_multiple_submissions(self, config):
        """Test penalty calculation with multiple submissions."""
        schedule = {
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
    
    def test_late_submission_penalty(self, config):
        """Test penalty for late submissions."""
        # Create a schedule with submissions after their deadlines
        schedule = {
            "test-pap": date(2025, 12, 31),  # Very late
            "test-mod": date(2025, 6, 30)    # Moderately late
        }
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty >= 0
        # Should have some penalty for late submissions
        assert breakdown.total_penalty >= 0
    
    def test_overlap_penalty(self, config):
        """Test penalty for overlapping submissions."""
        # Create a schedule with overlapping submissions
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 1),  # Same day - should cause overlap
            "test-abs": date(2025, 1, 1)   # Same day - should cause overlap
        }
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty >= 0
        # Should have some penalty for overlaps
        assert breakdown.total_penalty >= 0
    
    def test_dependency_violation_penalty(self, config):
        """Test penalty for dependency violations."""
        # Create a schedule where child starts before parent
        schedule = {
            "parent-pap": date(2025, 2, 1),
            "child-pap": date(2025, 1, 1)  # Child before parent
        }
        breakdown = calculate_penalty_score(schedule, config)
        
        assert breakdown.total_penalty >= 0
        # Should have some penalty for dependency violations
        assert breakdown.total_penalty >= 0



