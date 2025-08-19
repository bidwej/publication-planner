"""Tests for efficiency scoring."""

from datetime import date
from typing import Dict, Any
from src.core.models import Schedule, Interval

from src.scoring.efficiency import calculate_efficiency_score


class TestCalculateEfficiencyScore:
    """Test the calculate_efficiency_score function."""
    
    def test_empty_schedule(self, config: Any) -> None:
        """Test efficiency calculation with empty schedule."""
        schedule = Schedule(intervals={})
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_single_submission(self, config: Any) -> None:
        """Test efficiency calculation with single submission."""
        intervals = {
            "test-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_multiple_submissions(self, config: Any) -> None:
        """Test efficiency calculation with multiple submissions."""
        intervals = {
            "test-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "test-mod": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 1, 30)),
            "test-abs": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 15))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_resource_utilization(self, config: Any) -> None:
        """Test efficiency score for resource utilization."""
        # Create a schedule that uses resources efficiently
        intervals = {
            "paper1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "paper2": Interval(start_date=date(2025, 3, 1), end_date=date(2025, 3, 15)),  # After first paper ends
            "paper3": Interval(start_date=date(2025, 4, 1), end_date=date(2025, 4, 15))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_time_spacing(self, config: Any) -> None:
        """Test efficiency score for time spacing."""
        # Create a schedule with good time spacing
        intervals = {
            "paper1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "paper2": Interval(start_date=date(2025, 3, 1), end_date=date(2025, 3, 15)),
            "paper3": Interval(start_date=date(2025, 5, 1), end_date=date(2025, 5, 15))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0
    
    def test_concurrent_utilization(self, config: Any) -> None:
        """Test efficiency score for concurrent utilization."""
        # Create a schedule that uses concurrency efficiently
        intervals = {
            "paper1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "paper2": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),  # Same day - uses concurrency
            "paper3": Interval(start_date=date(2025, 3, 1), end_date=date(2025, 3, 15))  # After first two end
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_efficiency_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0



