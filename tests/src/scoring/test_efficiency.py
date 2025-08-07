"""Tests for efficiency scoring."""

from datetime import date

from scoring.efficiency import calculate_efficiency_score


class TestCalculateEfficiencyScore:
    """Test the calculate_efficiency_score function."""
    
    def test_empty_schedule(self, config):
        """Test efficiency calculation with empty schedule."""
        schedule = {}
        score = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_single_submission(self, config):
        """Test efficiency calculation with single submission."""
        schedule = {"test-pap": date(2025, 1, 1)}
        score = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_multiple_submissions(self, config):
        """Test efficiency calculation with multiple submissions."""
        schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15),
            "test-abs": date(2025, 2, 1)
        }
        score = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_resource_utilization(self, config):
        """Test efficiency score for resource utilization."""
        # Create a schedule that uses resources efficiently
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 3, 1),  # After first paper ends
            "paper3": date(2025, 4, 1)
        }
        score = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_time_spacing(self, config):
        """Test efficiency score for time spacing."""
        # Create a schedule with good time spacing
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 3, 1),
            "paper3": date(2025, 5, 1)
        }
        score = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_concurrent_utilization(self, config):
        """Test efficiency score for concurrent utilization."""
        # Create a schedule that uses concurrency efficiently
        schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 1),  # Same day - uses concurrency
            "paper3": date(2025, 3, 1)  # After first two end
        }
        score = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0



