"""Test resource validation functions."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from core.models import Config, Submission, Schedule, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, ValidationResult
from validation.resources import validate_resources_constraints


class TestResourcesValidation:
    """Test cases for resources validation functions."""
    
    def test_validate_resources_constraints_empty_schedule(self, empty_config, empty_schedule) -> None:
        """Test resources validation with empty schedule."""
        result: ValidationResult = validate_resources_constraints(empty_schedule, empty_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.metadata.get("max_observed", 0) == 0
    
    def test_calculate_daily_load_empty_schedule(self, empty_config, empty_schedule) -> None:
        """Test daily load calculation with empty schedule."""
        # This test is testing an internal function that's not directly accessible
        # Instead, test the public function that uses it
        result: ValidationResult = validate_resources_constraints(empty_schedule, empty_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.metadata.get("max_observed", 0) == 0
    
    def test_resources_validation_with_submissions(self, sample_config, sample_schedule) -> None:
        """Test resources validation with actual submissions."""
        # Use the sample_config and sample_schedule fixtures which already have data
        
        result: ValidationResult = validate_resources_constraints(sample_schedule, sample_config)
        assert result.is_valid == True
        assert result.metadata.get("max_observed", 0) <= sample_config.max_concurrent_submissions
        
        # Test that the result has the expected structure
        assert isinstance(result, ValidationResult)
        assert hasattr(result, 'metadata')
        assert 'max_observed' in result.metadata
    
    def test_concurrency_limit_validation(self, sample_config) -> None:
        """Test concurrency limit validation."""
        # Create a modified config with stricter concurrency limits to test resource constraints
        # Use model_copy to avoid modifying the shared fixture
        strict_config = sample_config.model_copy(update={"max_concurrent_submissions": 2})
        
        # Create a schedule that exceeds the concurrency limit
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)
        invalid_schedule.add_interval("paper1-pap", date(2025, 1, 1), duration_days=30)
        invalid_schedule.add_interval("mod2-wrk", date(2025, 1, 1), duration_days=30)
        
        result: ValidationResult = validate_resources_constraints(invalid_schedule, strict_config)
        assert result.is_valid == False
        assert result.metadata.get("max_observed", 0) > strict_config.max_concurrent_submissions
        assert len(result.violations) > 0
        
        # Test with valid schedule (respects concurrency limit)
        valid_schedule = Schedule()
        valid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)
        valid_schedule.add_interval("paper1-pap", date(2025, 2, 1), duration_days=30)
        valid_schedule.add_interval("mod2-wrk", date(2025, 3, 1), duration_days=30)
        
        valid_result: ValidationResult = validate_resources_constraints(valid_schedule, strict_config)
        assert valid_result.is_valid == True
        assert valid_result.metadata.get("max_observed", 0) <= strict_config.max_concurrent_submissions
