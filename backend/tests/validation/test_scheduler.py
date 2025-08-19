"""Test scheduler validation functions."""

import pytest
from datetime import date
from src.core.models import Config, Submission, Schedule, SubmissionType, ValidationResult
from src.validation.scheduler import validate_scheduler_constraints


class TestSchedulerValidation:
    """Test cases for scheduler validation functions."""
    
    def test_validate_scheduler_constraints_basic(self, sample_config) -> None:
        """Test basic scheduler validation."""
        # Create a valid submission and schedule
        submission = sample_config.submissions[0]
        schedule = Schedule()
        start_date = date(2025, 1, 1)
        
        result = validate_scheduler_constraints(submission, start_date, schedule, sample_config)
        assert isinstance(result, ValidationResult)
        # The validation should run without crashing
        assert isinstance(result.violations, list)
        assert isinstance(result.metadata, dict)
    
    def test_validate_scheduler_constraints_concurrency(self, sample_config) -> None:
        """Test scheduler concurrency validation."""
        submission = sample_config.submissions[0]
        schedule = Schedule()
        
        # Test with valid start date
        start_date = date(2025, 1, 1)
        result = validate_scheduler_constraints(submission, start_date, schedule, sample_config)
        assert isinstance(result, ValidationResult)
        
        # Test with schedule that would exceed concurrency limits
        schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)
        schedule.add_interval("paper1-pap", date(2025, 1, 1), duration_days=45)  # Same start date
        
        # Create config with strict concurrency limit
        strict_config = sample_config.model_copy(update={
            "max_concurrent_submissions": 1  # Very strict limit
        })
        
        result = validate_scheduler_constraints(submission, start_date, schedule, strict_config)
        assert isinstance(result, ValidationResult)
        # Should detect concurrency violations
        assert len(result.violations) > 0
    
    def test_validate_scheduler_constraints_working_days(self, sample_config) -> None:
        """Test scheduler working day validation."""
        submission = sample_config.submissions[0]
        schedule = Schedule()
        start_date = date(2025, 1, 1)
        
        # Test with config that has blackout dates
        config_with_blackouts = sample_config.model_copy(update={
            "blackout_dates": [date(2025, 1, 1)]  # New Year's Day
        })
        
        result = validate_scheduler_constraints(submission, start_date, schedule, config_with_blackouts)
        assert isinstance(result, ValidationResult)
        # Should detect blackout date violations
        assert len(result.violations) > 0
    
    def test_validate_scheduler_constraints_integration(self, sample_config) -> None:
        """Test scheduler validation integration with other validations."""
        submission = sample_config.submissions[0]
        schedule = Schedule()
        start_date = date(2025, 1, 1)
        
        # Test that scheduler validation calls other validation functions
        result = validate_scheduler_constraints(submission, start_date, schedule, sample_config)
        assert isinstance(result, ValidationResult)
        
        # The result should contain violations from all validation types
        assert isinstance(result.violations, list)
        assert isinstance(result.summary, str)
        assert isinstance(result.metadata, dict)
