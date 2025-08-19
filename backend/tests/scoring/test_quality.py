"""Tests for quality scoring."""

from datetime import date, timedelta
from typing import Dict, Any, List
import pytest
from src.core.models import Schedule, Interval, Submission, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, Config
from src.scoring.quality import calculate_quality_score, calculate_quality_robustness, calculate_quality_balance


class TestCalculateQualityScore:
    """Test the calculate_quality_score function."""
    
    def test_empty_schedule(self, config: Any) -> None:
        """Test quality calculation with empty schedule."""
        schedule = Schedule(intervals={})
        score: float = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0.0
    
    def test_single_submission(self, config: Any) -> None:
        """Test quality calculation with single submission."""
        intervals = {
            "test-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0.0
    
    def test_multiple_submissions(self, config: Any) -> None:
        """Test quality calculation with multiple submissions."""
        intervals = {
            "test-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "test-mod": Interval(start_date=date(2025, 1, 15), end_date=date(2025, 1, 30)),
            "test-abs": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 15))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0.0
    
    def test_diversity_score(self, config: Any) -> None:
        """Test quality calculation with diverse submission types."""
        intervals = {
            "paper1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "abstract1": Interval(start_date=date(2025, 1, 20), end_date=date(2025, 1, 25)),
            "poster1": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 5))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0.0
    
    def test_balance_score(self, config: Any) -> None:
        """Test quality calculation with balanced schedule."""
        intervals = {
            "balanced1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "balanced2": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 15)),
            "balanced3": Interval(start_date=date(2025, 3, 1), end_date=date(2025, 3, 15))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0.0
    
    def test_priority_weighting(self, config: Any) -> None:
        """Test quality calculation with priority weighting."""
        intervals = {
            "high-priority": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "medium-priority": Interval(start_date=date(2025, 1, 20), end_date=date(2025, 2, 5)),
            "low-priority": Interval(start_date=date(2025, 2, 10), end_date=date(2025, 2, 25))
        }
        schedule = Schedule(intervals=intervals)
        score: float = calculate_quality_score(schedule, config)
        
        assert isinstance(score, float)
        assert score >= 0.0


class TestQualityFunctions:
    """Test additional quality functions."""
    
    def test_calculate_schedule_robustness(self, config: Any) -> None:
        """Test schedule robustness calculation."""
        intervals = {
            "robust1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "robust2": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 15))
        }
        schedule = Schedule(intervals=intervals)
        robustness = calculate_quality_robustness(schedule, config)
        
        assert isinstance(robustness, float)
        assert robustness >= 0.0
    
    def test_calculate_quality_balance(self, config: Any) -> None:
        """Test quality balance calculation."""
        intervals = {
            "balance1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "balance2": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 15))
        }
        schedule = Schedule(intervals=intervals)
        balance = calculate_quality_balance(schedule, config)
        
        assert isinstance(balance, float)
        assert balance >= 0.0
    
    def test_robustness_with_empty_schedule(self, config: Any) -> None:
        """Test robustness calculation with empty schedule."""
        schedule = Schedule(intervals={})
        robustness = calculate_quality_robustness(schedule, config)
        
        assert isinstance(robustness, float)
        assert robustness >= 0.0
    
    def test_balance_with_empty_schedule(self, config: Any) -> None:
        """Test balance calculation with empty schedule."""
        schedule = Schedule(intervals={})
        balance = calculate_quality_balance(schedule, config)
        
        assert isinstance(balance, float)
        assert balance >= 0.0
    
    def test_robustness_with_single_submission(self, config: Any) -> None:
        """Test robustness calculation with single submission."""
        intervals = {
            "single": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15))
        }
        schedule = Schedule(intervals=intervals)
        robustness = calculate_quality_robustness(schedule, config)
        
        assert isinstance(robustness, float)
        assert robustness >= 0.0
    
    def test_balance_with_well_distributed_schedule(self, config: Any) -> None:
        """Test balance calculation with well-distributed schedule."""
        intervals = {
            "dist1": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 1, 15)),
            "dist2": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 2, 15)),
            "dist3": Interval(start_date=date(2025, 3, 1), end_date=date(2025, 3, 15)),
            "dist4": Interval(start_date=date(2025, 4, 1), end_date=date(2025, 4, 15))
        }
        schedule = Schedule(intervals=intervals)
        balance = calculate_quality_balance(schedule, config)
        
        assert isinstance(balance, float)
        assert balance >= 0.0
