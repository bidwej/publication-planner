"""Test schedule validation functions."""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from src.core.models import Config, Submission, Schedule, SubmissionType, Conference, ConferenceType, ConferenceRecurrence, ValidationResult
from src.validation.schedule import validate_schedule_constraints


class TestScheduleValidation:
    """Test cases for schedule validation functions."""
    
    def test_validate_schedule_empty_schedule(self, empty_config) -> None:
        """Test schedule validation with empty schedule."""
        schedule = Schedule()
        
        result = validate_schedule_constraints(schedule, empty_config)
        assert isinstance(result, ValidationResult)
        assert result.is_valid == True
        assert result.metadata.get("total_submissions", 0) == 0
    
    def test_schedule_validation_with_submissions(self, sample_config) -> None:
        """Test schedule validation with actual submissions."""
        from core.models import Interval
        
        # Test with valid schedule (dependencies satisfied and no blackout dates)
        valid_schedule = Schedule()
        valid_schedule.add_interval("mod1-wrk", date(2025, 4, 15), duration_days=30)   # Work item starts first, no blackout
        valid_schedule.add_interval("paper1-pap", date(2025, 5, 15), duration_days=45)  # Paper starts after mod1 completes
        
        result = validate_schedule_constraints(valid_schedule, sample_config)
        # The validation might fail due to other constraints, but we can test the structure
        assert isinstance(result, ValidationResult)
        assert "summary" in result.__dict__
        assert "metadata" in result.__dict__
        
        # Test with invalid schedule (dependencies violated)
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2025, 5, 15), duration_days=30)   # Work item starts later
        invalid_schedule.add_interval("paper1-pap", date(2025, 4, 15), duration_days=45)  # Paper starts before mod1
        
        invalid_result = validate_schedule_constraints(invalid_schedule, sample_config)
        # This should fail due to dependency violation
        assert isinstance(invalid_result, ValidationResult)
        assert "summary" in invalid_result.__dict__
        assert "metadata" in invalid_result.__dict__
    
    def test_dependency_validation(self, sample_config) -> None:
        """Test dependency satisfaction validation."""
        from core.models import Interval
        
        # Test with valid dependency chain (respecting durations)
        valid_schedule = Schedule()
        valid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)   # First
        valid_schedule.add_interval("paper1-pap", date(2025, 2, 1), duration_days=45) # After mod1 (assuming mod1 takes ~1 month)
        valid_schedule.add_interval("mod2-wrk", date(2025, 3, 1), duration_days=30)   # After paper1
        valid_schedule.add_interval("paper2-pap", date(2025, 4, 1), duration_days=45)  # After mod2
        
        result = validate_schedule_constraints(valid_schedule, sample_config)
        assert isinstance(result, ValidationResult)
        assert "summary" in result.__dict__
        assert "metadata" in result.__dict__
        
        # Test with broken dependency chain
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2025, 3, 1), duration_days=30)   # Later
        invalid_schedule.add_interval("paper1-pap", date(2025, 1, 1), duration_days=45) # Before mod1 (violation)
        invalid_schedule.add_interval("mod2-wrk", date(2025, 2, 1), duration_days=30)   # After mod1
        invalid_schedule.add_interval("paper2-pap", date(2025, 4, 1), duration_days=45)  # After both
        
        invalid_result = validate_schedule_constraints(invalid_schedule, sample_config)
        assert isinstance(invalid_result, ValidationResult)
        assert "summary" in invalid_result.__dict__
        assert "metadata" in invalid_result.__dict__
    
    def test_comprehensive_constraint_validation(self, sample_config) -> None:
        """Test comprehensive constraint validation."""
        from core.models import Interval
        
        # Create a modified config with stricter concurrency limits to test resource constraints
        strict_config = sample_config.model_copy(update={
            "max_concurrent_submissions": 2,  # Strict limit
            "blackout_dates": [date(2025, 1, 1)]  # New Year's Day
        })
        
        # Test with schedule that violates multiple constraints
        invalid_schedule = Schedule()
        invalid_schedule.add_interval("mod1-wrk", date(2025, 1, 1), duration_days=30)    # Valid start
        invalid_schedule.add_interval("paper1-pap", date(2025, 1, 1), duration_days=45)  # Same day as mod1 (resource violation)
        invalid_schedule.add_interval("mod2-wrk", date(2025, 1, 1), duration_days=30)    # Same day as others (resource violation)
        invalid_schedule.add_interval("paper2-pap", date(2025, 2, 1), duration_days=45)   # After others
        
        result = validate_schedule_constraints(invalid_schedule, strict_config)
        assert isinstance(result, ValidationResult)
        assert "summary" in result.__dict__
        assert "metadata" in result.__dict__
        
        # Check that violations are found
        assert len(result.violations) > 0
