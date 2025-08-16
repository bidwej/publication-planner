from typing import Dict, List, Any, Optional

"""
Tests for resources validation module.
"""

import pytest
from datetime import date
from validation.resources import validate_resources_constraints, _calculate_daily_load
from core.models import Config, Submission, ResourceValidation


class TestResourcesValidation:
    """Test cases for resources validation functions."""
    
    def test_validate_resources_constraints_empty_schedule(self, empty_config) -> None:
        """Test resources validation with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result: Any = validate_resources_constraints(schedule, empty_config)
        assert isinstance(result, ResourceValidation)
        assert result.is_valid == True
        assert result.max_observed == 0
    
    def test_calculate_daily_load_empty_schedule(self, empty_config) -> None:
        """Test daily load calculation with empty schedule."""
        schedule: Dict[str, date] = {}
        
        result: Any = _calculate_daily_load(schedule, empty_config)
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_resources_validation_with_submissions(self, sample_config) -> None:
        """Test resources validation with actual submissions."""
        # Use the sample_config fixture which already has submissions and conferences
        
        # Test with valid schedule (respects concurrency limit)
        valid_schedule = {
            "mod1-wrk": date(2025, 1, 1),   # Starts first
            "paper1-pap": date(2025, 3, 1), # Starts after mod1 completes
            "mod2-wrk": date(2025, 5, 1),   # Starts after paper1 completes
            "paper2-pap": date(2025, 7, 1)  # Starts after mod2 completes
        }
        
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
        strict_config = Config(
            submissions=sample_config.submissions,
            conferences=sample_config.conferences,
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=2  # Strict limit
        )
        
        # Test with invalid schedule (exceeds concurrency limit)
        invalid_schedule = {
            "mod1-wrk": date(2025, 1, 1),   # All three start on same day
            "paper1-pap": date(2025, 1, 1), # Violates max_concurrent_submissions=2
            "mod2-wrk": date(2025, 1, 1),   # Violates max_concurrent_submissions=2
            "paper2-pap": date(2025, 2, 1)  # After others
        }
        
        result = validate_resources_constraints(invalid_schedule, strict_config)
        assert result.is_valid == False
        assert result.max_observed > strict_config.max_concurrent_submissions
        assert len(result.violations) > 0
        
        # Test with valid schedule (respects concurrency limit)
        valid_schedule = {
            "mod1-wrk": date(2025, 1, 1),   # First submission
            "paper1-pap": date(2025, 2, 1), # Second submission (after mod1 completes)
            "mod2-wrk": date(2025, 3, 1),   # Third submission (after paper1 completes)
            "paper2-pap": date(2025, 4, 1)  # Fourth submission (after mod2 completes)
        }
        
        valid_result = validate_resources_constraints(valid_schedule, strict_config)
        assert valid_result.is_valid == True
        assert valid_result.max_observed <= strict_config.max_concurrent_submissions
