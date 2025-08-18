from typing import Dict, List, Any, Optional

"""
Tests for resources validation module.
"""

import pytest
from datetime import date
from src.validation.resources import validate_resources_constraints, _calculate_daily_load
from src.core.models import Config, Submission, ResourceValidation, Schedule, Interval


class TestResourcesValidation:
    """Test cases for resources validation functions."""
    
    def test_validate_resources_constraints_empty_schedule(self, empty_config) -> None:
        """Test resources validation with empty schedule."""
        schedule = Schedule(intervals={})
        
        result: Any = validate_resources_constraints(schedule, empty_config)
        assert isinstance(result, ResourceValidation)
        assert result.is_valid == True
        assert result.max_observed == 0
    
    def test_calculate_daily_load_empty_schedule(self, empty_config) -> None:
        """Test daily load calculation with empty schedule."""
        schedule = Schedule(intervals={})
        
        result: Any = _calculate_daily_load(schedule, empty_config)
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_resources_validation_with_submissions(self, sample_config) -> None:
        """Test resources validation with actual submissions."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Test with valid schedule (respects concurrency limit)
        valid_schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 2, 1)),
            "paper1-pap": Interval(start_date=date(2025, 3, 1), end_date=date(2025, 4, 1)),
            "mod2-wrk": Interval(start_date=date(2025, 5, 1), end_date=date(2025, 6, 1)),
            "paper2-pap": Interval(start_date=date(2025, 7, 1), end_date=date(2025, 8, 1))
        })
        
        result = validate_resources_constraints(valid_schedule, sample_config)
        assert result.is_valid == True
        assert result.max_observed <= sample_config.max_concurrent_submissions
        
        # Test daily load calculation
        daily_load = _calculate_daily_load(valid_schedule, sample_config)
        assert isinstance(daily_load, dict)
        assert len(daily_load) > 0
        
        # Find the maximum daily load
        max_load = max(daily_load.values()) if daily_load else 0
        assert max_load <= sample_config.max_concurrent_submissions
    
    def test_concurrency_limit_validation(self, sample_config) -> None:
        """Test concurrency limit validation."""
        # Create a modified config with stricter concurrency limits to test resource constraints
        # Modify the existing config instead of creating a new one
        sample_config.max_concurrent_submissions = 2  # Strict limit
        
        # Test with invalid schedule (exceeds concurrency limit)
        invalid_schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 2, 1)),
            "paper1-pap": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 2, 1)),
            "mod2-wrk": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 2, 1)),
            "paper2-pap": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 3, 1))
        })
        
        result = validate_resources_constraints(invalid_schedule, sample_config)
        assert result.is_valid == False
        assert result.max_observed > sample_config.max_concurrent_submissions
        assert len(result.violations) > 0
        
        # Test with valid schedule (respects concurrency limit)
        valid_schedule = Schedule(intervals={
            "mod1-wrk": Interval(start_date=date(2025, 1, 1), end_date=date(2025, 2, 1)),
            "paper1-pap": Interval(start_date=date(2025, 2, 1), end_date=date(2025, 3, 1)),
            "mod2-wrk": Interval(start_date=date(2025, 3, 1), end_date=date(2025, 4, 1)),
            "paper2-pap": Interval(start_date=date(2025, 4, 1), end_date=date(2025, 5, 1))
        })
        
        valid_result = validate_resources_constraints(valid_schedule, sample_config)
        assert valid_result.is_valid == True
        assert valid_result.max_observed <= sample_config.max_concurrent_submissions
