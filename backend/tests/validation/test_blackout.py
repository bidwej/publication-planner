"""Test blackout validation functions."""

import pytest
from datetime import date
from core.models import Config, Schedule, ValidationResult
from validation.blackout import validate_blackout_constraints


class TestBlackoutValidation:
    """Test cases for blackout validation functions."""
    
    def test_validate_blackout_constraints_no_blackout_dates(self, empty_config) -> None:
        """Test blackout validation with no blackout dates configured."""
        schedule = Schedule()
        
        result = validate_blackout_constraints(schedule, empty_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.metadata.get("total_submissions", 0) == 0
    
    def test_validate_blackout_constraints_with_blackout_dates(self, sample_config) -> None:
        """Test blackout validation with blackout dates configured."""
        # Create a copy of the config with blackout dates
        config_with_blackouts = sample_config.model_copy(update={
            "blackout_dates": [date(2025, 1, 1), date(2025, 7, 4)]  # New Year's and July 4th
        })
        
        # Test with valid schedule (no blackout dates) - use IDs that exist in config
        valid_schedule = Schedule()
        valid_schedule.add_interval("mod1-wrk", date(2025, 4, 15), duration_days=30)  # Regular weekday
        valid_schedule.add_interval("paper1-pap", date(2025, 5, 15), duration_days=45)  # Regular weekday
        
        result = validate_blackout_constraints(valid_schedule, config_with_blackouts)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
    
    def test_validate_blackout_constraints_violations(self, sample_config) -> None:
        """Test blackout validation with violations."""
        # Create a copy of the config with blackout dates
        config_with_blackouts = sample_config.model_copy(update={
            "blackout_dates": [date(2025, 1, 1), date(2025, 7, 4)]
        })
        
        # Test with invalid schedule (blackout date)
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)  # New Year's Day
        
        result = validate_blackout_constraints(invalid_schedule, config_with_blackouts)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == False
        assert len(result.violations) > 0
    
    def test_validate_blackout_constraints_multiple_violations(self, sample_config) -> None:
        """Test blackout validation with multiple violations."""
        # Create a copy of the config with blackout dates
        config_with_blackouts = sample_config.model_copy(update={
            "blackout_dates": [date(2025, 1, 1), date(2025, 7, 4)]
        })
        
        # Test with schedule that spans multiple blackout dates
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)   # Starts on New Year's
        invalid_schedule.add_interval("paper1-pap", date(2025, 7, 1), duration_days=30)  # Spans July 4th
        
        result = validate_blackout_constraints(invalid_schedule, config_with_blackouts)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == False
        assert len(result.violations) > 0
    
    def test_validate_blackout_constraints_edge_cases(self, sample_config) -> None:
        """Test blackout validation edge cases."""
        # Create a copy of the config with blackout dates
        config_with_blackouts = sample_config.model_copy(update={
            "blackout_dates": [date(2025, 1, 1)]
        })
        
        # Test with schedule that spans a blackout date - use ID that exists in config
        edge_schedule = Schedule()
        edge_schedule.add_interval("mod1-wrk", date(2024, 12, 31), duration_days=2)  # Spans Jan 1
        
        result = validate_blackout_constraints(edge_schedule, config_with_blackouts)
        assert isinstance(result, ValidationResult)
        # This should detect the violation since the submission spans the blackout date
        assert result.is_valid == False
