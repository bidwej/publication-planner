"""Tests for efficiency scoring."""

from datetime import date
from typing import Dict, Any

from scoring.efficiency import calculate_efficiency_score


class TestCalculateEfficiencyScore:
    """Test the calculate_efficiency_score function."""
    
    def test_empty_schedule(self, config: Any) -> None:
        """Test efficiency calculation with empty schedule."""
        schedule: Schedule = {}
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_single_submission(self, config: Any) -> None:
        """Test efficiency calculation with single submission."""
        schedule: Schedule = {"test-pap": date(2025, 1, 1)}
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_multiple_submissions(self, config: Any) -> None:
        """Test efficiency calculation with multiple submissions."""
        schedule: Schedule = {
            "test-pap": date(2025, 1, 1),
            "test-mod": date(2025, 1, 15),
            "test-abs": date(2025, 2, 1)
        }
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_resource_utilization(self, config: Any) -> None:
        """Test efficiency score for resource utilization."""
        # Create a schedule that uses resources efficiently
        schedule: Schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 3, 1),  # After first paper ends
            "paper3": date(2025, 4, 1)
        }
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_time_spacing(self, config: Any) -> None:
        """Test efficiency score for time spacing."""
        # Create a schedule with good time spacing
        schedule: Schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 3, 1),
            "paper3": date(2025, 5, 1)
        }
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_concurrent_utilization(self, config: Any) -> None:
        """Test efficiency score for concurrent utilization."""
        # Create a schedule that uses concurrency efficiently
        schedule: Schedule = {
            "paper1": date(2025, 1, 1),
            "paper2": date(2025, 1, 1),  # Same day - uses concurrency
            "paper3": date(2025, 3, 1)  # After first two end
        }
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0



