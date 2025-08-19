"""Test deadline validation functions."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from src.core.models import Config, Submission, Schedule, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, ValidationResult
from src.validation.deadline import validate_deadline_constraints


class TestDeadlineValidation:
    """Test cases for deadline validation functions."""
    
    def test_validate_deadline_constraints_empty_schedule(self) -> None:
        """Test deadline validation with empty schedule."""
        # Create empty config with required parameters
        config: Config = Config(
            submissions=[],
            conferences=[],
            min_abstract_lead_time_days=30,
            min_paper_lead_time_days=90,
            max_concurrent_submissions=3
        )
        schedule = Schedule()  # Use proper Schedule object
        
        result = validate_deadline_constraints(schedule, config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.metadata.get("total_submissions", 0) == 0
    
    def test_deadline_validation_with_submissions(self, sample_config) -> None:
        """Test deadline validation with actual submissions."""
        from core.models import Interval
        
        # Use the sample_config fixture which already has submissions and conferences
        config = sample_config
        
        # Test with valid schedule (submissions before deadlines)
        schedule = Schedule()
        schedule.add_interval("mod1-wrk", date(2025, 4, 1), duration_days=30)  # 2 months before ICRA deadline
        schedule.add_interval("paper1-pap", date(2025, 5, 1), duration_days=45) # 1 month before ICRA deadline
        schedule.add_interval("mod2-wrk", date(2025, 2, 1), duration_days=30)  # 1 month before MICCAI deadline
        schedule.add_interval("paper2-pap", date(2025, 3, 1), duration_days=45) # 1 month before MICCAI deadline
        
        result = validate_deadline_constraints(schedule, config)
        assert result.is_valid == True
        assert result.metadata.get("total_submissions", 0) == 4
        assert result.metadata.get("compliant_submissions", 0) == 4
        
        # Test with invalid schedule (submissions after deadlines)
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2026, 3, 1), duration_days=30)  # After ICRA deadline
        invalid_schedule.add_interval("paper1-pap", date(2026, 4, 1), duration_days=45) # After ICRA deadline
        invalid_schedule.add_interval("mod2-wrk", date(2026, 5, 1), duration_days=30)  # After MICCAI deadline
        invalid_schedule.add_interval("paper2-pap", date(2026, 6, 1), duration_days=45) # After MICCAI deadline
        
        invalid_result = validate_deadline_constraints(invalid_schedule, config)
        assert invalid_result.is_valid == False
        assert len(invalid_result.violations) > 0
    
    def test_blackout_date_validation(self, sample_config) -> None:
        """Test blackout date validation."""
        from core.models import Interval
        
        # Create a copy of the config with blackout dates to avoid modifying the shared fixture
        config_with_blackouts = sample_config.model_copy(update={
            "blackout_dates": [date(2025, 1, 1), date(2025, 7, 4)]  # New Year's and July 4th
        })
        
        # Test with valid schedule (no blackout dates)
        valid_schedule = Schedule()
        valid_schedule.add_interval("mod1-wrk", date(2025, 4, 15), duration_days=30)  # Regular weekday
        valid_schedule.add_interval("paper1-pap", date(2025, 5, 15), duration_days=45)  # Regular weekday
        
        result = validate_deadline_constraints(valid_schedule, config_with_blackouts)
        assert result.is_valid == True
        
        # Test with invalid schedule (blackout date)
        # Note: deadline validation doesn't check blackout dates - that's handled by blackout validation
        # So this test just verifies that deadline validation still works with blackout dates configured
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)  # New Year's Day
        invalid_schedule.add_interval("paper1-pap", date(2025, 5, 15), duration_days=45)  # Regular weekday
        
        invalid_result = validate_deadline_constraints(invalid_schedule, config_with_blackouts)
        # Deadline validation should still pass - blackout validation is separate
        assert invalid_result.is_valid == True
